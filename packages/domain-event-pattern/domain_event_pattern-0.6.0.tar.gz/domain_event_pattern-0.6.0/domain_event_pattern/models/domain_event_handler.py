"""
DomainEventHandler module.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .domain_event import DomainEvent

T = TypeVar('T', bound=DomainEvent)


class DomainEventHandler(ABC, Generic[T]):  # noqa: UP046
    """
    Interface for domain event handlers.

    ***This class is abstract and should not be instantiated directly***.

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

    @abstractmethod
    async def on(self, *, event: T) -> None:
        """
        Handle a domain event.

        Args:
            event (T): The domain event to handle.

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
