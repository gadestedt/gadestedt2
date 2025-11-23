import argparse
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, Tuple

import tkinter as tk


SensorValue = Tuple[str, float]


@dataclass
class SensorReading:
    name: str
    unit: str
    value: float


class SensorProvider:
    def initial_readings(self) -> Iterable[SensorReading]:
        raise NotImplementedError

    def read(self) -> Iterable[SensorReading]:
        raise NotImplementedError


class SenseairTSenseReader(SensorProvider):
    """Hämtar mätvärden via Modbus RTU från en Senseair tSENSE över seriell port."""

    def __init__(
        self,
        port: str,
        *,
        slave_address: int = 1,
        baudrate: int = 9600,
        timeout: float = 1.0,
        co2_register: int = 0x0008,
        temperature_register: int = 0x0009,
        humidity_register: int = 0x000A,
        decimals: int = 1,
    ) -> None:
        import minimalmodbus
        import serial

        self.instrument = minimalmodbus.Instrument(port, slave_address)
        self.instrument.serial.baudrate = baudrate
        self.instrument.serial.bytesize = serial.EIGHTBITS
        self.instrument.serial.parity = serial.PARITY_NONE
        self.instrument.serial.stopbits = serial.STOPBITS_ONE
        self.instrument.serial.timeout = timeout
        self.instrument.mode = minimalmodbus.MODE_RTU

        self.co2_register = co2_register
        self.temperature_register = temperature_register
        self.humidity_register = humidity_register
        self.decimals = decimals

    def initial_readings(self) -> Iterable[SensorReading]:
        return self.read()

    def read(self) -> Iterable[SensorReading]:
        co2 = self.instrument.read_register(self.co2_register, self.decimals, functioncode=4)
        temperature = self.instrument.read_register(
            self.temperature_register, self.decimals, functioncode=4
        )
        humidity = self.instrument.read_register(
            self.humidity_register, self.decimals, functioncode=4
        )

        yield SensorReading("CO₂", "ppm", co2)
        yield SensorReading("Temperatur", "°C", temperature)
        yield SensorReading("Luftfuktighet", "%", humidity)


class SimulatedSensorProvider(SensorProvider):
    def __init__(self) -> None:
        self.current_values: Dict[str, SensorValue] = {
            "Temperatur": ("°C", 21.5),
            "Luftfuktighet": ("%", 40.0),
            "CO₂": ("ppm", 650.0),
        }
        self.min_max: Dict[str, Tuple[float, float]] = {
            "Temperatur": (18.0, 26.0),
            "Luftfuktighet": (25.0, 60.0),
            "CO₂": (400.0, 1200.0),
        }

    def _update_value(self, name: str) -> float:
        unit, current = self.current_values[name]
        minimum, maximum = self.min_max[name]
        delta = random.uniform(-0.5, 0.5)
        updated = max(minimum, min(maximum, current + delta))
        self.current_values[name] = (unit, updated)
        return updated

    def initial_readings(self) -> Iterable[SensorReading]:
        for name, (unit, value) in self.current_values.items():
            yield SensorReading(name, unit, value)

    def read(self) -> Iterable[SensorReading]:
        for name, (unit, _) in self.current_values.items():
            yield SensorReading(name, unit, self._update_value(name))


