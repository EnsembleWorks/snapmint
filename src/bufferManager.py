import asyncio
from collections import OrderedDict
from colors import Colors


class BufferManager:
    def __init__(self, maxsize):
        self.frames = OrderedDict()
        self.maxsize = maxsize
        self.lock = asyncio.Lock()

    async def add(self, timestamp, frame):
        async with self.lock:
            if len(self.frames) >= self.maxsize:
                self.frames.popitem(last=False)
            self.frames[timestamp] = frame
            print(
                f"{Colors.BLUE}First frame timestamp:\t{next(iter(self.frames))}\tLast frame timestamp:\t{next(reversed(self.frames))}{Colors.END}"
            )

    async def get_latest(self):
        async with self.lock:
            if self.frames:
                latest_timestamp = next(reversed(self.frames))
                return self.frames[latest_timestamp], latest_timestamp
            return None

    async def get_size(self):
        async with self.lock:
            return len(self.frames)

    async def find_closest_by_timestamp(self, target_timestamp):
        async with self.lock:
            closest_timestamp = min(
                self.frames, key=lambda k: abs(k - target_timestamp)
            )
            return self.frames[closest_timestamp], closest_timestamp

    def __del__(self):
        self.frames.clear()
