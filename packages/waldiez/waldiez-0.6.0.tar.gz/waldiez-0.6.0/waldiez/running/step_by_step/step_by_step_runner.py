# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Waldiez and contributors.

# pylint: disable=line-too-long
# pyright: reportUnknownMemberType=false, reportAttributeAccessIssue=false
# pyright: reportUnknownArgumentType=false, reportOptionalMemberAccess=false
# pylint: disable=duplicate-code
# flake8: noqa: E501

"""Step-by-step Waldiez runner with user interaction capabilities."""

import asyncio
import threading
import traceback
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, Union

from pydantic import ValidationError

from waldiez.io.utils import DEBUG_INPUT_PROMPT, gen_id
from waldiez.models.waldiez import Waldiez
from waldiez.running.step_by_step.command_handler import CommandHandler
from waldiez.running.step_by_step.events_processor import EventProcessor

from ..base_runner import WaldiezBaseRunner
from ..exceptions import StopRunningException
from ..run_results import WaldiezRunResults
from .breakpoints_mixin import BreakpointsMixin
from .step_by_step_models import (
    VALID_CONTROL_COMMANDS,
    WaldiezDebugConfig,
    WaldiezDebugError,
    WaldiezDebugEventInfo,
    WaldiezDebugInputRequest,
    WaldiezDebugInputResponse,
    WaldiezDebugMessage,
    WaldiezDebugStats,
    WaldiezDebugStepAction,
)

if TYPE_CHECKING:
    from autogen.events import BaseEvent  # type: ignore
    from autogen.messages import BaseMessage  # type: ignore


MESSAGES = {
    "workflow_starting": "<Waldiez step-by-step> - Starting workflow...",
    "workflow_finished": "<Waldiez step-by-step> - Workflow finished",
    "workflow_stopped": "<Waldiez step-by-step> - Workflow stopped by user",
    "workflow_failed": (
        "<Waldiez step-by-step> - Workflow execution failed: {error}"
    ),
}


