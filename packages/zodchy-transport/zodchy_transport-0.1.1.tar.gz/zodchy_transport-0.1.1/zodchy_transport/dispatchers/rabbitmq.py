from faststream.rabbit import RabbitBroker
from zodchy.codex.transport import CommunicationMessage

class RabbitDispatcher:
    def __init__(self, dsn: str, exchange_name: str, persist: bool = False):
        self._broker = RabbitBroker(dsn)
        self._exchange_name = exchange_name
        self._persist = persist
        self._connected = False

    async def dispatch(
        self,
        message: CommunicationMessage,
    ) -> bool:
        try:
            return await self._dispatch_one(message)
        except Exception as e:
            print(f"Failed to send message: {e}")
                
    async def shutdown(self):
        if self._connected:
            await self._broker.stop()
            self._connected = False
                
    async def _ensure_connection(self):
        if not self._connected:
            await self._broker.connect()
            self._connected = True

    async def _dispatch_one(self, message: CommunicationMessage):
        await self._ensure_connection()
        if message.exchange:
            if not message.routing_key:
                raise ValueError(
                    "Routing key must be provided when exchange is provided"
                )
        try:
            await self._broker.publish(
                    message.body,
                    exchange=self._exchange_name,
                    routing_key=message.routing_key,
                    persist=self._persist,
            )
            print(f"Message sent to {message.queue}: {message}")
            return True
        except Exception as e:
            print(f"Failed to send message: {e}")
            return False
