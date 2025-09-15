import asyncio
import inspect
import logging
import time
from graphlib import TopologicalSorter
from typing import Any, Optional

from .assets import get_asset
from .context import AssetContext
from .result import AssetResult
from .tui import FlowTUIRenderer, show_flow_tree


class Flow:
    """A class representing a workflow of assets."""

    def __init__(self, asset_names: list[str]):
        self.asset_names = asset_names
        self.asset_outputs: dict[str, Any] = {}

        self.graph = self._get_graph()

        ts = self._get_ts()
        self.static_order = list(ts.static_order())

    def _get_graph(self) -> dict[str, set[str]]:
        """Sets up the graph based on asset dependencies."""
        graph: dict[str, set[str]] = {}

        queue = list(self.asset_names)
        visited = set()

        while queue:
            asset_name = queue.pop(0)
            if asset_name in visited:
                continue
            visited.add(asset_name)

            asset = get_asset(asset_name)
            deps = set(asset["deps"])
            graph[asset_name] = deps

            for dep in deps:
                queue.append(dep)

        return graph

    def _get_ts(self) -> TopologicalSorter:
        """Sets up the topological sorter based on asset dependencies."""

        return TopologicalSorter(self.graph)

    async def _execute_asset(
        self, asset_name: str, logger: logging.Logger
    ) -> AssetResult:
        """Executes an asset and returns a result object."""
        start_time = time.monotonic()
        output = None
        exception = None
        success = False
        try:
            logger.info(f"Executing asset: {asset_name}")
            asset = get_asset(asset_name)

            asset_func = asset["func"]
            deps = asset["deps"]

            # Only pass outputs that are actual parameters of the asset function
            sig = inspect.signature(asset_func)
            params = sig.parameters
            input_kwargs = {
                dep: self.asset_outputs[dep]
                for dep in deps
                if dep in self.asset_outputs and dep in params
            }

            if "context" in params:
                context = AssetContext(logger=logger, asset_name=asset_name)
                input_kwargs["context"] = context

            if asyncio.iscoroutinefunction(asset_func):
                output = await asset_func(**input_kwargs)
            else:
                # Run sync function in a thread pool executor
                loop = asyncio.get_running_loop()
                import functools

                p = functools.partial(asset_func, **input_kwargs)
                output = await loop.run_in_executor(None, p)
            success = True

        except Exception as e:
            exception = e
            logger.exception(f"Error executing asset {asset_name}: {e}")

        duration = time.monotonic() - start_time
        if success:
            logger.info(f"Finished executing asset: {asset_name} in {duration:.2f}s")

        return AssetResult(
            name=asset_name,
            success=success,
            duration=duration,
            start_time=start_time,
            output=output,
            exception=exception,
        )

    async def run_async(
        self,
        config: Optional[dict[str, Any]] = None,
        max_concurrency: Optional[int] = None,
    ) -> None:
        """Executes the assets in the flow asynchronously with a concurrency limit."""
        if max_concurrency is not None and max_concurrency <= 0:
            raise ValueError("max_concurrency must be a positive integer or None.")

        show_flow_tree(self.graph)
        ts = self._get_ts()
        ts.prepare()

        tui = FlowTUIRenderer(total_assets=len(self.static_order))
        running_tasks_map: dict[asyncio.Task, tuple[str, int]] = {}

        with tui:
            while ts.is_active():
                ready_to_run = list(ts.get_ready())

                limit = max_concurrency if max_concurrency is not None else float("inf")

                # Start new tasks if we have capacity and there are tasks ready to run
                while len(running_tasks_map) < limit and ready_to_run:
                    asset_name = ready_to_run.pop(0)
                    progress_task_id = tui.add_running_task(asset_name)
                    async_task = asyncio.create_task(
                        self._execute_asset(asset_name, tui.logger)
                    )
                    running_tasks_map[async_task] = (asset_name, progress_task_id)

                if not running_tasks_map:
                    break  # Nothing running, nothing new to start

                done, _ = await asyncio.wait(
                    running_tasks_map.keys(), return_when=asyncio.FIRST_COMPLETED
                )

                for task in done:
                    asset_name, progress_task_id = running_tasks_map.pop(task)

                    asset_result: AssetResult = task.result()

                    tui.complete_running_task(progress_task_id, asset_result)

                    if asset_result.success:
                        self.asset_outputs[asset_name] = asset_result.output
                        ts.done(asset_name)
