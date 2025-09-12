import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from asyncio import Future
from typing import Any, Dict

import uvicorn
from aioconsole import aprint
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic_core import to_jsonable_python
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax

from hygroup.agent import FeedbackRequest, PermissionRequest
from hygroup.utils import arun


class RequestHandler(ABC):
    @abstractmethod
    async def handle_permission_request(
        self,
        request: PermissionRequest,
        sender: str,
        receiver: str,
        session_id: str,
    ): ...

    @abstractmethod
    async def handle_feedback_request(
        self,
        request: FeedbackRequest,
        sender: str,
        receiver: str,
        session_id: str,
    ): ...


class RichConsoleHandler(RequestHandler):
    def __init__(
        self,
        upper_bound: int = 3,
        default_permission_response: int | None = None,
        default_confirmation_response: bool | None = None,
        permission_color: str = "yellow",
        action_color: str = "yellow",
        feedback_color: str = "blue",
        question_color: str = "white",
        confirmation_color: str = "magenta",
        query_color: str = "white",
        agent_color: str = "green",
        session_color: str = "cyan",
        error_color: str = "red",
        thoughts_color: str = "bright_black",
    ):
        if not 1 <= upper_bound <= 3:
            raise ValueError("upper_bound must be in [1, 3]")
        self.upper_bound = upper_bound
        self.default_permission_response = default_permission_response
        self.default_confirmation_response = default_confirmation_response

        # Color configuration
        self.permission_color = permission_color
        self.action_color = action_color
        self.feedback_color = feedback_color
        self.question_color = question_color
        self.confirmation_color = confirmation_color
        self.query_color = query_color
        self.agent_color = agent_color
        self.session_color = session_color
        self.error_color = error_color
        self.thoughts_color = thoughts_color

        # Initialize Rich console
        self.console = Console()

    async def handle_permission_request(self, request: PermissionRequest, sender: str, receiver: str, session_id: str):
        await arun(
            self.console.print,
            f"\n🔐 [bold {self.permission_color}]Permission Request[/bold {self.permission_color}]",
        )
        await arun(
            self.console.print,
            f"[{self.session_color}]Session:[/{self.session_color}] {session_id}",
            highlight=False,
        )
        await arun(
            self.console.print,
            f"[{self.agent_color}]Sender:[/{self.agent_color}] {sender}",
            highlight=False,
        )

        # Render action as Python code panel
        syntax = Syntax(request.call, "python", theme="monokai", line_numbers=True)
        panel = Panel.fit(syntax, title="[bold]Action[/bold]", title_align="left", border_style=self.action_color)
        await arun(self.console.print, panel)

        if self.default_permission_response is not None:
            return request.respond(self.default_permission_response)

        while True:
            # Create descriptive prompt showing what each option means
            await arun(self.console.print, "\n[bold]Grant permission for this action?[/bold]")
            await arun(self.console.print, "\\[0] Deny", highlight=False)
            await arun(self.console.print, "\\[1] Allow once [dim](default)[/dim]", highlight=False)
            if self.upper_bound > 1:
                await arun(self.console.print, "\\[2] Allow for session", highlight=False)
            if self.upper_bound > 2:
                await arun(self.console.print, "\\[3] Allow always", highlight=False)

            resp = await arun(Prompt.ask, "Choose option", default="1")

            match resp:
                case "0":
                    request.deny()
                case "1":
                    request.grant_once()
                case "2" if self.upper_bound > 1:
                    request.grant_session()
                case "3" if self.upper_bound > 2:
                    request.grant_always()
                case _:
                    valid_options = list(range(self.upper_bound + 1))
                    await arun(
                        self.console.print,
                        f"[{self.error_color}]Invalid input '{resp}'. Please choose from {valid_options}.[/{self.error_color}]",
                    )
                    continue

            await arun(self.console.print, f"Option {resp} submitted")
            break

    async def handle_feedback_request(self, request: FeedbackRequest, sender: str, receiver: str, session_id: str):
        await arun(
            self.console.print,
            f"\n💬 [bold {self.feedback_color}]Feedback Request[/bold {self.feedback_color}]",
        )
        await arun(
            self.console.print,
            f"[{self.session_color}]Session:[/{self.session_color}] {session_id}",
            highlight=False,
        )
        await arun(
            self.console.print,
            f"[{self.agent_color}]Sender:[/{self.agent_color}] {sender}",
            highlight=False,
        )
        await arun(
            self.console.print,
            f"[{self.question_color}]Question:[/{self.question_color}] {request.question}",
            highlight=False,
        )

        resp = await arun(Prompt.ask, "Answer")
        request.respond(resp)
        await arun(self.console.print, "Answer submitted")


