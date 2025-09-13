"""
handle_events module.
"""

from typing import Any

from domain_event_pattern.models import DomainEvent, DomainEventHandler
from domain_event_pattern.models.domain_event_handler_registry import EventHandlerRegistry


def handle_events(*event_types: type[DomainEvent]) -> Any:
    """
    Decorator to automatically register domain event subscribers.

    Args:
        *event_types (type[DomainEvent]): The event types this subscriber should handle.

    Returns:
        Any: The decorated class with automatic registration.

    Example:
    ```python
    from domain_event_pattern import DomainEvent, DomainEventHandler, handle_events


    class UserCreatedEvent(DomainEvent):
        _event_name = 'user.created'
        user_identifier: str
        email: str

        def __init__(
            self,
            user_identifier: str,
            email: str,
            identifier: str | None = None,
            occurred_datetime: str | None = None,
        ) -> None:
            super().__init__(identifier=identifier, occurred_datetime=occurred_datetime)
            self.user_identifier = user_identifier
            self.email = email


    class OrderPlacedEvent(DomainEvent):
        _event_name = 'order.placed'
        order_identifier: str
        user_identifier: str
        amount: float

        def __init__(
            self,
            order_identifier: str,
            user_identifier: str,
            amount: float,
            identifier: str | None = None,
            occurred_datetime: str | None = None,
        ) -> None:
            super().__init__(identifier=identifier, occurred_datetime=occurred_datetime)
            self.order_identifier = order_identifier
            self.user_identifier = user_identifier
            self.amount = amount


    @handle_events(UserCreatedEvent, OrderPlacedEvent)
    class EmailNotificationHandler(DomainEventHandler[UserCreatedEvent | OrderPlacedEvent]):
        async def on(self, *, event: UserCreatedEvent | OrderPlacedEvent) -> None:
            if isinstance(event, UserCreatedEvent):
                print(f'Sending welcome email to {event.email}')
                return

            print(f'Sending order confirmation for order {event.order_identifier}')
    ```
    """

    def decorator(cls: type[DomainEventHandler[Any]]) -> type[DomainEventHandler[Any]]:
        """
        Internal decorator function that handles the actual registration.

        Args:
            cls (type[DomainEventSubscriber[Any]]): The subscriber class to register.

        Returns:
            type[DomainEventSubscriber[Any]]: The decorated class.

        Example:
        ```python
        from domain_event_pattern import DomainEvent, DomainEventHandler, handle_events


        class UserCreatedEvent(DomainEvent):
            _event_name = 'user.created'
            user_identifier: str
            email: str

            def __init__(
                self,
                user_identifier: str,
                email: str,
                identifier: str | None = None,
                occurred_datetime: str | None = None,
            ) -> None:
                super().__init__(identifier=identifier, occurred_datetime=occurred_datetime)
                self.user_identifier = user_identifier
                self.email = email


        class OrderPlacedEvent(DomainEvent):
            _event_name = 'order.placed'
            order_identifier: str
            user_identifier: str
            amount: float

            def __init__(
                self,
                order_identifier: str,
                user_identifier: str,
                amount: float,
                identifier: str | None = None,
                occurred_datetime: str | None = None,
            ) -> None:
                super().__init__(identifier=identifier, occurred_datetime=occurred_datetime)
                self.order_identifier = order_identifier
                self.user_identifier = user_identifier
                self.amount = amount


        @handle_events(UserCreatedEvent, OrderPlacedEvent)
        class EmailNotificationHandler(DomainEventHandler[UserCreatedEvent | OrderPlacedEvent]):
            async def on(self, *, event: UserCreatedEvent | OrderPlacedEvent) -> None:
                if isinstance(event, UserCreatedEvent):
                    print(f'Sending welcome email to {event.email}')
                    return

                print(f'Sending order confirmation for order {event.order_identifier}')
        ```
        """
        cls._registered_event_types = event_types  # type: ignore[attr-defined]

        instance = cls()
        EventHandlerRegistry.register(subscriber=instance, event_types=event_types)

        return cls

    return decorator
