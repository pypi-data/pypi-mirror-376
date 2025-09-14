import asyncio
import collections
import itertools
import json
import re
from datetime import datetime
from pathlib import Path
from typing import TypeVar, Literal, Any, Dict

import pydash
try:
    import tzlocal
except ImportError:
    tzlocal = None
from scopinator.util.logging_config import get_logger
logging = get_logger(__name__)
from pydantic import BaseModel

from scopinator.seestar.commands.common import CommandResponse
from scopinator.seestar.commands.parameterized import (
    IscopeStopView,
    IscopeStartView,
    IscopeStartViewParams, ScopeViewMode, ScopeTargetType,
)
from scopinator.seestar.commands.responses import (
    TelescopeMessageParser,
    MessageAnalytics,
)
from scopinator.seestar.commands.settings import SetUserLocation, SetUserLocationParameters, PiSetTime, \
    PiSetTimeParameter, SetSetting, SettingParameters, SetStackSetting, SetStackSettingParameters
from scopinator.seestar.commands.simple import (
    GetTime,
    GetDeviceState,
    GetViewState,
    GetFocuserPosition,
    GetDiskVolume,
    ScopeGetEquCoord,
    ScopeSync, PiIsVerified, BalanceSensorInfo, GetDeviceStateResponse,
)
from scopinator.seestar.connection import SeestarConnection
from scopinator.seestar.events import (
    EventTypes,
    PiStatusEvent,
    AnnotateResult,
    AnnotateEvent,
    InternalEvent,
    BaseEvent,
)
from scopinator.seestar.protocol_handlers import TextProtocol
from scopinator.util.eventbus import EventBus

U = TypeVar("U")


class TelescopeMessage(BaseModel):
    """A message sent or received by the telescope."""

    timestamp: str
    direction: Literal["sent", "received"]
    message: str


class SeestarStatus(BaseModel):
    """Seestar status."""

    temp: float | None = None
    charger_status: Literal["Discharging", "Charging", "Full", "Not charging"] | None = None
    stage: str | None = None
    charge_online: bool | None = None
    battery_capacity: int | None = None
    stacked_frame: int = 0
    dropped_frame: int = 0
    target_name: str = ""
    annotate: AnnotateResult | None = None
    pattern_match_found: bool = False
    pattern_match_file: str | None = None
    pattern_match_last_check: str | None = None
    focus_position: int | None = None
    lp_filter: bool = False
    gain: int | None = None
    freeMB: int | None = None
    totalMB: int | None = None
    ra: float | None = None
    dec: float | None = None
    dist_deg: float | None = None # Distance from the telescope to the target in degrees
    percent: float | None = None
    balance_sensor: BalanceSensorInfo | None = None
    device_state: dict | None = None  # Full device state info including mount, station, etc.
    pi_status: dict | None = None  # Pi status info including battery temp
    last_device_state_update: float | None = None  # Timestamp of last device state update

    def reset(self):
        self.temp = None
        self.charger_status = None
        self.charge_online = None
        self.battery_capacity = None
        self.stacked_frame = 0
        self.dropped_frame = 0
        self.target_name = ""
        self.annotate = None
        self.pattern_match_found = False
        self.pattern_match_file = None
        self.pattern_match_last_check = None
        self.focus_position = None
        self.lp_filter = False
        self.gain = None
        self.freeMB = None
        self.totalMB = None
        self.ra = None
        self.dec = None
        self.stage = None
        self.device_state = None
        self.pi_status = None
        self.last_device_state_update = None


class ParsedEvent(BaseModel):
    """Parsed event."""

    event: EventTypes