class RequestServer(RequestHandler):
    def __init__(self, host: str = "0.0.0.0", port: int = 8623):
        self.host = host
        self.port = port

        self._connections: Dict[str, WebSocket] = {}
        self._requests: Dict[str, PermissionRequest | FeedbackRequest] = {}

        self._server: uvicorn.Server | None = None
        self._task: asyncio.Task | None = None

        self._app = FastAPI()
        self._app.websocket("/ws/{username}")(self.connect)

    async def start(self, join: bool = True):
        config = uvicorn.Config(self._app, host=self.host, port=self.port)
        self._server = uvicorn.Server(config)
        self._task = asyncio.create_task(self._server.serve())
        if join:
            await self._task

    async def stop(self):
        if self._server:
            self._server.should_exit = True
            self._server = None
        if self._task:
            await self._task
            self._task = None

    async def connect(self, websocket: WebSocket, username: str):
        """Handle a new WebSocket connection."""
        await websocket.accept()

        try:
            # Wait for connect message
            data = await websocket.receive_json()

            if data.get("type") != "connect":
                await websocket.send_json(
                    {"type": "connect_response", "success": False, "message": "First message must be connect"}
                )
                await websocket.close()
                return

            # Check if user already has a connection
            if username in self._connections:
                await websocket.send_json(
                    {"type": "connect_response", "success": False, "message": "User already connected"}
                )
                await websocket.close()
                return

            # Store connection
            self._connections[username] = websocket

            # Send success response
            await websocket.send_json(
                {"type": "connect_response", "success": True, "message": "Connected successfully"}
            )

            # Handle incoming messages
            while True:
                data = await websocket.receive_json()
                await self._handle_response(data, username)

        except WebSocketDisconnect:
            # Clean up on disconnect
            if username in self._connections:
                del self._connections[username]
        except Exception:
            # Clean up on any error
            if username in self._connections:
                del self._connections[username]
            raise

    async def _handle_response(self, data: dict, username: str):
        """Handle response messages from the client."""
        msg_type = data.get("type")
        request_id = data.get("request_id")

        if msg_type == "permission_response" and request_id in self._requests:
            request = self._requests.pop(request_id)
            if isinstance(request, PermissionRequest):
                request.respond(data.get("granted", 0))

        elif msg_type == "feedback_response" and request_id in self._requests:
            request = self._requests.pop(request_id)
            if isinstance(request, FeedbackRequest):
                request.respond(data.get("text", ""))

    async def handle_permission_request(self, request: PermissionRequest, sender: str, receiver: str, session_id: str):
        """Called by backend to request a permission response from the user."""
        if receiver not in self._connections:
            # User not connected, respond with denial
            request.respond(False)
            return

        # Generate request ID
        request_id = str(uuid.uuid4())
        self._requests[request_id] = request

        # Send request to client with separate tool fields
        websocket = self._connections[receiver]

        # Safely serialize tool arguments
        try:
            tool_args = to_jsonable_python(request.tool_args)
        except Exception:
            tool_args = ()

        try:
            tool_kwargs = to_jsonable_python(request.tool_kwargs)
        except Exception:
            tool_kwargs = {}

        await websocket.send_json(
            {
                "type": "permission_request",
                "request_id": request_id,
                "tool_name": request.tool_name,
                "tool_args": tool_args,
                "tool_kwargs": tool_kwargs,
                "sender": sender,
                "session_id": session_id,
            }
        )

    async def handle_feedback_request(self, request: FeedbackRequest, sender: str, receiver: str, session_id: str):
        """Called by backend to request a feedback response from the user."""
        if receiver not in self._connections:
            # User not connected, respond with empty feedback
            request.respond("")
            return

        # Generate request ID
        request_id = str(uuid.uuid4())
        self._requests[request_id] = request

        # Send request to client
        websocket = self._connections[receiver]
        await websocket.send_json(
            {
                "type": "feedback_request",
                "request_id": request_id,
                "question": request.question,
                "sender": sender,
                "session_id": session_id,
            }
        )


