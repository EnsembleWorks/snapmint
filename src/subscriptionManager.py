import asyncio
from firebase_admin import firestore_async as firestore


# Define the transaction function outside the class
@firestore.async_transactional
async def process_job(transaction, job_ref, onFrameRequest):
    try:
        snapshot = await job_ref.get(transaction=transaction)
        if snapshot.exists and snapshot.get("mediaTimestamp") is None:
            targetTimestamp = snapshot.get("dateCreated")
            media_timestamp = await onFrameRequest(targetTimestamp)
            transaction.update(
                job_ref,
                {"mediaTimestamp": media_timestamp},
            )
    except Exception as e:
        print(f"Failed to process job {job_ref.id}: {e}")


class SubscriptionManager:
    def __init__(self, onFrameRequest, batchFrequency, shutdownEvent):
        self.onFrameRequest = onFrameRequest
        self.batchFrequency = batchFrequency
        self.shutdownEvent = shutdownEvent
        self.loop = asyncio.get_event_loop()
        self.db = firestore.client()

    async def fetch_jobs(self):
        print("Looking for recent jobs...")
        jobs_query = (
            self.db.collection("jobs").where("mediaTimestamp", "==", None).limit(250)
        )
        jobs = jobs_query.stream()
        async for job in jobs:
            print("Processing job: ", job.id)
            job_ref = self.db.collection("jobs").document(job.id)
            transaction = self.db.transaction()
            self.loop.create_task(
                process_job(transaction, job_ref, self.onFrameRequest)
            )

    async def start_listening(self):
        print("Starting subscription manager...")
        while not self.shutdownEvent.is_set():
            await self.fetch_jobs()
            await asyncio.sleep(self.batchFrequency)
