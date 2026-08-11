from __future__ import annotations

import asyncio
from typing import Any

from ..data_service_client import DataServiceClient
from ..settings import MEMORY_WORKER_INTERVAL_SECONDS
from .policy import MemoryPolicy
from .provider import MemoryProvider


class MemoryWorker:
    def __init__(self, data_service: DataServiceClient, provider: MemoryProvider) -> None:
        self.data_service = data_service
        self.provider = provider
        self.policy = MemoryPolicy()

    async def run_once(self) -> dict[str, Any]:
        await self.data_service.request("memory-job.recover")
        job = await self.data_service.request("memory-job.claim")
        if not job or not job.get("jobId"):
            return {"status": "idle"}
        messages = job.get("messages") or []
        decision = self.policy.evaluate(messages)
        if not decision.eligible:
            await self.data_service.request("memory-job.ignore", {"jobId": job["jobId"], "reason": decision.reason})
            return {"status": "ignored", "jobId": job["jobId"], "reason": decision.reason}
        try:
            refs = await self.provider.add(
                user_id=job["userId"],
                messages=[{"role": item["role"], "content": item["content"]} for item in messages],
                metadata={"memoryBucket": decision.bucket, "sourceEventId": job["eventId"]},
            )
            completed = await self.data_service.request("memory-job.complete", {"jobId": job["jobId"], "refs": [
                {"memoryId": item["memoryId"], "memoryBucket": (item.get("metadata") or {}).get("memoryBucket", decision.bucket)}
                for item in refs if item.get("memoryId")
            ]})
            return {"status": "completed", "jobId": job["jobId"], "result": completed}
        except Exception as exc:
            try:
                result = await self.data_service.request("memory-job.fail", {"jobId": job["jobId"], "error": str(exc)})
            except Exception:
                result = {"status": "failed", "jobId": job["jobId"]}
            return {"status": "failed", "jobId": job["jobId"], "result": result}

    async def run_forever(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                await self.run_once()
            except Exception:
                # The next interval retries connectivity without taking down the service.
                pass
            try:
                await asyncio.wait_for(stop.wait(), timeout=MEMORY_WORKER_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                continue
