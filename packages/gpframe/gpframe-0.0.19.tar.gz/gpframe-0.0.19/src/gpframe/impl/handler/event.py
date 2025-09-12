import asyncio
import inspect
import threading
from typing import TYPE_CHECKING, Any, Awaitable, Callable, TypeVar, Union

from ..context.event import ROContext

from .errors import FrameHandlerError

R = TypeVar("R")

EventHandler = Union[Callable[[ROContext[R]], Any], Callable[[ROContext[R]], Awaitable[Any]]]

class EventHandlerWrapper:
    __slots__ = ('_lock', '_event_name', '_caller',)
    def __init__(self, event_name: str):
        self._event_name = event_name
        self._caller = None
    
    async def __call__(self, ctx: ROContext):
        if self._caller is not None:
            try:
                return await self._caller(ctx)
            except Exception as e:
                raise FrameHandlerError(self._event_name, e)
                
        
    def set_handler(self, handler: EventHandler):
        if inspect.iscoroutinefunction(handler):
            self._caller = handler
        else:
            async def sync_caller(message: ROContext):
                return await asyncio.to_thread(handler, message)
            self._caller = sync_caller


