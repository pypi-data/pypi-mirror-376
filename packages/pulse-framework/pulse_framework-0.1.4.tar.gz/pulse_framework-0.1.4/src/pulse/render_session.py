from asyncio import iscoroutine
import logging
from typing import Any, Callable, Optional
import uuid
import asyncio
import traceback

from pulse.context import PulseContext
from pulse.messages import (
    RouteInfo,
    ServerInitMessage,
    ServerMessage,
    ServerUpdateMessage,
    ServerErrorMessage,
)
from pulse.reactive import Effect, flush_effects
from pulse.reconciler import RenderRoot
from pulse.routing import Layout, Route, RouteContext, RouteTree
from pulse.state import State


logger = logging.getLogger(__file__)


class RouteMount:
    def __init__(
        self, render: "RenderSession", route: Route | Layout, route_info: RouteInfo
    ) -> None:
        self.render = render
        self.root = RenderRoot(route.render.fn)
        self.route = RouteContext(route_info)
        self.effect: Optional[Effect] = None
        self._pulse_ctx: PulseContext | None = None


class RenderSession:
    def __init__(
        self,
        id: str,
        routes: RouteTree,
        *,
        server_address: Optional[str] = None,
        client_address: Optional[str] = None,
    ) -> None:
        self.id = id
        self.routes = routes
        # Base server address for building absolute API URLs (e.g., http://localhost:8000)
        self._server_address: Optional[str] = server_address
        # Best-effort client address, captured at prerender or socket connect time
        self._client_address: Optional[str] = client_address
        self.route_mounts: dict[str, RouteMount] = {}
        self.message_listeners: set[Callable[[ServerMessage], Any]] = set()
        self._pending_api: dict[str, asyncio.Future] = {}
        # Registry of per-session global singletons (created via ps.global_state without id)
        self._global_states: dict[str, State] = {}

    @property
    def server_address(self) -> str:
        if self._server_address is None:
            raise RuntimeError("Server address not set")
        return self._server_address

    @property
    def client_address(self) -> str:
        if self._client_address is None:
            raise RuntimeError("Client address not set")
        return self._client_address

    # Effect error handler (batch-level) to surface runtime errors
    def _on_effect_error(self, effect, exc: Exception):
        # TODO: wirte into effects created within a Render

        # We don't want to couple effects to routing; broadcast to all active paths
        details = {"effect": getattr(effect, "name", "<unnamed>")}
        for path in list(self.route_mounts.keys()):
            self.report_error(path, "effect", exc, details)

    def connect(
        self,
        message_listener: Callable[[ServerMessage], Any],
    ):
        self.message_listeners.add(message_listener)
        # Return a disconnect function. Use `discard` since there are two ways
        # of disconnecting a message listener
        return lambda: self.message_listeners.discard(message_listener)

    # Use `discard` since there are two ways of disconnecting a message listener
    def disconnect(self, message_listener: Callable[[ServerMessage], Any]):
        self.message_listeners.discard(message_listener)

    def notify(self, message: ServerMessage):
        for listener in self.message_listeners:
            listener(message)

    def report_error(
        self,
        path: str,
        phase: str,
        exc: Exception,
        details: dict[str, Any] | None = None,
    ):
        error_msg: ServerErrorMessage = {
            "type": "server_error",
            "path": path,
            "error": {
                "message": str(exc),
                "stack": traceback.format_exc(),
                "phase": phase,  # type: ignore
                "details": details or {},
            },
        }
        self.notify(error_msg)
        logger.error(
            "Error reported for path %r during %s: %s\n%s",
            path,
            phase,
            exc,
            traceback.format_exc(),
        )

    def close(self):
        # The effect will be garbage collected, and with it the dependencies
        self.message_listeners.clear()
        for path in list(self.route_mounts.keys()):
            self.unmount(path)
        self.route_mounts.clear()
        # Dispose per-session global singletons if they expose dispose()
        for value in list(self._global_states.values()):
            try:
                value.dispose()
            except Exception as e:  # noqa: BLE001
                # Best-effort: report but continue cleanup
                logger.exception("Error disposing session global state: %s", e)
        self._global_states.clear()

    def execute_callback(self, path: str, key: str, args: list | tuple):
        mount = self.route_mounts[path]
        try:
            cb = mount.root.callbacks[key]
            fn, n_params = cb.fn, cb.n_args
            res = fn(*args[:n_params])
            if iscoroutine(res):
                loop = asyncio.get_running_loop()
                task = loop.create_task(res)

                def _on_task_done(t):
                    try:
                        t.result()
                    except Exception as e:  # noqa: BLE001 - forward all
                        self.report_error(
                            path,
                            "callback",
                            e,
                            {"callback": key, "async": True},
                        )

                task.add_done_callback(_on_task_done)
        except Exception as e:  # noqa: BLE001 - forward all
            self.report_error(path, "callback", e, {"callback": key})

    async def call_api(
        self,
        url_or_path: str,
        *,
        method: str = "POST",
        headers: dict[str, str] | None = None,
        body: Any | None = None,
        credentials: str = "include",
    ) -> dict[str, Any]:
        """Request the client to perform a fetch and await the result.

        Accepts either an absolute URL (http/https) or a relative path. When a
        relative path is provided, it is resolved against this session's
        server_address.
        """
        # Resolve to absolute URL if a relative path is passed
        if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
            url = url_or_path
        else:
            base = self.server_address
            if not base:
                raise RuntimeError(
                    "Server address unavailable. Ensure App.run_codegen/asgi_factory set server_address."
                )
            path = url_or_path if url_or_path.startswith("/") else "/" + url_or_path
            url = f"{base}{path}"
        corr_id = uuid.uuid4().hex
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending_api[corr_id] = fut
        headers = headers or {}
        headers["x-pulse-render-id"] = self.id
        self.notify(
            {
                "type": "api_call",
                "id": corr_id,
                "url": url,
                "method": method,
                "headers": headers,
                "body": body,
                "credentials": "include" if credentials == "include" else "omit",
            }
        )
        result = await fut
        return result

    def handle_api_result(self, data: dict[str, Any]):
        id_ = data.get("id")
        if id_ is None:
            return
        id_ = str(id_)
        fut = self._pending_api.pop(id_, None)
        if fut and not fut.done():
            fut.set_result(
                {
                    "ok": data.get("ok", False),
                    "status": data.get("status", 0),
                    "headers": data.get("headers", {}),
                    "body": data.get("body"),
                }
            )

    def create_route_mount(self, path: str, route_info: Optional[RouteInfo] = None):
        route = self.routes.find(path)
        mount = RouteMount(self, route, route_info or route.default_route_info())
        self.route_mounts[path] = mount
        return mount

    def get_route_mount(
        self,
        path: str,
    ):
        mount = self.route_mounts.get(path)
        if not mount:
            raise ValueError(f"No active route for '{path}'")
        return mount

    # ---- Session-local global state registry ----
    def get_global_state(self, key: str, factory: Callable[[], Any]) -> Any:
        """Return a per-session singleton for the provided key."""
        inst = self._global_states.get(key)
        if inst is None:
            inst = factory()
            self._global_states[key] = inst
        return inst

    def render(
        self, path: str, route_info: Optional[RouteInfo] = None, prerendering=False
    ):
        mount = self.create_route_mount(path, route_info)
        with PulseContext.update(route=mount.route):
            return mount.root.render_vdom(prerendering=prerendering)

    def rerender(self, path: str):
        mount = self.get_route_mount(path)
        with PulseContext.update(route=mount.route):
            return mount.root.render_diff()

    def mount(self, path: str, route_info: RouteInfo):
        if path in self.route_mounts:
            # No logging, this is bound to happen with React strict mode
            # logger.error(f"Route already mounted: '{path}'")
            return

        mount = self.create_route_mount(path, route_info)
        # Get current context + add RouteContext. Save it to be able to mount it
        # whenever the render effect reruns.
        ctx = PulseContext.update(route=mount.route)

        def _render_effect():
            with ctx:
                if mount.root.render_count == 0:
                    vdom = mount.root.render_vdom(prerendering=False)
                    self.notify(
                        ServerInitMessage(type="vdom_init", path=path, vdom=vdom)
                    )
                else:
                    result = mount.root.render_diff()
                    if result.ops:
                        self.notify(
                            ServerUpdateMessage(
                                type="vdom_update", path=path, ops=result.ops
                            )
                        )

        # print(f"Mounting '{path}'")
        mount.effect = Effect(
            _render_effect,
            immediate=True,
            name=f"{path}:render",
            on_error=lambda e: self.report_error(path, "render", e),
        )

    def flush(self):
        flush_effects()

    def navigate(self, path: str, route_info: RouteInfo):
        # Route is already mounted, we can just update the routing state
        try:
            mount = self.get_route_mount(path)
            mount.route.update(route_info)
        except Exception as e:  # noqa: BLE001
            self.report_error(path, "navigate", e)

    def unmount(self, path: str):
        if path not in self.route_mounts:
            return
        try:
            mount = self.route_mounts.pop(path)
            mount.root.unmount()
            if mount.effect:
                mount.effect.dispose()
        except Exception as e:  # noqa: BLE001
            self.report_error(path, "unmount", e)