class SensorGUI:
    """En GUI som kan visa data från tSENSE eller simulera värden."""

    def __init__(self, sensor_provider: "SensorProvider") -> None:
        self.root = tk.Tk()
        self.root.title("Sensorvärden")
        self.root.configure(padx=20, pady=20)

        self.sensor_provider = sensor_provider
        self.sensor_vars: Dict[str, Tuple[tk.StringVar, str]] = {}

        self._build_ui()
        self._update_values()

    def _build_ui(self) -> None:
        header = tk.Label(self.root, text="Sensorpanel", font=("Helvetica", 16, "bold"))
        header.grid(row=0, column=0, sticky="w")

        timestamp_label = tk.Label(self.root, text="Senast uppdaterad:")
        timestamp_label.grid(row=1, column=0, sticky="w", pady=(10, 0))

        self.timestamp_var = tk.StringVar(value="-")
        timestamp_value = tk.Label(self.root, textvariable=self.timestamp_var, font=("Helvetica", 10))
        timestamp_value.grid(row=2, column=0, sticky="w")

        separator = tk.Frame(self.root, height=2, bd=1, relief="sunken")
        separator.grid(row=3, column=0, sticky="we", pady=10)

        sensor_frame = tk.Frame(self.root)
        sensor_frame.grid(row=4, column=0, sticky="w")

        try:
            initial_readings = list(self.sensor_provider.initial_readings())
        except Exception as exc:  # noqa: BLE001 - bredt för att fånga kommunikationsfel
            self.timestamp_var.set(f"Fel vid start: {exc}")
            initial_readings = []

        for idx, reading in enumerate(initial_readings):
            label = tk.Label(sensor_frame, text=reading.name, font=("Helvetica", 12))
            label.grid(row=idx, column=0, sticky="w", padx=(0, 15), pady=2)

            value_var = tk.StringVar(value=f"{reading.value:0.1f} {reading.unit}")
            self.sensor_vars[reading.name] = (value_var, reading.unit)

            value_label = tk.Label(sensor_frame, textvariable=value_var, font=("Helvetica", 12, "bold"))
            value_label.grid(row=idx, column=1, sticky="w", pady=2)

    def _update_values(self) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.timestamp_var.set(now)

        try:
            readings = list(self.sensor_provider.read())
        except Exception as exc:  # noqa: BLE001 - bredt för att fånga kommunikationsfel
            self.timestamp_var.set(f"{now} (fel: {exc})")
        else:
            for reading in readings:
                if reading.name not in self.sensor_vars:
                    continue
                value_var, unit = self.sensor_vars[reading.name]
                value_var.set(f"{reading.value:0.1f} {unit}")

        self.root.after(1000, self._update_values)

    def run(self) -> None:
        self.root.mainloop()

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visa sensorvärden i ett Tkinter-gränssnitt")
    parser.add_argument(
        "--serial-port",
        help="Seriell port för tSENSE (t.ex. COM3 eller /dev/ttyUSB0). Utelämna för simulering.",
    )
    parser.add_argument("--slave-address", type=int, default=1, help="Modbus-slavadress (standard 1)")
    parser.add_argument("--baudrate", type=int, default=9600, help="Baudrate för Modbus-anslutningen")
    parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="Timeout i sekunder för seriell kommunikation (standard 1.0)",
    )
    parser.add_argument("--decimals", type=int, default=1, help="Antal decimaler i registren (standard 1)")
    parser.add_argument(
        "--co2-register", type=lambda x: int(x, 0), default=0x0008, help="Registeradress för CO₂ (standard 0x0008)"
    )
    parser.add_argument(
        "--temperature-register",
        type=lambda x: int(x, 0),
        default=0x0009,
        help="Registeradress för temperatur (standard 0x0009)",
    )
    parser.add_argument(
        "--humidity-register",
        type=lambda x: int(x, 0),
        default=0x000A,
        help="Registeradress för luftfuktighet (standard 0x000A)",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Tvinga simulering även om en seriell port anges (för felsökning)",
    )
    return parser.parse_args()


def build_provider(args: argparse.Namespace) -> SensorProvider:
    if args.serial_port and not args.simulate:
        return SenseairTSenseReader(
            args.serial_port,
            slave_address=args.slave_address,
            baudrate=args.baudrate,
            timeout=args.timeout,
            co2_register=args.co2_register,
            temperature_register=args.temperature_register,
            humidity_register=args.humidity_register,
            decimals=args.decimals,
        )
    return SimulatedSensorProvider()


def main() -> None:
    args = parse_args()
    provider = build_provider(args)
    gui = SensorGUI(provider)
    gui.run()


if __name__ == "__main__":
    main()
