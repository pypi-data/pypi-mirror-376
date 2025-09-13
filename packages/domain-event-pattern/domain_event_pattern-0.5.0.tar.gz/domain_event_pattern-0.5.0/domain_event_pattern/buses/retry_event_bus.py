"""
RetryEventBus module.
"""

from __future__ import annotations

from sys import version_info

if version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from asyncio import CancelledError, sleep
from dataclasses import dataclass
from random import uniform
from typing import Sequence

from domain_event_pattern.errors import HandlerError, PublicationError
from domain_event_pattern.models.domain_event import DomainEvent

from .event_bus import EventBus


@dataclass(frozen=True)
class RetryPolicy:
    """
    Configuration for retrying failed event handler invocations.
    """

    max_attempts: int = 3  # total attempts including the first
    base_delay: float = 0.2
    backoff_factor: float = 2.0  # exponential multiplier
    max_delay: float = 5.0
    jitter: float = 0.1  # +/- proportion of delay


class RetryEventBus(EventBus):
    """
    Decorator event bus that adds retry logic to an inner event bus.

    Behavior:
    - Calls inner `publish()`.
    - If it raises `PublicationError`, retries ONLY the failed (event, subscriber) pairs
      using exponential backoff.
    - If some still fail after retries, re-raises a new `PublicationError` with the remaining failures.

    Example:
    ```python
    # TODO:
    ```
    """

    def __init__(self, *, bus: EventBus, policy: RetryPolicy | None = None) -> None:
        """
        Initialize the retry event bus with an inner bus and retry policy.

        Args:
            bus (EventBus): The inner event bus to decorate.
            policy (RetryPolicy | None): The retry policy to use. If None, a default policy will be used.

        Example:
        ```python
        # TODO:
        ```
        """
        self._bus = bus
        self._policy = policy or RetryPolicy()

    @override
    async def publish(self, *, events: Sequence[DomainEvent]) -> None:
        """
        Publish a sequence of domain events, retrying failed handlers as per policy.

        Args:
            events (Sequence[DomainEvent]): Sequence of domain events to publish.

        Raises:
            PublicationError: If there is an error during publication.

        Example:
        ```python
        # TODO:
        ```
        """
        try:
            await self._bus.publish(events=events)

        except PublicationError as exception:
            errors = await self._retry_errors(publication_error=exception)
            if errors:
                raise PublicationError(errors=errors) from exception

    async def _retry_errors(self, *, publication_error: PublicationError) -> list[HandlerError]:
        """
        Retry failed (event, handler) pairs as per policy.


        Args:
            publication_error (PublicationError): The publication error containing failed handlers.

        Returns:
            list[HandlerError]: List of handler errors that still failed after retries.
        """
        errors: list[HandlerError] = []

        for error in publication_error.errors:
            attempts = 1  # the original attempt already happened inside the inner bus
            delay = self._policy.base_delay

            while True:
                try:
                    attempts += 1
                    await error.handler(error.event)
                    break

                except CancelledError as exception:
                    raise exception

                except Exception as exception:
                    if attempts > self._policy.max_attempts:
                        # TODO: on give up send a message or whatever
                        errors.append(HandlerError(handler=error.handler, event=error.event, error=exception))
                        break

                        # TODO: on retry send a message or whatever

                    await sleep(
                        delay=self._with_jitter(
                            delay=min(delay, self._policy.max_delay),
                            jitter=self._policy.jitter,
                        )
                    )
                    delay *= self._policy.backoff_factor

        return errors

    def _with_jitter(self, *, delay: float, jitter: float) -> float:
        """
        Apply jitter to a delay value.

        Args:
            delay (float): Base delay value.
            jitter (float): Jitter proportion (0 to 1).

        Returns:
            float: Delay value with jitter applied.
        """
        if jitter <= 0:
            return delay

        delta = jitter * delay
        return delay + uniform(a=-delta, b=+delta)  # noqa: S311
