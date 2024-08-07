import os
import aiofiles
import asyncio
import cv2
from colors import Colors
from firebase_admin import storage
from concurrent.futures import ThreadPoolExecutor


class OutputManager:
    def __init__(self, buffer, sessionTitle, checkpointFrequency, shutdownEvent):
        self.buffer = buffer
        self.sessionTitle = sessionTitle
        self.checkpointFrequency = checkpointFrequency
        self.shutdownEvent = shutdownEvent
        self.executor = ThreadPoolExecutor()
        self.bucket = storage.bucket()

    async def write_frame_to_disk(self, frame, captureTime):
        filename = os.path.join(self.sessionTitle, f"{captureTime}.jpg")
        success = False
        try:
            async with aiofiles.open(filename, "wb") as file:
                encoded_image = cv2.imencode(".jpg", frame)[1]
                await file.write(encoded_image.tobytes())
                success = True
        except Exception as e:
            print(e)

        if success:
            print(f"{Colors.GREEN}Frame saved to disk:\t{captureTime}{Colors.END}")
        else:
            print(f"{Colors.RED}FAILED TO WRITE TO DISK:\t{filename}{Colors.END}")
        return

    async def upload_frame_to_storage(self, frame, captureTime):
        encoded_image = cv2.imencode(".jpg", frame)[1]
        filename = os.path.join("frames", self.sessionTitle, f"{captureTime}.jpg")
        blob = self.bucket.blob(filename)
        try:
            await asyncio.get_running_loop().run_in_executor(
                self.executor,
                blob.upload_from_string,
                encoded_image.tobytes(),
                "image/jpeg",
            )
            print(
                f"{Colors.GREEN}Frame uploaded\t{captureTime}{Colors.END}"
            )
        except Exception as e:
            print(
                f"{Colors.RED}FAILED TO UPLOAD TO CLOUD STORAGE:\t{filename}{Colors.END}"
            )
            print(e)

    async def save_checkpoints(self):
        while not self.shutdownEvent.is_set():
            frame, captureTime = await self.buffer.get_latest()
            if frame is not None:
                await self.write_frame_to_disk(frame, captureTime)
            await asyncio.sleep(self.checkpointFrequency)

    async def save_frame_at_timestamp(self, targetTimestamp):
        frame, captureTime = await self.buffer.find_closest_by_timestamp(
            targetTimestamp
        )
        latency = abs(targetTimestamp - captureTime)
        latencyColor = Colors.RED if latency > 0 else Colors.YELLOW
        print(
            f"{Colors.YELLOW}Searching for frame:\t{targetTimestamp}\tFound frame: {captureTime}\tLatency: {latencyColor}{latency}{Colors.END}"
        )
        if frame is not None:
            await self.write_frame_to_disk(frame, captureTime)
            await self.upload_frame_to_storage(frame, captureTime)
            return captureTime
        return None
