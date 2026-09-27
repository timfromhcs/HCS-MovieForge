"""Abstract Base Worker implementing the unified worker execution protocol."""

from abc import ABC, abstractmethod
from typing import Any
from packages.contracts.src.worker import (
    ServiceState,
    WorkerCapabilities,
    WorkerRequest,
    WorkerResponse,
    WorkerTelemetry,
)


class BaseWorker(ABC):
    def __init__(self, worker_id: str, backend_name: str, backend_version: str = "1.0.0"):
        self.worker_id = worker_id
        self.backend_name = backend_name
        self.backend_version = backend_version
        self.state = ServiceState.READY
        self.current_job_id: str | None = None

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """Returns health status of the worker backend."""
        pass

    @abstractmethod
    def capabilities(self) -> WorkerCapabilities:
        """Returns capabilities, supported tasks, and compute device requirements."""
        pass

    @abstractmethod
    def estimate(self, request: WorkerRequest) -> dict[str, Any]:
        """Provides runtime and memory estimates for a request."""
        pass

    @abstractmethod
    def prepare(self, request: WorkerRequest) -> None:
        """Prepares models, buffers, or temporary files prior to execution."""
        pass

    @abstractmethod
    def run(self, request: WorkerRequest) -> WorkerResponse:
        """Executes the task and returns a structured response with artifact references."""
        pass

    @abstractmethod
    def cancel(self, job_id: str) -> bool:
        """Safely stops execution for the given job_id."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Releases temporary files, staging buffers, or idle model memory."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Terminates any background processes and releases all resources."""
        pass
