import time
import asyncio
import cv2
import numpy as np
from datetime import datetime


class CaptureManager:
    def __init__(
        self,
        buffer,
        sessionTitle,
        captureFrequency,
        cameraIndex,
        captureWidth,
        captureHeight,
        captureFPS,
        shutdownEvent,
    ):
        # Open the webcam
        cap = cv2.VideoCapture(cameraIndex)

        # Check if the camera opened successfully
        if not cap.isOpened():
            print("Error: Could not open video device")
            return

        # Set the resolution and frame rate
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, captureWidth)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, captureHeight)
        cap.set(cv2.CAP_PROP_FPS, captureFPS)

        # Verify the resolution and frame rate
        actualFps = cap.get(cv2.CAP_PROP_FPS)
        actualWidth = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actualHeight = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(
            f"Requested resolution: {captureWidth}x{captureHeight} at {captureFPS} FPS"
        )
        print(f"Actual resolution: {actualWidth}x{actualHeight} at {actualFps} FPS")

        self.buffer = buffer
        self.cap = cap
        self.sessionTitle = sessionTitle
        self.captureFrequency = captureFrequency
        self.shutdownEvent = shutdownEvent

    def cleanup_capture(self):
        # Release the webcam
        self.cap.release()
        return

    def get_current_unix_time(self):
        return int(time.time())


    def mock_read(self):
        # Create a blank black image
        height, width = 2160, 3840  # You can adjust these dimensions to your needs
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Set font scale and thickness
        font_scale = 8
        thickness = 4

        # Calculate the text size to center the timestamp
        text_size = cv2.getTextSize(
            timestamp, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )[0]
        text_x = (width - text_size[0]) // 2
        text_y = (height + text_size[1]) // 2

        # Put timestamp on the frame
        cv2.putText(
            frame,
            timestamp,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            thickness,
        )

        # Mock the success flag as True
        return True, frame

    def perform_capture(self):
        # ret, frame = self.cap.read()
        ret, frame = self.mock_read()
        
        # print(".", end="", flush=True)
        captureTime = self.get_current_unix_time()
        if ret:
            return frame, captureTime
        else:
            raise ValueError("Failed to capture frame")

    async def capture_video_frames(self):
        while not self.shutdownEvent.is_set():
            frame, captureTime = self.perform_capture()
            await self.buffer.add(captureTime, frame)
            await asyncio.sleep(self.captureFrequency)
        self.cleanup_capture()
