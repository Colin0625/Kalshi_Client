import asyncio


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
            print("Creating task")
            task = asyncio.create_task(self._wrap(coro, tid))
            self._tasks[tid] = task
            self._labels[tid] = label
            print(task)
            print("Returning")
            return tid, task

    async def _wrap(self, coro, tid):
        print("Starting wrap")
        try:
            print(f"Trying {coro}")
            return await coro
        finally:
            print("Finallying")
            async with self._lock:
                self._tasks.pop(tid, None)
                self._labels.pop(tid, None)





async def funcy(name, time):
    print(f"Hello my name is {name}")
    await asyncio.sleep(time)
    print(f"After {time} seconds, {name} is still my name!")

async def user_input(prompt):
    return await asyncio.to_thread(input, prompt)



async def main():
    manager = Manager()
    tid, task = asyncio.create_task(manager.add(funcy("Colin", 2), "Big Func"))
    tid2, task2 = asyncio.create_task(manager.add(user_input("Wassup? "), "Big Innie"))
    await task
    await task2
    

asyncio.run(main())