class RequestClient:
    def __init__(self, handler: RequestHandler | None = None, host: str = "localhost", port: int = 8623):
        self._handler = handler or RichConsoleHandler(default_confirmation_response=True)
        self._server_url = f"ws://{host}:{port}"
        self._websocket: Any = None
        self._username: str | None = None
        self._request_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._receiver_task: asyncio.Task | None = None

    async def join(self):
        if self._receiver_task is None:
            raise RuntimeError("Not connected")
        await self._receiver_task

    async def connect(self, username: str) -> bool:
        """Establish a websocket connection with the server."""
        try:
            from websockets import connect

            url = f"{self._server_url}/ws/{username}"
            self._websocket = await connect(url)

            # Send connect message
            await self._send_message({"type": "connect", "username": username})

            # Wait for connect response
            response = await self._websocket.recv()
            data = json.loads(response)

            if data.get("success"):
                self._username = username
                print(f"User {username} connected.")
                # Start worker and receiver loops
                self._worker_task = asyncio.create_task(self._worker())
                self._receiver_task = asyncio.create_task(self._receiver())
                return True
            else:
                print(f"Connection failed: {data.get('message', 'Unknown error')}")
                await self._websocket.close()
                self._websocket = None
                return False

        except Exception:
            if self._websocket:
                await self._websocket.close()
                self._websocket = None
            raise

    async def disconnect(self):
        """Close the websocket connection with the server."""
        if self._websocket:
            await self._websocket.close()
            self._websocket = None

        if self._worker_task:
            self._worker_task.cancel()

        if self._receiver_task:
            self._receiver_task.cancel()

        self._username = None

    async def _send_message(self, message: dict):
        """Send a message to the server if connected."""
        if self._websocket:
            await self._websocket.send(json.dumps(message))

    async def _receiver(self):
        """Continuously receive messages from the server."""
        try:
            while self._websocket:
                message = await self._websocket.recv()
                data = json.loads(message)
                await self._request_queue.put(data)
        except Exception:
            # Connection closed or error
            pass

    async def _worker(self):
        """Process queued requests by prompting the user."""
        while True:
            try:
                data = await self._request_queue.get()
                request_id = data.get("request_id")
                sender = data.get("sender")
                session_id = data.get("session_id")
                receiver = self._username or ""  # The client user is the receiver

                if data.get("type") == "permission_request":
                    # Create Future and PermissionRequest
                    future: Future[int] = Future()

                    # Extract tool information
                    tool_name = data.get("tool_name", "")
                    tool_args = tuple(data.get("tool_args", []))
                    tool_kwargs = data.get("tool_kwargs", {})

                    # Create request object
                    request = PermissionRequest(tool_name, tool_args, tool_kwargs, future)

                    # Call handler method
                    await self._handler.handle_permission_request(request, sender, receiver, session_id)

                    # Get response from Future
                    granted = await future

                    # Send response back to server
                    await self._send_message(
                        {"type": "permission_response", "request_id": request_id, "granted": granted}
                    )

                elif data.get("type") == "feedback_request":
                    # Create Future and FeedbackRequest
                    future_text: Future[str] = Future()
                    question = data.get("question", "")

                    # Create request object
                    feedback_request = FeedbackRequest(question, future_text)

                    # Call handler method
                    await self._handler.handle_feedback_request(feedback_request, sender, receiver, session_id)

                    # Get response from Future
                    text = await future_text

                    # Send response back to server
                    await self._send_message({"type": "feedback_response", "request_id": request_id, "text": text})

            except asyncio.CancelledError:
                break
            except Exception as e:
                await aprint(f"Error processing request: {e}")
