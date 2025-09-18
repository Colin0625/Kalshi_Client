import websockets
import asyncio
import time
import typing
import threading

class Manager():
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