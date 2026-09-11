import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class AsyncMemoryWriteBuffer:
    def __init__(self, sqlite_store, lancedb_store, batch_size=25, flush_interval_seconds=0.05):
        self.sqlite_store = sqlite_store
        self.lancedb_store = lancedb_store
        self.batch_size = batch_size
        self.flush_interval_seconds = flush_interval_seconds
        self._queue = asyncio.Queue()
        self._worker_task = None
        self._running = False

    def _ensure_started(self):
        if not self._running:
            try:
                loop = asyncio.get_running_loop()
                self._running = True
                self._worker_task = loop.create_task(self._flush_worker())
            except RuntimeError:
                pass

    def start(self):
        self._ensure_started()

    async def enqueue(self, item: Dict[str, Any]) -> asyncio.Future:
        self._ensure_started()
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        await self._queue.put((item, future))
        return future

    async def stop(self):
        if self._running:
            self._running = False
            if self._worker_task:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
            await self.flush_all()

    async def enqueue(self, item: Dict[str, Any]) -> asyncio.Future:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        await self._queue.put((item, future))
        return future

    async def _flush_worker(self):
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval_seconds)
                if not self._queue.empty():
                    await self._process_batch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f'Write buffer worker error: {e}')

    async def _process_batch(self):
        batch = []
        futures = []
        while not self._queue.empty() and len(batch) < self.batch_size:
            item, fut = await self._queue.get()
            batch.append(item)
            futures.append(fut)

        if not batch:
            return

        try:
            await self.sqlite_store.insert_memories_batch(batch)
            lancedb_items = [
                {
                    'id': item['memory_id'],
                    'vector': item['vector'],
                    'source_agent': item.get('source_agent', 'unknown'),
                    'category': item.get('category', 'general'),
                    'created_at_epoch': item.get('created_at_epoch', 0.0)
                }
                for item in batch if 'vector' in item
            ]
            if lancedb_items:
                self.lancedb_store.add_vectors_batch(lancedb_items)

            for fut in futures:
                if not fut.done():
                    fut.set_result(True)
        except Exception as e:
            logger.error(f'Batch flush failed: {e}')
            for fut in futures:
                if not fut.done():
                    fut.set_exception(e)

    async def flush_all(self):
        while not self._queue.empty():
            await self._process_batch()
