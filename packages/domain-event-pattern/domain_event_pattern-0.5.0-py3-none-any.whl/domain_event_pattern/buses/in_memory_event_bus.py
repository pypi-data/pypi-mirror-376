"""
InMemoryEventBus module.
"""

from sys import version_info

if version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from typing import Awaitable, Callable, Sequence

from domain_event_pattern.errors import HandlerError, PublicationError
from domain_event_pattern.models.domain_event import DomainEvent
from domain_event_pattern.models.domain_event_handler import DomainEventHandler
from domain_event_pattern.models.domain_event_handler_registry import EventHandlerRegistry

from .event_bus import EventBus


class InMemoryEventBus(EventBus):
    """
    In-memory implementation of the EventBus interface.

    This event bus provides a simple, synchronous event publishing mechanism that runs all event handlers in the same
    process. It automatically discovers and handlers to all registered domain event handlers from the
    EventHandlerRegistry.

    The InMemoryEventBus is ideal for:
    - Single-process applications
    - Testing scenarios
    - Development environments
    - Applications that don't require distributed event processing

    Example:
    ```python
    # TODO:
    ```
    """

    _handlers: dict[str, list[Callable[[DomainEvent], Awaitable[None]]]]

    def __init__(self) -> None:
        """
        Initialize the event bus with registered handlers.

        Example:
        ```python
        # TODO:
        ```
        """
        self._handlers = {}

        for handler, event_types in EventHandlerRegistry.subscribers.items():
            for event_type in event_types:
                self._subscribe_handler(event_name=event_type.event_name, handler=handler)

    @override
    async def publish(self, *, events: Sequence[DomainEvent]) -> None:
        """
        Publish a sequence of domain events to all registered handlers.

        Args:
            events (Sequence[DomainEvent]): The events to publish.

        Raises:
            PublicationError: If there is an error during publication.

        Example:
        ```python
        # TODO:
        ```
        """
        errors: list[HandlerError] = []

        for event in events:
            handlers = self._handlers.get(event.event_name, [])
            for handler in handlers:
                try:
                    await handler(event)

                except Exception as exception:
                    errors.append(HandlerError(event=event, handler=handler, error=exception))

        if errors:
            raise PublicationError(errors=errors)

    def _subscribe(self, *, event_name: str, handler: DomainEventHandler[DomainEvent]) -> None:
        """
        Subscribe a domain event handler to a specific event.

        Args:
            event_name (str): The name of the event to subscribe to.
            handler (DomainEventHandler[DomainEvent]): The handler to register.
        """

        async def subscription_wrapper(event: DomainEvent) -> None:
            await handler.on(event=event)

        if event_name in self._handlers:
            self._handlers[event_name].append(subscription_wrapper)
            return

        self._handlers[event_name] = [subscription_wrapper]

    def _subscribe_handler(self, *, event_name: str, handler: object) -> None:
        """
        Subscribe an event handler to a specific event.

        Args:
            event_name (str): The name of the event to subscribe to.
            handler (object): The handler that implements the on() method.
        """

        async def subscription_wrapper(event: DomainEvent) -> None:
            await handler.on(event=event)  # type: ignore[attr-defined]

        if event_name in self._handlers:
            self._handlers[event_name].append(subscription_wrapper)
            return

        self._handlers[event_name] = [subscription_wrapper]