# pylint: disable=too-many-instance-attributes
# noinspection DuplicatedCode,StrFormat
class WaldiezStepByStepRunner(WaldiezBaseRunner, BreakpointsMixin):
    """Refactored step-by-step runner with improved architecture."""

    def __init__(
        self,
        waldiez: Waldiez,
        output_path: str | Path | None = None,
        uploads_root: str | Path | None = None,
        structured_io: bool = False,
        dot_env: str | Path | None = None,
        auto_continue: bool = False,
        breakpoints: Iterable[str] | None = None,
        config: WaldiezDebugConfig | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the step-by-step runner."""
        super().__init__(
            waldiez,
            output_path=output_path,
            uploads_root=uploads_root,
            structured_io=structured_io,
            dot_env=dot_env,
            **kwargs,
        )
        BreakpointsMixin.__init__(self)

        # Configuration
        self._config = config or WaldiezDebugConfig()
        self._config.auto_continue = auto_continue

        # Core state
        self._event_count = 0
        self._processed_events = 0
        self._step_mode = self._config.step_mode

        # Use deque for efficient FIFO operations on event history
        self._event_history: deque[dict[str, Any]] = deque(
            maxlen=self._config.max_event_history
        )
        self._current_event: Union["BaseEvent", "BaseMessage", None] = None

        # Participant tracking
        self._known_participants = self.waldiez.info.participants
        self._last_sender: str | None = None
        self._last_recipient: str | None = None

        # Initialize breakpoints
        if breakpoints:
            _, errors = self.import_breakpoints(list(breakpoints))
            if errors:
                for error in errors:
                    self.log.warning("Breakpoint import error: %s", error)

        # Command handling
        self._command_handler = CommandHandler(self)
        self._event_processor = EventProcessor(self)

    @property
    def auto_continue(self) -> bool:
        """Get whether auto-continue is enabled."""
        return self._config.auto_continue

    @auto_continue.setter
    def auto_continue(self, value: bool) -> None:
        """Set whether auto-continue is enabled.

        Parameters
        ----------
        value : bool
            Whether to enable auto-continue.
        """
        self._config.auto_continue = value
        self.log.debug("Auto-continue mode set to: %s", value)

    @property
    def step_mode(self) -> bool:
        """Get the step mode.

        Returns
        -------
        bool
            Whether the step mode is enabled.
        """
        return self._step_mode

    @step_mode.setter
    def step_mode(self, value: bool) -> None:
        """Set the step mode.

        Parameters
        ----------
        value : bool
            Whether to enable step mode.
        """
        self._step_mode = value
        self.log.debug("Step mode set to: %s", value)

    @property
    def last_sender(self) -> str | None:
        """Get the last sender.

        Returns
        -------
        str | None
            The last sender, if available.
        """
        return self._last_sender

    @last_sender.setter
    def last_sender(self, value: str | None) -> None:
        """Set the last sender.

        Parameters
        ----------
        value : str | None
            The last sender to set.
        """
        self._last_sender = value

    @property
    def last_recipient(self) -> str | None:
        """Get the last recipient.

        Returns
        -------
        str | None
            The last recipient, if available.
        """
        return self._last_recipient

    @last_recipient.setter
    def last_recipient(self, value: str | None) -> None:
        """Set the last recipient.

        Parameters
        ----------
        value : str | None
            The last recipient to set.
        """
        self._last_recipient = value

    @property
    def stop_requested(self) -> threading.Event:
        """Get the stop requested event."""
        return self._stop_requested

    @property
    def max_event_history(self) -> int:
        """Get the maximum event history size."""
        return self._config.max_event_history

    @staticmethod
    def print(*args: Any, **kwargs: Any) -> None:
        """Print method.

        Parameters
        ----------
        *args : Any
            Positional arguments to print.
        **kwargs : Any
            Keyword arguments to print.
        """
        WaldiezBaseRunner.print(*args, **kwargs)

    def add_to_history(self, event_info: dict[str, Any]) -> None:
        """Add an event to the history.

        Parameters
        ----------
        event_info : dict[str, Any]
            The event information to add to the history.
        """
        self._event_history.append(event_info)

    def pop_event(self) -> None:
        """Pop event from the history."""
        if self._event_history:
            self._event_history.popleft()

    def emit_event(
        self, event: Union["BaseEvent", "BaseMessage", dict[str, Any]]
    ) -> None:
        """Emit an event.

        Parameters
        ----------
        event : BaseEvent | BaseMessage | dict[str, Any]
            The event to emit.
        """
        if not isinstance(event, dict):
            event_info = event.model_dump(
                mode="json", exclude_none=True, fallback=str
            )
            event_info["count"] = self._event_count
            event_info["sender"] = getattr(event, "sender", self._last_sender)
            event_info["recipient"] = getattr(
                event, "recipient", self._last_recipient
            )
        else:
            event_info = event
        self.emit(WaldiezDebugEventInfo(event=event_info))

    # noinspection PyTypeHints
    def emit(self, message: WaldiezDebugMessage) -> None:
        """Emit a debug message.

        Parameters
        ----------
        message : WaldiezDebugMessage
            The message to emit.
        """
        message_dump = message.model_dump(
            mode="json", exclude_none=True, fallback=str
        )
        self.print(message_dump)

    @property
    def current_event(self) -> Union["BaseEvent", "BaseMessage", None]:
        """Get the current event.

        Returns
        -------
        Union["BaseEvent", "BaseMessage", None]
            The current event, if available.
        """
        return self._current_event

    @current_event.setter
    def current_event(
        self, value: Union["BaseEvent", "BaseMessage", None]
    ) -> None:
        """Set the current event.

        Parameters
        ----------
        value : Union["BaseEvent", "BaseMessage", None]
            The event to set as the current event.
        """
        self._current_event = value

    @property
    def event_count(self) -> int:
        """Get the current event count.

        Returns
        -------
        int
            The current event count.
        """
        return self._event_count

    def event_plus_one(self) -> None:
        """Increment the current event count."""
        self._event_count += 1

    def show_event_info(self) -> None:
        """Show detailed information about the current event."""
        if not self._current_event:
            self.emit(WaldiezDebugError(error="No current event to display"))
            return

        event_info = self._current_event.model_dump(
            mode="json", exclude_none=True, fallback=str
        )
        # Add additional context
        event_info["_meta"] = {
            "event_number": self._event_count,
            "processed_events": self._processed_events,
            "step_mode": self._step_mode,
            "has_breakpoints": len(self._breakpoints) > 0,
        }
        self.emit(WaldiezDebugEventInfo(event=event_info))

    def show_stats(self) -> None:
        """Show comprehensive execution statistics."""
        base_stats: dict[str, Any] = {
            "execution": {
                "events_processed": self._processed_events,
                "total_events": self._event_count,
                "processing_rate": (
                    f"{(self._processed_events / self._event_count * 100):.1f}%"
                    if self._event_count > 0
                    else "0%"
                ),
            },
            "mode": {
                "step_mode": self._step_mode,
                "auto_continue": self._config.auto_continue,
            },
            "history": {
                "event_history_count": len(self._event_history),
                "max_history_size": self._config.max_event_history,
                "memory_usage": f"{len(self._event_history) * 200}B (est.)",
            },
            "participants": {
                "last_sender": self._last_sender,
                "last_recipient": self._last_recipient,
                "known_participants": len(self._known_participants),
            },
        }

        # Merge with breakpoint stats
        breakpoint_stats = self.get_breakpoint_stats()
        stats_dict: dict[str, Any] = {
            **base_stats,
            "breakpoints": breakpoint_stats,
        }

        self.emit(WaldiezDebugStats(stats=stats_dict))

    @property
    def execution_stats(self) -> dict[str, Any]:
        """Get comprehensive execution statistics.

        Returns
        -------
        dict[str, Any]
            A dictionary containing execution statistics.
        """
        base_stats: dict[str, Any] = {
            "total_events": self._event_count,
            "processed_events": self._processed_events,
            "event_processing_rate": (
                self._processed_events / self._event_count
                if self._event_count > 0
                else 0
            ),
            "step_mode": self._step_mode,
            "auto_continue": self._config.auto_continue,
            "event_history_count": len(self._event_history),
            "last_sender": self._last_sender,
            "last_recipient": self._last_recipient,
            "known_participants": [
                p.model_dump() for p in self._known_participants
            ],
            "config": self._config.model_dump(),
        }

        return {**base_stats, "breakpoints": self.get_breakpoint_stats()}

    @property
    def event_history(self) -> list[dict[str, Any]]:
        """Get the history of processed events.

        Returns
        -------
        list[dict[str, Any]]
            A list of dictionaries containing event history.
        """
        return list(self._event_history)

    def reset_session(self) -> None:
        """Reset the debugging session state."""
        self._event_count = 0
        self._processed_events = 0
        self._event_history.clear()
        self._current_event = None
        self._last_sender = None
        self._last_recipient = None
        self.reset_stats()
        self.log.info("Debug session reset")

    def _get_user_response(
        self,
        user_response: str,
        request_id: str,
        skip_id_check: bool = False,
    ) -> tuple[str | None, bool]:
        """Get and validate user response."""
        try:
            response = WaldiezDebugInputResponse.model_validate_json(
                user_response
            )
        except ValidationError as exc:
            # Handle raw CLI input
            got = user_response.strip().lower()
            if got in VALID_CONTROL_COMMANDS:
                return got, True
            self.emit(WaldiezDebugError(error=f"Invalid input: {exc}"))
            return None, False

        if not skip_id_check and response.request_id != request_id:
            self.emit(
                WaldiezDebugError(
                    error=f"Stale input received: {response.request_id} != {request_id}"
                )
            )
            return None, False

        return response.data, True

    def _parse_user_action(
        self, user_response: str, request_id: str
    ) -> WaldiezDebugStepAction:
        """Parse user action using the command handler."""
        self.log.debug("Parsing user action... '%s'", user_response)

        user_input, is_valid = self._get_user_response(
            user_response,
            request_id=request_id,
            skip_id_check=True,
        )
        if not is_valid:
            return WaldiezDebugStepAction.UNKNOWN

        return self._command_handler.handle_command(user_input or "")

    def _get_user_action(self) -> WaldiezDebugStepAction:
        """Get user action with timeout support."""
        if self._config.auto_continue:
            self.step_mode = True
            return WaldiezDebugStepAction.CONTINUE

        while True:
            request_id = gen_id()
            try:
                if not self.structured_io:
                    self.emit(
                        WaldiezDebugInputRequest(
                            prompt=DEBUG_INPUT_PROMPT, request_id=request_id
                        )
                    )
            except Exception as e:  # pylint: disable=broad-exception-caught
                self.log.warning("Failed to emit input request: %s", e)
            try:
                user_input = WaldiezBaseRunner.get_user_input(
                    DEBUG_INPUT_PROMPT
                ).strip()
                return self._parse_user_action(
                    user_input, request_id=request_id
                )

            except (KeyboardInterrupt, EOFError):
                self._stop_requested.set()
                return WaldiezDebugStepAction.QUIT

    async def _a_get_user_action(self) -> WaldiezDebugStepAction:
        """Get user action asynchronously."""
        if self._config.auto_continue:
            self.step_mode = True
            return WaldiezDebugStepAction.CONTINUE

        while True:
            request_id = gen_id()
            # pylint: disable=too-many-try-statements
            try:
                self.emit(
                    WaldiezDebugInputRequest(
                        prompt=DEBUG_INPUT_PROMPT, request_id=request_id
                    )
                )

                user_input = await WaldiezBaseRunner.a_get_user_input(
                    DEBUG_INPUT_PROMPT
                )
                user_input = user_input.strip()
                return self._parse_user_action(
                    user_input, request_id=request_id
                )

            except (KeyboardInterrupt, EOFError):
                return WaldiezDebugStepAction.QUIT

    def _handle_step_interaction(self) -> bool:
        """Handle step-by-step user interaction."""
        while True:
            action = self._get_user_action()
            if action in (
                WaldiezDebugStepAction.CONTINUE,
                WaldiezDebugStepAction.STEP,
            ):
                return True
            if action == WaldiezDebugStepAction.RUN:
                return True
            if action == WaldiezDebugStepAction.QUIT:
                return False
            # For other actions (info, help, etc.), continue the loop

    async def _a_handle_step_interaction(self) -> bool:
        """Handle step-by-step user interaction asynchronously."""
        while True:
            action = await self._a_get_user_action()
            if action in (
                WaldiezDebugStepAction.CONTINUE,
                WaldiezDebugStepAction.STEP,
            ):
                return True
            if action == WaldiezDebugStepAction.RUN:
                return True
            if action == WaldiezDebugStepAction.QUIT:
                return False
            # For other actions (info, help, etc.), continue the loop

    def _run(
        self,
        temp_dir: Path,
        output_file: Path,
        uploads_root: Path | None,
        skip_mmd: bool,
        skip_timeline: bool,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Run the Waldiez workflow with step-by-step debugging."""
        # pylint: disable=import-outside-toplevel
        from autogen.io import IOStream  # type: ignore

        from waldiez.io import StructuredIOStream

        results_container: WaldiezRunResults = {
            "results": [],
            "exception": None,
            "completed": False,
        }
        # pylint: disable=too-many-try-statements,broad-exception-caught
        try:
            loaded_module = self._load_module(output_file, temp_dir)
            if self._stop_requested.is_set():
                self.log.debug(
                    "Step-by-step execution stopped before workflow start"
                )
                return []

            # Setup I/O
            if self.structured_io:
                stream = StructuredIOStream(
                    uploads_root=uploads_root, is_async=False
                )
            else:
                stream = IOStream.get_default()

            WaldiezBaseRunner._print = stream.print
            WaldiezBaseRunner._input = stream.input
            WaldiezBaseRunner._send = stream.send

            self.print(MESSAGES["workflow_starting"])
            self.print(self.waldiez.info.model_dump_json())

            results = loaded_module.main(on_event=self._on_event)
            results_container["results"] = results
            self.print(MESSAGES["workflow_finished"])

        except Exception as e:
            if StopRunningException.reason in str(e):
                raise StopRunningException(StopRunningException.reason) from e
            results_container["exception"] = e
            traceback.print_exc()
            self.print(MESSAGES["workflow_failed"].format(error=str(e)))
        finally:
            results_container["completed"] = True

        return results_container["results"]

    def _on_event(self, event: Union["BaseEvent", "BaseMessage"]) -> bool:
        """Process an event with step-by-step debugging."""
        # pylint: disable=too-many-try-statements,broad-exception-caught
        try:
            # Use the event processor for core logic
            result = self._event_processor.process_event(event)

            if result["action"] == "stop":
                self.log.debug(
                    "Step-by-step execution stopped before event processing"
                )
                return False
            self.emit_event(result["event_info"])
            # Handle breakpoint logic
            if result["should_break"]:
                if not self._handle_step_interaction():
                    self._stop_requested.set()
                    if hasattr(event, "type") and event.type == "input_request":
                        event.content.respond("exit")
                        return True
                    raise StopRunningException(StopRunningException.reason)

            # Process the actual event
            WaldiezBaseRunner.process_event(event, skip_send=True)
            self._processed_events += 1

        except Exception as e:
            if not isinstance(e, StopRunningException):
                raise RuntimeError(
                    f"Error processing event {event}: {e}\n{traceback.format_exc()}"
                ) from e
            raise StopRunningException(StopRunningException.reason) from e

        return not self._stop_requested.is_set()

    # pylint: disable=too-complex
    async def _a_run(
        self,
        temp_dir: Path,
        output_file: Path,
        uploads_root: Path | None,
        skip_mmd: bool = False,
        skip_timeline: bool = False,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Run the Waldiez workflow with step-by-step debugging (async)."""

        async def _execute_workflow() -> list[dict[str, Any]]:
            # pylint: disable=import-outside-toplevel
            from autogen.io import IOStream  # pyright: ignore

            from waldiez.io import StructuredIOStream

            # pylint: disable=too-many-try-statements,broad-exception-caught
            try:
                loaded_module = self._load_module(output_file, temp_dir)
                if self._stop_requested.is_set():
                    self.log.debug(
                        "Step-by-step execution stopped before workflow start"
                    )
                    return []

                if self.structured_io:
                    stream = StructuredIOStream(
                        uploads_root=uploads_root, is_async=True
                    )
                else:
                    stream = IOStream.get_default()

                WaldiezBaseRunner._print = stream.print
                WaldiezBaseRunner._input = stream.input
                WaldiezBaseRunner._send = stream.send

                self.print(MESSAGES["workflow_starting"])
                self.print(self.waldiez.info.model_dump_json())

                results = await loaded_module.main(on_event=self._a_on_event)
                self.print(MESSAGES["workflow_finished"])
                return results

            except Exception as e:
                if StopRunningException.reason in str(e):
                    raise StopRunningException(
                        StopRunningException.reason
                    ) from e
                self.print(MESSAGES["workflow_failed"].format(error=str(e)))
                traceback.print_exc()
                return []

        # Create and monitor cancellable task
        task = asyncio.create_task(_execute_workflow())
        # pylint: disable=too-many-try-statements,broad-exception-caught
        try:
            while not task.done():
                if self._stop_requested.is_set():
                    task.cancel()
                    self.log.debug("Step-by-step execution stopped by user")
                    break
                await asyncio.sleep(0.1)
            return await task
        except asyncio.CancelledError:
            self.log.debug("Step-by-step execution cancelled")
            return []

    async def _a_on_event(
        self, event: Union["BaseEvent", "BaseMessage"]
    ) -> bool:
        """Process an event with step-by-step debugging asynchronously."""
        # pylint: disable=too-many-try-statements,broad-exception-caught
        try:
            # Use the event processor for core logic
            result = self._event_processor.process_event(event)

            if result["action"] == "stop":
                self.log.debug(
                    "Async step-by-step execution stopped before event processing"
                )
                return False
            self.emit_event(result["event_info"])
            # Handle breakpoint logic
            if result["should_break"]:
                if not await self._a_handle_step_interaction():
                    self._stop_requested.set()
                    if hasattr(event, "type") and event.type == "input_request":
                        event.content.respond("exit")
                        return True
                    raise StopRunningException(StopRunningException.reason)

            # Process the actual event
            await WaldiezBaseRunner.a_process_event(event, skip_send=True)
            self._processed_events += 1

        except Exception as e:
            if not isinstance(e, StopRunningException):
                raise RuntimeError(
                    f"Error processing event {event}: {e}\n{traceback.format_exc()}"
                ) from e
            raise StopRunningException(StopRunningException.reason) from e

        return not self._stop_requested.is_set()