class SeestarClient(BaseModel, arbitrary_types_allowed=True):
    """Seestar client."""

    host: str
    port: int
    event_bus: EventBus | None = None
    websocket_manager: Any | None = None  # WebSocketManager - using Any to avoid circular import
    telescope_id: str | None = None
    connection: SeestarConnection | None = None
    # Start counter at 100 to not conflict with some lower, hardcoded IDs
    counter: itertools.count = itertools.count(100)
    is_connected: bool = False
    status: SeestarStatus = SeestarStatus()
    view_refresh_task: asyncio.Task | None = None
    background_task: asyncio.Task | None = None
    reader_task: asyncio.Task | None = None
    pattern_monitor_task: asyncio.Task | None = None
    responses: dict[int, dict] = {}
    recent_events: collections.deque = collections.deque(maxlen=5)
    text_protocol: TextProtocol = TextProtocol()
    client_mode: Literal["Initialise", "ContinuousExposure", "Stack", "Streaming", "AutoGoto", "AutoFocus", "Idle"] | None = "Idle"
    message_history: collections.deque = collections.deque(maxlen=5000)

    # Image enhancement settings
    image_enhancement_settings: Dict[str, Any] = {}

    # Pattern monitoring configuration
    pattern_file_path: str = "/mnt/sfro/roof/building-6/RoofStatusFile.txt"
    pattern_regex: str = r"OPEN"
    pattern_check_interval: float = 5.0

    # Timeout configuration
    connection_timeout: float = 10.0
    read_timeout: float = 30.0
    write_timeout: float = 10.0
    device_state_refresh_interval: float = 30.0  # Refresh device state every 30 seconds
    
    # Connection monitoring
    connection_monitor_task: asyncio.Task | None = None
    _last_successful_read: float = 0.0
    _connection_check_interval: float = 10.0
    _reconnect_in_progress: bool = False

    def __init__(
            self,
            host: str,
            port: int,
            event_bus: EventBus | None = None,
            websocket_manager: Any = None,
            telescope_id: str = None,
            connection_timeout: float = 10.0,
            read_timeout: float = 30.0,
            write_timeout: float = 10.0,
    ):
        # Create an EventBus if none provided
        if event_bus is None:
            from scopinator.util.eventbus import EventBus
            event_bus = EventBus()
            
        super().__init__(
            host=host,
            port=port,
            event_bus=event_bus,
            websocket_manager=websocket_manager,
            telescope_id=telescope_id,
            connection_timeout=connection_timeout,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
        )

        self.connection = SeestarConnection(
            host=host,
            port=port,
            connection_timeout=connection_timeout,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            should_reconnect_callback=self._should_attempt_reconnection,
        )

    async def _reader(self):
        """Background task that continuously reads messages and handles them."""
        logging.info(f"Starting reader task for {self}")
        while self.is_connected:
            try:
                response_str = await self.connection.read()
                if response_str is not None:
                    # Update last successful read timestamp
                    import time
                    self._last_successful_read = time.time()
                    
                    # Log received message
                    self.message_history.append(
                        TelescopeMessage(
                            timestamp=datetime.now().isoformat(),
                            direction="received",
                            message=response_str,
                        )
                    )

                    # Parse and handle the response
                    if "Event" in response_str:
                        # Handle events
                        await self._handle_event(response_str)
                    elif "jsonrpc" in response_str:
                        # Parse as command response and let protocol handler process it
                        try:
                            parsed_response = CommandResponse(
                                **json.loads(response_str)
                            )
                            self.text_protocol.handle_incoming_message(parsed_response)
                        except Exception as parse_error:
                            logging.error(
                                f"Error parsing response from {self}: '{response_str}' {parse_error}"
                            )
                else:
                    # response_str is None - connection layer handles reconnection automatically
                    # Just continue the loop, no need for manual reconnection here
                    await asyncio.sleep(0.1)
                    continue
            except Exception as e:
                logging.error(f"Unexpected error in reader task for {self}: {e}")
                if self.is_connected:
                    await asyncio.sleep(1.0)  # Brief pause before retrying
                    continue
                else:
                    break
        logging.debug(f"Reader task stopped for {self}")

    async def _pattern_monitor(self):
        """Background task that monitors a file for specific patterns."""
        logging.info(
            f"Starting pattern monitor task for {self} - monitoring {self.pattern_file_path}"
        )
        last_modified_time = None
        last_file_size = 0

        while self.is_connected:
            try:
                file_path = Path(self.pattern_file_path)
                current_time = datetime.now().isoformat()

                # Check if file exists
                if not file_path.exists():
                    self.status.pattern_match_last_check = current_time
                    await asyncio.sleep(self.pattern_check_interval)
                    continue

                # Get file stats
                stat = file_path.stat()
                current_modified_time = stat.st_mtime
                current_size = stat.st_size

                # Check if file has been modified or grown
                if (
                        last_modified_time is None
                        or current_modified_time > last_modified_time
                        or current_size > last_file_size
                ):
                    # Read the file content
                    try:
                        with open(
                                file_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = f.read()

                        # Search for pattern
                        pattern_found = bool(
                            re.search(self.pattern_regex, content, re.IGNORECASE)
                        )

                        # Update status
                        self.status.pattern_match_found = pattern_found
                        self.status.pattern_match_file = str(file_path)
                        self.status.pattern_match_last_check = current_time

                        if pattern_found:
                            logging.info(
                                f"Pattern '{self.pattern_regex}' found in {file_path}"
                            )
                        else:
                            logging.trace(
                                f"Pattern '{self.pattern_regex}' not found in {file_path}"
                            )

                        # Update tracking variables
                        last_modified_time = current_modified_time
                        last_file_size = current_size

                    except Exception as e:
                        logging.error(f"Error reading pattern file {file_path}: {e}")
                        self.status.pattern_match_last_check = current_time
                else:
                    # File hasn't changed, just update the check time
                    self.status.pattern_match_last_check = current_time

            except Exception as e:
                logging.error(f"Error in pattern monitor task for {self}: {e}")
                self.status.pattern_match_last_check = datetime.now().isoformat()

            await asyncio.sleep(self.pattern_check_interval)

        logging.debug(f"Pattern monitor task stopped for {self}")

    async def _heartbeat(self):
        """Background task that sends periodic heartbeat messages."""
        await asyncio.sleep(5)
        while self.is_connected:
            try:
                if self.connection.is_connected() and not self._reconnect_in_progress:
                    logging.trace(f"Pinging {self}")
                    _ = await self.send_and_recv(GetTime())
                await asyncio.sleep(5)
            except Exception as e:
                logging.trace(f"Heartbeat failed for {self}: {e}")
                await asyncio.sleep(5)
                continue

    async def refresh_view_state(self):
        """Refresh the view state."""
        logging.trace(f"Refreshing view state for {self}")
        response = await self.send_and_recv(GetViewState())
        self._process_view_state(response)

    async def _view_refresher(self):
        """Background task that refreshes the view state periodically."""
        logging.info(f"Starting view refresher task for {self}")
        last_device_state_update = 0
        while True:
            if self.is_connected:
                await self.refresh_view_state()
                response = await self.send_and_recv(GetDiskVolume())
                self.status.freeMB = response.result.get("freeMB")
                self.status.totalMB = response.result.get("totalMB")
                
                # Refresh device state every 30 seconds
                import time
                current_time = time.time()
                if current_time - last_device_state_update > 30:
                    try:
                        device_response = await self.send_and_recv(GetDeviceState())
                        if device_response and device_response.result:
                            # Store the full device state
                            self.status.device_state = device_response.result
                            self.status.last_device_state_update = current_time
                            last_device_state_update = current_time
                            logging.trace(f"Device state updated for {self}")
                    except Exception as e:
                        logging.error(f"Failed to refresh device state: {e}")
            await asyncio.sleep(15)

    def _update_client_mode(self, stage: str, state: str = "unknown", mode: str | None = None):
        """Update client mode."""
        if state != "cancel":
            if stage == "ContinuousExposure":
                new_client_mode = "ContinuousExposure"
            elif stage == "RTSP":
                new_client_mode = "Streaming"
            elif stage == "Stack":
                new_client_mode = "Stacking"
            elif stage == "AutoGoto" or stage == "ScopeGoto":
                new_client_mode = "AutoGoto"
            elif stage == "AutoFocus":
                new_client_mode = "AutoFocus"
            elif stage == "Initialise":
                new_client_mode = "Initialise"
            else:
                # Stage isn't a known active stage, default to Idle for safety
                # This prevents the frontend from trying to load streams when the telescope state is unknown
                logging.warning(f"Unknown stage: {stage=} {mode=} {state=} - defaulting to Idle")
                new_client_mode = "ContinuousExposure"
        else:
            new_client_mode = "Idle"

        if self.client_mode != new_client_mode:
            # client mode is changing, so let's make appropriate changes
            old_client_mode = self.client_mode
            logging.warning(
                f"Client mode changing from {old_client_mode} to {new_client_mode}"
            )

            # Emit to event bus for imaging client and other local listeners
            if self.event_bus:
                self.event_bus.emit(
                    "ClientModeChanged",
                    InternalEvent(
                        Timestamp=datetime.now().isoformat(),
                        params={"existing": old_client_mode, "new_mode": new_client_mode},
                    ),
                )

            # Update client mode
            self.client_mode = new_client_mode

            # Broadcast to websocket for frontend clients
            if self.websocket_manager and self.telescope_id:
                try:
                    # Create a task to handle the async websocket broadcast
                    asyncio.create_task(self._broadcast_client_mode_change(old_client_mode, new_client_mode))
                except Exception as e:
                    logging.error(f"Error broadcasting client mode change to websocket: {e}")
        else:
            self.client_mode = new_client_mode

        # Set status.stage to match the client mode for frontend consistency
        # Frontend expects status.stage to indicate the current telescope state
        if new_client_mode == "Idle":
            self.status.stage = "Idle"
        elif new_client_mode == "ContinuousExposure":
            self.status.stage = "ContinuousExposure"
        elif new_client_mode == "Stacking":
            self.status.stage = "Stack"
        elif new_client_mode == "Streaming":
            self.status.stage = "RTSP"
        elif new_client_mode == "AutoGoto":
            self.status.stage = "AutoGoto"
        elif new_client_mode == "AutoFocus":
            self.status.stage = "AutoFocus"
        elif new_client_mode == "Initialise":
            self.status.stage = "Initialise"
        else:
            # Fallback to original stage if unknown mode
            self.status.stage = stage

    def _process_view(self, data: dict[str, Any] | None):
        if not data:
            return

        # print("View", data)
        self.status.target_name = pydash.get(data, "target_name", "unknown")
        self.status.gain = pydash.get(data, "gain", 0)

        stage = pydash.get(data, "stage", "unknown")
        mode = pydash.get(data, "mode", "unknown")
        state = pydash.get(data, "state", "unknown")

        logging.debug(f"Process view: {stage=} {mode=} {state=}")

        annotate_result = pydash.get(data, "Stack.Annotate.result", None)

        if annotate_result is not None:
            # Ensure annotate_result is an AnnotateResult instance
            if not isinstance(annotate_result, AnnotateResult):
                annotate_result = AnnotateResult(**annotate_result) if isinstance(annotate_result, dict) else None
            
            if annotate_result:
                annotation = AnnotateEvent(
                    Timestamp=datetime.now().isoformat(),
                    result=annotate_result,
                )
                self.status.annotate = annotate_result
                self.event_bus.emit("Annotate", annotation)

        # Update client mode
        self._update_client_mode(stage, state, mode)

    async def _broadcast_client_mode_change(self, old_mode: str | None, new_mode: str | None):
        """Broadcast client mode change to websocket clients."""
        try:
            # Use dedicated client mode change broadcast
            await self.websocket_manager.broadcast_client_mode_changed(
                telescope_id=self.telescope_id,
                old_mode=old_mode,
                new_mode=new_mode
            )
            logging.info(f"Broadcasted client mode change from {old_mode} to {new_mode} via websocket")
        except Exception as e:
            logging.error(f"Failed to broadcast client mode change via websocket: {e}")

    def _process_view_state(self, response: CommandResponse):
        """Process view state."""
        logging.trace(f"Processing view state from {self}: {response}")
        if response.result is not None:
            # print(f"view state: {response.result}")
            if "View" in response.result:
                view = response.result["View"]
                self._process_view(view)
            else:
                logging.warning(f"No 'View' field in view state response from {self}: {response.result}")
        else:
            logging.error(f"Error while processing view state from {self}: {response}")

    def _process_device_state(self, response: CommandResponse):
        """Process device state."""
        logging.trace(f"Processing device state from {self}: {response}")
        if response.result is not None:
            pi_status = PiStatusEvent(
                **response.result["pi_status"], Timestamp=response.Timestamp
            )
            self.status.temp = pi_status.temp
            self.status.charger_status = pi_status.charger_status
            self.status.charge_online = pi_status.charge_online
            self.status.battery_capacity = pi_status.battery_capacity
        else:
            logging.error(
                f"Error while processing device state from {self}: {response}"
            )

    def _process_focuser_position(self, response: CommandResponse):
        """Process focuser position."""
        logging.trace(f"Processing focuser position from {self}: {response}")
        if response.result is not None:
            self.status.focus_position = response.result
        else:
            logging.error(
                f"Error while processing focuser position from {self}: {response}"
            )

    def _process_current_coords(self, response: CommandResponse):
        """Process current coordinates."""
        logging.trace(f"Processing current coordinates from {self}: {response}")
        if response.result is not None:
            equ_coord = response.result
            self.status.ra = 15.0 * float(equ_coord.get("ra"))
            self.status.dec = float(equ_coord.get("dec"))

    async def connect(self):
        await self.connection.open()
        
        # Cancel any existing reader task before starting a new one
        # This prevents duplicate readers after reconnection
        if self.reader_task:
            logging.debug(f"Canceling existing reader task before reconnect for {self}")
            self.reader_task.cancel()
            try:
                await self.reader_task
            except asyncio.CancelledError:
                pass
            self.reader_task = None
        
        self.is_connected = True
        self.status.reset()

        # Start background tasks
        import time
        self._last_successful_read = time.time()
        self.background_task = asyncio.create_task(self._heartbeat())
        self.reader_task = asyncio.create_task(self._reader())
        self.pattern_monitor_task = asyncio.create_task(self._pattern_monitor())
        self.view_refresh_task = asyncio.create_task(self._view_refresher())
        self.connection_monitor_task = asyncio.create_task(self._connection_monitor())

        # Upon connect, grab current status

        response: CommandResponse = await self.send_and_recv(GetDeviceState())

        self._process_device_state(response)

        await self.refresh_view_state()

        # Get initial focus position
        response = await self.send_and_recv(GetFocuserPosition())
        logging.trace(f"Received GetFocuserPosition: {response}")

        self._process_focuser_position(response)

        # Get initial coordinates
        response = await self.send_and_recv(ScopeGetEquCoord())
        logging.trace(f"Received ScopeGetEquCoord: {response}")
        self._process_current_coords(response)

        logging.info(f"Connected to {self}")

    async def disconnect(self):
        """Disconnect from Seestar."""
        self.is_connected = False

        # Cancel background tasks
        if self.background_task:
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass
            self.background_task = None

        if self.reader_task:
            self.reader_task.cancel()
            try:
                await self.reader_task
            except asyncio.CancelledError:
                pass
            self.reader_task = None

        if self.pattern_monitor_task:
            self.pattern_monitor_task.cancel()
            try:
                await self.pattern_monitor_task
            except asyncio.CancelledError:
                pass
            self.pattern_monitor_task = None

        if self.view_refresh_task:
            self.view_refresh_task.cancel()
            try:
                await self.view_refresh_task
            except asyncio.CancelledError:
                pass
            self.view_refresh_task = None

        if self.connection_monitor_task:
            self.connection_monitor_task.cancel()
            try:
                await self.connection_monitor_task
            except asyncio.CancelledError:
                pass
            self.connection_monitor_task = None

        await self.connection.close()
        logging.info(f"Disconnected from {self}")

    async def send(self, data: str | BaseModel):
        # todo : do connected check...
        # todo : set "next heartbeat" time, and then in the heartbeat task, check the value
        if isinstance(data, BaseModel):
            if data.id is None:
                data.id = next(self.counter)
            data = data.model_dump_json(exclude_none=True)  # Not sure if this is safe...

        # Log sent message
        self.message_history.append(
            TelescopeMessage(
                timestamp=datetime.now().isoformat(), direction="sent", message=data
            )
        )

        await self.connection.write(data)

    async def _handle_event(self, event_str: str):
        """Parse an event."""
        logging.trace(f"Handling event from {self}: {event_str}")
        try:
            parsed = json.loads(event_str)
            parser: ParsedEvent = ParsedEvent(event=parsed)
            # print(f"Received event from {self}: {type(parser.event)} {parser}")
            logging.trace(
                f"Received event from {self}: {parser.event.Event} {type(parser.event)}"
            )
            self.recent_events.append(parser.event)
            match parser.event.Event:
                case "PiStatus":
                    pi_status = parser.event
                    if pi_status.temp is not None:
                        self.status.temp = pi_status.temp
                    if pi_status.charger_status is not None:
                        self.status.charger_status = pi_status.charger_status
                    if pi_status.charge_online is not None:
                        self.status.charge_online = pi_status.charge_online
                    if pi_status.battery_capacity is not None:
                        self.status.battery_capacity = pi_status.battery_capacity
                    
                    # Store pi_status for battery temperature and other fields
                    self.status.pi_status = {
                        'battery_temp': getattr(pi_status, 'battery_temp', None),
                        'battery_temp_type': getattr(pi_status, 'battery_temp_type', None),
                        'temp': pi_status.temp,
                        'charger_status': pi_status.charger_status,
                        'charge_online': pi_status.charge_online,
                        'battery_capacity': pi_status.battery_capacity
                    }
                case "Stack":
                    logging.trace(f"Updating stacked frame and dropped frame: {parsed}")
                    if self.status.stacked_frame is not None:
                        self.status.stacked_frame = parser.event.stacked_frame
                    if self.status.dropped_frame is not None:
                        self.status.dropped_frame = parser.event.dropped_frame
                    self.event_bus.emit("Stack", parser.event)
                case "Annotate":
                    annotate_event = AnnotateEvent(**parser.event)
                    # Ensure result is an AnnotateResult instance if it exists
                    if annotate_event.result and not isinstance(annotate_event.result, AnnotateResult):
                        annotate_event.result = AnnotateResult(**annotate_event.result) if isinstance(annotate_event.result, dict) else None
                    self.status.annotate = annotate_event.result
                    self.event_bus.emit("Annotate", annotate_event)
                case "FocuserMove":
                    focuser_event = parser.event
                    if focuser_event.position is not None:
                        self.status.focus_position = focuser_event.position
                    logging.trace(f"Focuser event: {focuser_event}")
                case "WheelMove":
                    wheel_event = parser.event
                    if wheel_event.state == "complete":
                        self.status.lp_filter = wheel_event.position == 2
                case "View":
                    self._process_view(parser.event.dict())
                case "ScopeGoto":
                    if parser.event.cur_ra_dec is not None:
                        self.status.ra = parser.event.cur_ra_dec.ra
                        self.status.dec = parser.event.cur_ra_dec.dec
                        self.status.dist_deg = parser.event.dist_deg
                        self._update_client_mode("ScopeGoto")
                case "Initialise":
                    self._update_client_mode("Initialise")
                    if parser.event.state == "working":
                        self.status.percent = 0
                case "DarkLibrary":
                    self.status.percent = parser.event.percent
                case "AutoFocus":
                    self._update_client_mode("AutoFocus")
                case _:
                    self.event_bus.emit(parser.event.Event, parser.event)

            # Todo: include Exposure, Stacked
            # case _:
            #    logging.debug(f"Unhandled event: {parser}")
        except Exception as e:
            logging.error(
                f"Error while parsing event from {self}: {event_str} {type(e)} {e}"
            )

    async def send_and_recv(self, data: str | BaseModel) -> CommandResponse | None:
        # Get or assign message ID
        if isinstance(data, BaseModel):
            if data.id is None:
                data.id = next(self.counter)
            message_id = data.id
        else:
            # For string data, we can't easily assign an ID, so fall back to simple send
            await self.send(data)
            return None

        await self.send(data)

        # The reader task handles all incoming messages and resolves futures
        # We just need to wait for our specific message ID
        return await self.text_protocol.recv_message(self, message_id)

    async def send_and_validate(self, data: str | BaseModel) -> CommandResponse | None:
        """Send a command and validate the response."""
        response = await self.send_and_recv(data)
        # perhaps throw a special kind of error?  also prints the response...
        if response is not None:
            if response.result is not None:
                if response.result.get("success") is True:
                    return response
                else:
                    logging.error(f"Error while processing {data} from {self}: {response}")
                    return None

    async def update_current_coords(self) -> bool:
        """Update telescope position and balance sensor.

        Returns True if the position changed, False otherwise."""
        response: CommandResponse = await self.send_and_recv(GetDeviceState(params={
            "keys": ["balance_sensor"]
        }))
        if response is not None:
            dev_balance_sensor = GetDeviceStateResponse(**response.result)
            self.status.balance_sensor = dev_balance_sensor.balance_sensor

        response = await self.send_and_recv(ScopeGetEquCoord())
        logging.trace(f"Received ScopeGetEquCoord: {response}")
        if response is not None:
            # Normalize to degrees...
            new_ra = response.result.get("ra") * 15.0
            new_dec = response.result.get("dec")

            if new_ra != self.status.ra or new_dec != self.status.dec:
                self.status.ra = new_ra
                self.status.dec = new_dec
                return True
        return False

    def get_message_history(self) -> list[Dict[str, Any]]:
        """Get message history as a list of dictionaries."""
        return [msg.model_dump() for msg in self.message_history]

    def get_parsed_message_history(self) -> list[Dict[str, Any]]:
        """Get message history with parsed message analysis."""
        parsed_messages = []
        for msg in self.message_history:
            msg_dict = msg.model_dump()
            # Add parsed analysis
            parsed = TelescopeMessageParser.parse_message(msg.message, msg.timestamp)
            msg_dict["parsed"] = parsed.model_dump()
            parsed_messages.append(msg_dict)
        return parsed_messages

    def get_message_analytics(self) -> Dict[str, Any]:
        """Get analytics for the message history."""
        messages = self.get_message_history()
        return MessageAnalytics.analyze_message_history(messages)

    def get_recent_commands(self, limit: int = 10) -> list[Dict[str, Any]]:
        """Get recent command messages with parsing."""
        commands = []
        for msg in reversed(self.message_history):
            if msg.direction == "sent":
                parsed = TelescopeMessageParser.parse_message(
                    msg.message, msg.timestamp
                )
                if hasattr(parsed, "method"):
                    cmd_dict = msg.model_dump()
                    cmd_dict["parsed"] = parsed.model_dump()
                    commands.append(cmd_dict)
                    if len(commands) >= limit:
                        break
        return list(reversed(commands))

    def get_recent_events(self, limit: int = 10) -> list[Dict[str, Any]]:
        """Get recent event messages with parsing."""
        events = []
        for msg in reversed(self.message_history):
            if msg.direction == "received":
                parsed = TelescopeMessageParser.parse_message(
                    msg.message, msg.timestamp
                )
                if hasattr(parsed, "event_type"):
                    event_dict = msg.model_dump()
                    event_dict["parsed"] = parsed.model_dump()
                    events.append(event_dict)
                    if len(events) >= limit:
                        break
        return list(reversed(events))

    # Helper methods
    async def goto(
            self,
            target_name: str,
            in_ra: float,
            in_dec: float,
            *,
            mode: ScopeViewMode = "star",
            target_type: ScopeTargetType | None = None,
            lp_filter: bool = False,
    ):
        """Generalized goto."""
        return await self.send_and_recv(
            IscopeStartView(
                params=IscopeStartViewParams(
                    mode=mode,
                    target_ra_dec=(in_ra, in_dec),
                    target_name=target_name,
                    target_type=target_type,
                    lp_filter=lp_filter,
                )
            )
        )

    async def stop_goto(self):
        """Stop goto."""
        return await self.send_and_recv(IscopeStopView(params={"stage": "AutoGoto"}))

    async def stop_stack(self):
        """Stop stack."""
        return await self.send_and_recv(IscopeStopView(params={"stage": "Stack"}))

    async def scope_sync(self, in_ra: float, in_dec: float):
        """Scope sync."""
        return await self.send_and_recv(ScopeSync(params=(in_ra, in_dec)))

    async def scope_view(self, mode: ScopeViewMode = 'star'):
        """Set scope view mode."""
        return await self.send_and_recv(IscopeStartView(params=(IscopeStartViewParams(mode=mode))))

    async def wait_for_event_completion(
            self, event_type: str, timeout: float = 60.0
    ) -> tuple[bool, str | None]:
        """
        Wait for an event of the specified type to complete.

        Listens for events of the given type and waits until the state field
        reaches a terminal state: "complete" (success), "cancel" or "fail" (failure).

        Args:
            event_type: The type of event to listen for (e.g., "AutoGoto", "FocuserMove")
            timeout: Maximum time to wait in seconds (default: 60)

        Returns:
            tuple[bool, str | None]: (success, error_message)
                - success: True if state is "complete", False if state is "cancel" or "fail"
                - error_message: Error message if available when state is "cancel" or "fail", None otherwise

        Raises:
            asyncio.TimeoutError: If timeout is reached without completion
            ValueError: If no event bus is available
        """
        if not self.event_bus:
            raise ValueError("No event bus available")

        # Create an asyncio Event to signal completion
        completion_event = asyncio.Event()
        result = {"success": False, "error": None}

        async def event_handler(event: BaseEvent):
            """Handle incoming events and check for completion."""
            logging.debug(f"wait_for_event_completion Received {event_type} event: {event}")

            # Check if event has a state field
            if hasattr(event, "state") and event.state is not None:
                state = (
                    event.state.lower() if isinstance(event.state, str) else event.state
                )

                if state == "complete":
                    logging.info(f"{event_type} completed successfully")
                    result["success"] = True
                    result["error"] = None
                    completion_event.set()
                elif state in ["cancel", "fail"]:
                    # Try to extract error information
                    error_msg = None
                    if hasattr(event, "error") and event.error is not None:
                        error_msg = str(event.error)
                    elif hasattr(event, "message") and event.message is not None:
                        error_msg = str(event.message)
                    elif hasattr(event, "reason") and event.reason is not None:
                        error_msg = str(event.reason)

                    # Check if event is a dict-like object with error field
                    try:
                        if hasattr(event, "__dict__") and "error" in event.__dict__:
                            error_msg = str(event.__dict__["error"])
                        elif hasattr(event, "dict") and callable(event.dict):
                            event_dict = event.dict()
                            if "error" in event_dict and event_dict["error"]:
                                error_msg = str(event_dict["error"])
                    except Exception:
                        pass

                    logging.info(f"{event_type} failed with state: {state}, error: {error_msg}")
                    result["success"] = False
                    result["error"] = error_msg
                    completion_event.set()
                else:
                    logging.trace(f"{event_type} in progress with state: {state}")

        # Subscribe to the event
        self.event_bus.subscribe(event_type, event_handler)

        try:
            # Wait for completion or timeout
            await asyncio.wait_for(completion_event.wait(), timeout=timeout)
            return result["success"], result["error"]
        except asyncio.TimeoutError:
            logging.error(
                f"Timeout waiting for {event_type} completion after {timeout}s"
            )
            raise
        finally:
            # Clean up the event listener
            self.event_bus.remove_listener(event_type, event_handler)

    async def initialize_telescope(self, lat: float | None = None, lon: float | None = None):
        """Initialize telescope.

        Sends a series of commands to initialize the telescope."""

        # get device state.  if device.is_verified == False, initialize
        if tzlocal:
            tz_name = tzlocal.get_localzone_name()
            tz = tzlocal.get_localzone()
        else:
            # Fallback if tzlocal is not available
            import time
            tz_name = time.tzname[0]
            tz = None
        now = datetime.now(tz)

        await self.send_and_recv(PiIsVerified())
        await self.send_and_recv(PiSetTime(params=[PiSetTimeParameter(
            year=now.year,
            mon=now.month,
            day=now.day,
            hour=now.hour,
            min=now.minute,
            sec=now.second,
            time_zone=tz_name
        )]))

        if lat is not None and lon is not None:
            await self.send_and_recv(SetUserLocation(params=SetUserLocationParameters(
                lat=lat, lon=lon)))

        settings = [
            SettingParameters(lang="en"),
            SettingParameters(auto_af=True), # ??
            SettingParameters(stack_after_goto=False), #  New in firmware 2.1
            SettingParameters(exp_ms={"stack_l": 1, "continuous": 1}),
            SettingParameters(stack_dither={
                "enable": True,
                "pix": 1,
                "interval": 1,
            }),
            SettingParameters(stack={"dbe": False}), # ???
            SettingParameters(frame_calib=False),
        ]
        for setting in settings:
            await self.send_and_recv(SetSetting(params=setting))

        # delay....
        await asyncio.sleep(3)

        # await self.send_and_recv(PiOutputSet2(params={
        #     "heater": {
        #         "state": False,
        #         "value": 0, # Power
        #     }
        # }))

        await self.send_and_recv(SetStackSetting(params=SetStackSettingParameters(
            save_discrete_ok_frame=True,
            save_discrete_frame=True,
        )))

        # await self.send_and_recv(ScopePark(params={"equ_mode": self.is_EQ_mode}))

    async def _connection_monitor(self):
        """Background task that monitors connection health and manages reconnection."""
        logging.info(f"Starting connection monitor task for {self}")
        
        while self.is_connected:
            try:
                await asyncio.sleep(self._connection_check_interval)
                
                if not self.is_connected:
                    break
                    
                # Check if we should attempt reconnection
                if not self.connection.is_connected() and self._should_attempt_reconnection():
                    if not self._reconnect_in_progress:
                        self._reconnect_in_progress = True
                        logging.info(f"Connection monitor initiating reconnection for {self}")
                        try:
                            # Ensure clean state before reconnection
                            # Cancel the reader task if it's still running
                            if self.reader_task and not self.reader_task.done():
                                logging.debug(f"Canceling reader task before reconnection for {self}")
                                self.reader_task.cancel()
                                try:
                                    await self.reader_task
                                except asyncio.CancelledError:
                                    pass
                                self.reader_task = None
                            
                            # Reconnect and restart the reader task
                            await self.connection.open()
                            
                            # Restart the reader task after successful reconnection
                            self.reader_task = asyncio.create_task(self._reader())
                            logging.info(f"Connection monitor successfully reconnected {self} and restarted reader task")
                        except Exception as e:
                            logging.debug(f"Connection monitor failed to reconnect {self.host}:{self.port}: {type(e).__name__}")
                        finally:
                            self._reconnect_in_progress = False
                            
            except Exception as e:
                logging.error(f"Error in connection monitor task for {self}: {e}")
                await asyncio.sleep(5.0)  # Wait before retrying
                
        logging.debug(f"Connection monitor task stopped for {self}")
    
    def _should_attempt_reconnection(self) -> bool:
        """Determine if reconnection should be attempted based on client state."""
        # Always attempt reconnection for main client unless explicitly disconnected
        return self.is_connected

    async def __aenter__(self):
        """Async context manager entry - connects to the telescope."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - disconnects from the telescope."""
        await self.disconnect()
        # Don't suppress exceptions
        return False

    def __str__(self):
        return f"{self.host}:{self.port}"
