from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Callable

from ..api.frame import Frame
from ..impl.routine.subprocess import SyncRoutineInSubprocess

if TYPE_CHECKING:
    from ..impl import builder
    from .message import MessageUpdater, MessageReader

def create_frame_api(
        base_state: builder._BaseState,
        routine_sync: builder._FrameSynchronization,
        start_fn: Callable[[], asyncio.Task]
    ) -> Frame:
    
    class _Interface(Frame):
        __slots__ = ()
        @property
        def frame_name(self) -> str:
            return base_state.frame_name
        @property
        def logger(self) -> logging.Logger:
            return base_state.logger
        @property
        def routine_in_subprocess(self) -> bool:
            return isinstance(routine_sync.routine_execution, SyncRoutineInSubprocess)
        @property
        def environment(self) -> MessageReader:
            return routine_sync.environment_map.reader
        @property
        def request(self) -> MessageUpdater:
            return routine_sync.request_map.updater
        @property
        def event_message(self) -> MessageReader:
            return routine_sync.event_msg_map.reader
        @property
        def routine_message(self) -> MessageReader:
            return routine_sync.routine_msg_map.reader
        
        def request_stop_routine(self, **kwargs) -> None:
            routine_sync.routine_execution.request_stop_routine(
                base_state.frame_name,
                base_state.logger,
                **kwargs)
        
        def start(self) -> asyncio.Task:
            return start_fn()
        
    return _Interface()


