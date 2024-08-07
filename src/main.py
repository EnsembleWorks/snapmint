from bufferManager import BufferManager
from captureManager import CaptureManager
from outputManager import OutputManager
from subscriptionManager import SubscriptionManager
import asyncio
from datetime import datetime
import os
import firebase_admin


CAPTURE_WIDTH = 3840
CAPTURE_HEIGHT = 2160
CAPTURE_FPS = 30
CAMERA_INDEX = 0
CAPTURE_FREQUENCY = 1
CHECKPOINT_FREQUENCY = 100
BATCH_FREQUENCY = 5
BUFFER_SIZE = 150
CONTRACT_ADDRESS = "0x976441ac45ad70a5ff36ddcee7deda34b3475402"

def get_current_iso_time():
    return datetime.now().isoformat()

async def main():
    print(
        f"Starting the program with Configuration: WIDTH={CAPTURE_WIDTH}, HEIGHT={CAPTURE_HEIGHT}, FPS={CAPTURE_FPS}"
    )
    firebase_admin.initialize_app()
    shutdownEvent = asyncio.Event()
    sessionTitle = CONTRACT_ADDRESS
    if not os.path.exists(sessionTitle):
        os.makedirs(sessionTitle)
    
    buffer = BufferManager(maxsize=BUFFER_SIZE)
    capture = CaptureManager(
        buffer,
        sessionTitle,
        CAPTURE_FREQUENCY,
        CAMERA_INDEX,
        CAPTURE_WIDTH,
        CAPTURE_HEIGHT,
        CAPTURE_FPS,
        shutdownEvent,
    )
    output = OutputManager(
        buffer,
        sessionTitle,
        CHECKPOINT_FREQUENCY,
        shutdownEvent,
    )
    subscription = SubscriptionManager(
        output.save_frame_at_timestamp,
        BATCH_FREQUENCY,
        shutdownEvent,
    )

    # Initialize tasks
    capture_task = asyncio.create_task(
        capture.capture_video_frames()
    )
    checkpoint_task = asyncio.create_task(
        output.save_checkpoints()
    )
    subscription_task = asyncio.create_task(
        subscription.start_listening()
    )
    
    # Await tasks potentially forever or until a condition or error
    await asyncio.gather(capture_task, checkpoint_task, subscription_task)
    

    print("Capture session complete.")
    return


if __name__ == "__main__":
    asyncio.run(main())
