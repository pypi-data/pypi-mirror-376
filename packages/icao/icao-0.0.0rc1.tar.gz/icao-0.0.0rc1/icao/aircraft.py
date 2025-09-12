import logging
import threading
import time
from dataclasses import dataclass
from typing import List, Optional

from .beast import BeastServer
from .mode_s import adsb


@dataclass
class AircraftState:
    icao: int
    callsign: str
    latitude: float
    longitude: float
    altitude: float
    heading: Optional[float] = None
    speed: Optional[float] = None
    vertical_rate: Optional[float] = None
    squawk: Optional[int] = None
    on_ground: bool = False

    def __post_init__(self):
        if not (0 <= self.icao <= 0xFFFFFF):
            raise ValueError(f"ICAO address must be 24-bit: {self.icao:06X}")
        if len(self.callsign) > 8:
            raise ValueError(f"Callsign too long (max 8 chars): {self.callsign}")
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Invalid longitude: {self.longitude}")


class Aircraft:
    def __init__(self, state: AircraftState):
        self.state = state
        self.last_id_time = 0.0
        self.last_pos_time = 0.0

    @classmethod
    def create(
        cls,
        icao: int,
        callsign: str,
        lat: float,
        lon: float,
        alt: float,
        heading: Optional[float] = None,
        speed: Optional[float] = None,
    ) -> "Aircraft":
        state = AircraftState(
            icao=icao,  # ICAO address
            callsign=callsign,  # aircraft callsign
            latitude=lat,  # latitude in decimal degrees
            longitude=lon,  # longitude in decimal degrees
            altitude=alt,  # altitude in feet
            heading=heading,  # (optional) heading in degrees
            speed=speed,  # (optional) speed in knots
        )
        return cls(state)

    def update_position(self, lat: float, lon: float, alt: Optional[float] = None):
        self.state.latitude = lat
        self.state.longitude = lon
        if alt is not None:
            self.state.altitude = alt

    def update_state(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)

    def generate_identification_message(self) -> bytes:
        return adsb.get_identification_message(
            self.state.icao, 4, 5, self.state.callsign, 5
        )

    def generate_position_messages(self, tc: int = 18) -> tuple[bytes, bytes]:
        surface = 1 if self.state.on_ground else 0
        return adsb.get_encoded_position(
            5,  # ca: capability
            self.state.icao,
            tc,  # tc: type code (9-18, determines accuracy)
            0,  # ss: surveillance status
            0,  # nicsb: navigation integrity category
            self.state.altitude,
            0,  # time
            self.state.latitude,
            self.state.longitude,
            surface,
        )

    def should_send_identification(
        self, current_time: float, interval: float = 10.0
    ) -> bool:
        return current_time - self.last_id_time > interval

    def should_send_position(self, current_time: float, interval: float = 0.5) -> bool:
        return current_time - self.last_pos_time > interval

    def mark_identification_sent(self, timestamp: Optional[float] = None):
        self.last_id_time = timestamp or time.time()

    def mark_position_sent(self, timestamp: Optional[float] = None):
        self.last_pos_time = timestamp or time.time()

    def __repr__(self) -> str:
        return f"Aircraft(state={self.state!r})"


class ADSBSimulator:
    def __init__(self, host: str = "0.0.0.0", port: int = 30005):
        self.aircraft = {}
        self.running = False
        self.beast_server = BeastServer(host, port)
        self.broadcast_thread = None

        self.id_interval = 10.0
        self.pos_interval = 0.5
        self.pos_pair_delay = 0.1

    def add_aircraft(self, aircraft: Aircraft):
        self.aircraft[aircraft.state.icao] = aircraft
        logging.info(
            f"Added aircraft {aircraft.state.callsign} (ICAO: {aircraft.state.icao:06X})"
        )

    def remove_aircraft(self, icao: int):
        if icao in self.aircraft:
            aircraft = self.aircraft.pop(icao)
            logging.info(
                f"Removed aircraft {aircraft.state.callsign} (ICAO: {icao:06X})"
            )

    def get_aircraft(self, icao: int) -> Optional[Aircraft]:
        return self.aircraft.get(icao)

    def list_aircraft(self) -> List[Aircraft]:
        return list(self.aircraft.values())

    def clear_aircraft(self):
        self.aircraft.clear()

    def set_timing(
        self,
        id_interval: float = 10.0,
        pos_interval: float = 0.5,
        pos_pair_delay: float = 0.1,
    ):
        self.id_interval = id_interval  # identification messages
        self.pos_interval = pos_interval  # position messages
        self.pos_pair_delay = pos_pair_delay  # delay between even/odd position messages

    def start(self) -> bool:
        if not self.beast_server.start():
            return False
        self.running = True
        self.broadcast_thread = threading.Thread(
            target=self._broadcast_loop, daemon=True
        )
        self.broadcast_thread.start()

        logging.info(f"ADS-B simulator started with {len(self.aircraft)} aircraft")
        return True

    def stop(self):
        self.running = False
        self.beast_server.stop()
        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=1.0)

        logging.info("ADS-B simulator stopped")

    def _broadcast(
        self, force: bool = False
    ) -> int:  # force: send regardless of timing
        current_time = time.time()
        message_count = 0

        for aircraft in list(self.aircraft.values()):
            if force or aircraft.should_send_identification(
                current_time, self.id_interval
            ):
                id_message = aircraft.generate_identification_message()
                if self.beast_server.broadcast_message(id_message):
                    message_count += 1
                aircraft.mark_identification_sent(current_time)

            if force or aircraft.should_send_position(current_time, self.pos_interval):
                even_frame, odd_frame = aircraft.generate_position_messages()
                if self.beast_server.broadcast_message(even_frame):
                    message_count += 1
                time.sleep(self.pos_pair_delay)
                if self.beast_server.broadcast_message(odd_frame):
                    message_count += 1

                aircraft.mark_position_sent(current_time)

        return message_count

    def _broadcast_loop(self):
        while self.running:
            self._broadcast()
            time.sleep(0.1)

    def __len__(self) -> int:
        return len(self.aircraft)

    def __iter__(self):
        return iter(self.aircraft.values())
