from typing import Protocol, runtime_checkable
from contextlib import AbstractContextManager
from orcapod.protocols.core_protocols.kernel import Kernel
from orcapod.protocols.core_protocols.pods import Pod
from orcapod.protocols.core_protocols.source import Source
from orcapod.protocols.core_protocols.streams import Stream


@runtime_checkable
class Tracker(Protocol):
    """
    Records kernel invocations and stream creation for computational graph tracking.

    Trackers are responsible for maintaining the computational graph by recording
    relationships between kernels, streams, and invocations. They enable:
    - Lineage tracking and data provenance
    - Caching and memoization strategies
    - Debugging and error analysis
    - Performance monitoring and optimization
    - Reproducibility and auditing

    Multiple trackers can be active simultaneously, each serving different
    purposes (e.g., one for caching, another for debugging, another for
    monitoring). This allows for flexible and composable tracking strategies.

    Trackers can be selectively activated/deactivated to control overhead
    and focus on specific aspects of the computational graph.
    """

    def set_active(self, active: bool = True) -> None:
        """
        Set the active state of the tracker.

        When active, the tracker will record all kernel invocations and
        stream creations. When inactive, no recording occurs, reducing
        overhead for performance-critical sections.

        Args:
            active: True to activate recording, False to deactivate
        """
        ...

    def is_active(self) -> bool:
        """
        Check if the tracker is currently recording invocations.

        Returns:
            bool: True if tracker is active and recording, False otherwise
        """
        ...

    def record_kernel_invocation(
        self, kernel: Kernel, upstreams: tuple[Stream, ...], label: str | None = None
    ) -> None:
        """
        Record a kernel invocation in the computational graph.

        This method is called whenever a kernel is invoked. The tracker
        should record:
        - The kernel and its properties
        - The input streams that were used as input
        - Timing and performance information
        - Any relevant metadata

        Args:
            kernel: The kernel that was invoked
            upstreams: The input streams used for this invocation
        """
        ...

    def record_source_invocation(
        self, source: Source, label: str | None = None
    ) -> None:
        """
        Record a source invocation in the computational graph.

        This method is called whenever a source is invoked. The tracker
        should record:
        - The source and its properties
        - Timing and performance information
        - Any relevant metadata

        Args:
            source: The source that was invoked
        """
        ...

    def record_pod_invocation(
        self, pod: Pod, upstreams: tuple[Stream, ...], label: str | None = None
    ) -> None:
        """
        Record a pod invocation in the computational graph.

        This method is called whenever a pod is invoked. The tracker
        should record:
        - The pod and its properties
        - The upstream streams that were used as input
        - Timing and performance information
        - Any relevant metadata

        Args:
            pod: The pod that was invoked
            upstreams: The input streams used for this invocation
        """
        ...


@runtime_checkable
class TrackerManager(Protocol):
    """
    Manages multiple trackers and coordinates their activity.

    The TrackerManager provides a centralized way to:
    - Register and manage multiple trackers
    - Coordinate recording across all active trackers
    - Provide a single interface for graph recording
    - Enable dynamic tracker registration/deregistration

    This design allows for:
    - Multiple concurrent tracking strategies
    - Pluggable tracking implementations
    - Easy testing and debugging (mock trackers)
    - Performance optimization (selective tracking)
    """

    def get_active_trackers(self) -> list[Tracker]:
        """
        Get all currently active trackers.

        Returns only trackers that are both registered and active,
        providing the list of trackers that will receive recording events.

        Returns:
            list[Tracker]: List of trackers that are currently recording
        """
        ...

    def register_tracker(self, tracker: Tracker) -> None:
        """
        Register a new tracker in the system.

        The tracker will be included in future recording operations
        if it is active. Registration is separate from activation
        to allow for dynamic control of tracking overhead.

        Args:
            tracker: The tracker to register
        """
        ...

    def deregister_tracker(self, tracker: Tracker) -> None:
        """
        Remove a tracker from the system.

        The tracker will no longer receive recording notifications
        even if it is still active. This is useful for:
        - Cleaning up temporary trackers
        - Removing failed or problematic trackers
        - Dynamic tracker management

        Args:
            tracker: The tracker to remove
        """
        ...

    def record_kernel_invocation(
        self, kernel: Kernel, upstreams: tuple[Stream, ...], label: str | None = None
    ) -> None:
        """
        Record a stream in all active trackers.

        This method broadcasts the stream recording to all currently
        active and registered trackers. It provides a single point
        of entry for recording events, simplifying kernel implementations.

        Args:
            stream: The stream to record in all active trackers
        """
        ...

    def record_source_invocation(
        self, source: Source, label: str | None = None
    ) -> None:
        """
        Record a source invocation in the computational graph.

        This method is called whenever a source is invoked. The tracker
        should record:
        - The source and its properties
        - Timing and performance information
        - Any relevant metadata

        Args:
            source: The source that was invoked
        """
        ...

    def record_pod_invocation(
        self, pod: Pod, upstreams: tuple[Stream, ...], label: str | None = None
    ) -> None:
        """
        Record a stream in all active trackers.

        This method broadcasts the stream recording to all currently`
        active and registered trackers. It provides a single point
        of entry for recording events, simplifying kernel implementations.

        Args:
            stream: The stream to record in all active trackers
        """
        ...

    def no_tracking(self) -> AbstractContextManager[None]: ...
