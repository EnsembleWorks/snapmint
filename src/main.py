from bufferManager import BufferManager
from captureManager import CaptureManager
from outputManager import OutputManager
from subscriptionManager import SubscriptionManager
from configuration import Configuration
import asyncio
from datetime import datetime
import os
import firebase_admin

def get_current_iso_time():
    return datetime.now().isoformat()

async def main():
    print(
        f"Starting the program with Configuration: WIDTH={Configuration.CAPTURE_WIDTH}, HEIGHT={Configuration.CAPTURE_HEIGHT}, FPS={Configuration.CAPTURE_FPS}"
    )
    firebase_admin.initialize_app()
    shutdownEvent = asyncio.Event()
    sessionTitle = Configuration.CONTRACT_ADDRESS
    if not os.path.exists(sessionTitle):
        os.makedirs(sessionTitle)
    
    buffer = BufferManager(maxsize=Configuration.BUFFER_SIZE)
    capture = CaptureManager(
        buffer,
        sessionTitle,
        Configuration.CAPTURE_FREQUENCY,
        Configuration.CAMERA_INDEX,
        Configuration.CAPTURE_WIDTH,
        Configuration.CAPTURE_HEIGHT,
        Configuration.CAPTURE_FPS,
        shutdownEvent,
    )
    output = OutputManager(
        buffer,
        sessionTitle,
        Configuration.CHECKPOINT_FREQUENCY,
        shutdownEvent,
    )
    subscription = SubscriptionManager(
        output.save_frame_at_timestamp,
        Configuration.BATCH_FREQUENCY,
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
