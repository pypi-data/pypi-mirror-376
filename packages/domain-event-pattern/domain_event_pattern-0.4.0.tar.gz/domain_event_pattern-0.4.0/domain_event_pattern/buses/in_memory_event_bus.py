"""
InMemoryEventBus module.
"""

from sys import version_info

if version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from typing import Awaitable, Callable, Sequence

from domain_event_pattern.models.domain_event import DomainEvent
from domain_event_pattern.models.domain_event_handler import DomainEventHandler
from domain_event_pattern.models.domain_event_handler_registry import EventHandlerRegistry

from .event_bus import EventBus


class InMemoryEventBus(EventBus):
    """
    In-memory implementation of the EventBus interface.

    This event bus provides a simple, synchronous event publishing mechanism that runs all event handlers in the same
    process. It automatically discovers and subscribes to all registered domain event subscribers from the
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

    _subscriptions: dict[str, list[Callable[[DomainEvent], Awaitable[None]]]]

    def __init__(self) -> None:
        """
        Initialize the event bus with registered subscribers.

        Example:
        ```python
        # TODO:
        ```
        """
        self._subscriptions = {}

        for subscriber, event_types in EventHandlerRegistry.subscribers.items():
            for event_type in event_types:
                self._subscribe_handler(event_name=event_type.event_name, handler=subscriber)

    @override
    async def publish(self, *, events: Sequence[DomainEvent]) -> None:
        """
        Publish a sequence of domain events to all registered subscribers.

        Args:
            events (Sequence[DomainEvent]): The events to publish.

        Example:
        ```python
        # TODO:
        ```
        """
        for event in events:
            subscribers = self._subscriptions.get(event.event_name, [])
            for subscriber in subscribers:
                try:
                    await subscriber(event)

                except Exception as exception:
                    print(exception)

    def _subscribe(self, *, event_name: str, subscriber: DomainEventHandler[DomainEvent]) -> None:
        """
        Subscribe a domain event subscriber to a specific event.

        Args:
            event_name (str): The name of the event to subscribe to.
            subscriber (DomainEventSubscriber[DomainEvent]): The subscriber to register.
        """

        async def subscription_wrapper(event: DomainEvent) -> None:
            await subscriber.on(event=event)

        if event_name in self._subscriptions:
            self._subscriptions[event_name].append(subscription_wrapper)
            return

        self._subscriptions[event_name] = [subscription_wrapper]

    def _subscribe_handler(self, *, event_name: str, handler: object) -> None:
        """
        Subscribe an event handler to a specific event.

        Args:
            event_name (str): The name of the event to subscribe to.
            handler (object): The handler that implements the on() method.
        """

        async def subscription_wrapper(event: DomainEvent) -> None:
            await handler.on(event=event)  # type: ignore[attr-defined]

        if event_name in self._subscriptions:
            self._subscriptions[event_name].append(subscription_wrapper)
            return

        self._subscriptions[event_name] = [subscription_wrapper]
