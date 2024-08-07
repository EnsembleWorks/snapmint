import time
import asyncio
import cv2
import numpy as np
import random
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
            cap = cv2.VideoCapture("./assets/sketch-sample.mp4")

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
        colors = [
            (50, 50, 50),  # Dark grey
            (30, 30, 30),  # Darker grey
            (10, 10, 10),  # Even darker grey
            (100, 0, 0),  # Dark blue
            (70, 0, 0),  # Darker blue
            (40, 0, 0),  # Even darker blue
        ]
        # Create a blank black image
        height, width = 2160, 3840  # You can adjust these dimensions to your needs
        background_color = random.choice(colors)
        frame = np.full((height, width, 3), background_color, dtype=np.uint8)

        # Get current timestamp
        timestamp1 = datetime.now().strftime("%Y-%m-%d")
        timestamp2 = datetime.now().strftime("%H:%M:%S")

        # Set font scale and thickness
        font_scale = 15
        thickness = 12

        # Calculate the text size to center the timestamp
        text_size1 = cv2.getTextSize(
            timestamp1, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )[0]
        text_size2 = cv2.getTextSize(
            timestamp2, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )[0]
        text_x1 = (width - text_size1[0]) // 2
        text_y1 = ((height + text_size1[1]) // 2) - text_size2[1]
        text_x2 = (width - text_size2[0]) // 2
        text_y2 = ((height + text_size1[1]) // 2) + text_size2[1]

        # Put timestamp on the frame
        cv2.putText(
            frame,
            timestamp1,
            (text_x1, text_y1),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            thickness,
        )
        cv2.putText(
            frame,
            timestamp2,
            (text_x2, text_y2),
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
