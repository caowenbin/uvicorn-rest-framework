import enum
import typing

from collections.abc import Mapping
from rest_framework.core.types import Scope, Receive, Send, Message
from rest_framework.utils.escape import json_decode, json_encode
from rest_framework.core.datastructures import URL, Headers, QueryParams


class WebSocketState(enum.Enum):
    CONNECTING = 0
    CONNECTED = 1
    DISCONNECTED = 2


class WebSocketDisconnect(Exception):
    def __init__(self, code: int = 1000) -> None:
        self.code = code


class WebSocket(Mapping):
    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "websocket"
        self._scope = scope
        self._receive = receive
        self._send = send
        self.context = {}
        self.client_state = WebSocketState.CONNECTING
        self.application_state = WebSocketState.CONNECTING

    def __getitem__(self, key: str) -> str:
        return self._scope[key]

    def __iter__(self) -> typing.Iterator:
        return iter(self._scope)

    def __len__(self) -> int:
        return len(self._scope)

    @property
    def method(self) -> bytes:
        return b"GET"

    @property
    def url(self) -> URL:
        if not hasattr(self, "_url"):
            setattr(self, "_url", URL(scope=self._scope))

        return self._url

    @property
    def headers(self) -> Headers:
        if not hasattr(self, "_headers"):
            setattr(self, "_headers", Headers(self._scope["headers"]))

        return self._headers

    @property
    def query_params(self) -> QueryParams:
        if not hasattr(self, "_query_params"):
            query_string = self._scope["query_string"].decode()
            setattr(self, "_query_params", QueryParams(query_string))

        return self._query_params

    async def receive(self) -> Message:
        if self.client_state == WebSocketState.CONNECTING:
            message = await self._receive()
            message_type = message["type"]
            assert message_type == "websocket.connect"
            self.client_state = WebSocketState.CONNECTED
            return message
        elif self.client_state == WebSocketState.CONNECTED:
            message = await self._receive()
            message_type = message["type"]
            assert message_type in {"websocket.receive", "websocket.disconnect"}
            if message_type == "websocket.disconnect":
                self.client_state = WebSocketState.DISCONNECTED
            return message
        else:
            raise RuntimeError(
                'Cannot call "receive" once a disconnect message has been received.'
            )

    async def send(self, message: Message) -> None:
        if self.application_state == WebSocketState.CONNECTING:
            message_type = message["type"]
            assert message_type in {"websocket.accept", "websocket.close"}
            if message_type == "websocket.close":
                self.application_state = WebSocketState.DISCONNECTED
            else:
                self.application_state = WebSocketState.CONNECTED
            await self._send(message)
        elif self.application_state == WebSocketState.CONNECTED:
            message_type = message["type"]
            assert message_type in {"websocket.send", "websocket.close"}
            if message_type == "websocket.close":
                self.application_state = WebSocketState.DISCONNECTED
            await self._send(message)
        else:
            raise RuntimeError('Cannot call "send" once a close message has been sent.')

    async def accept(self, subprotocol: typing.List[str] = None) -> None:
        if self.client_state == WebSocketState.CONNECTING:
            # If we haven't yet seen the 'connect' message, then wait for it first.
            await self.receive()
        await self.send({"type": "websocket.accept", "subprotocol": subprotocol})

    def _raise_on_disconnect(self, message: Message) -> None:
        if message["type"] == "websocket.disconnect":
            raise WebSocketDisconnect(message["code"])

    async def receive_text(self) -> str:
        assert self.application_state == WebSocketState.CONNECTED
        message = await self.receive()
        self._raise_on_disconnect(message)
        return message["text"]

    async def receive_bytes(self) -> bytes:
        assert self.application_state == WebSocketState.CONNECTED
        message = await self.receive()
        self._raise_on_disconnect(message)
        return message["bytes"]

    async def receive_json(self) -> typing.Any:
        assert self.application_state == WebSocketState.CONNECTED
        message = await self.receive()
        self._raise_on_disconnect(message)
        data = message["bytes"]
        return json_decode(data)

    async def send_text(self, data: str) -> None:
        await self.send({"type": "websocket.send", "text": data})

    async def send_bytes(self, data: bytes) -> None:
        await self.send({"type": "websocket.send", "bytes": data})

    async def send_json(self, data: typing.Any) -> None:
        send_data = json_encode(data).encode("utf-8")
        await self.send({"type": "websocket.send", "bytes": send_data})

    async def close(self, code: int = 1000) -> None:
        await self.send({"type": "websocket.close", "code": code})


class WebSocketClose:
    def __init__(self, code: int = 1000) -> None:
        self.code = code

    async def __call__(self, receive: Receive, send: Send) -> None:
        await send({"type": "websocket.close", "code": self.code})
