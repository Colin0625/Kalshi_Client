import websockets
import asyncio
import time
import typing
import threading

class TaskManager():
    def __init__(self):
        self._tasks = {}
        self._labels = {}
        self._next_id = 1
        self._lock = asyncio.Lock()
    
    async def add(self, coro, label):
        async with self._lock:
            tid = self._next_id
            self._next_id += 1

            task = asyncio.create_task(self._wrap(coro, tid))
            self._tasks[tid] = task
            self._labels[tid] = label or f"task-{tid}"
            return tid
        
    async def _wrap(self, coro, tid):
        label = self._labels.get(tid, f"task-{tid}")
        try:
            return await coro
        finally:
            # auto-clean when done
            async with self._lock:
                self._tasks.pop(tid, None)
                self._labels.pop(tid, None)
    
    async def cancel(self, tid: int) -> bool:
        async with self._lock:
            t = self._tasks.get(tid)
            if not t:
                return False
            t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass
        return True