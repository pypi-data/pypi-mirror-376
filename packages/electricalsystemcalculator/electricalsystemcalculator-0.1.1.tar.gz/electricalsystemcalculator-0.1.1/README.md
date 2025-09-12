
# electricalsystemcalculator

`electricalsystemcalculator` is a Python library for performing advanced calculations in three-phase electrical power systems. It is designed for engineers, students, and researchers who need to analyze, simulate, or monitor three-phase systems in industrial, commercial, or academic settings.

## Features

- Calculate active, reactive, and apparent power and energy for three-phase systems
- Compute average current and voltage
- Calculate RMS voltage and voltage imbalance
- Phase calculations: phase difference, phase sequence detection, phase angle from real/imaginary parts, and phase unbalance
- Built-in logging for debugging and analysis
- Well-documented, type-annotated API

## Installation

Clone or download this repository, then use the library directly in your project:

```bash
git clone https://github.com/Modular-Minds/ElectricalSystemCalculator
```

Or copy the `electricalsystemcalculator` folder into your project.

## Usage Example

```python
from electricalsystemcalculator.three_phase_calculations import ThreePhaseCalculations

# Example data for a three-phase system
amplitude = [230, 230, 230, 10, 10, 10]  # [V_A, V_B, V_C, I_A, I_B, I_C]
phase = [0, -120, 120, 10, -110, 130]    # [V_A, V_B, V_C, I_A, I_B, I_C]
time = 2  # hours


tpc = ThreePhaseCalculations()

active_power = tpc.calculate_active_power(amplitude, phase)
print(f"Active Power (kW): {active_power}")

reactive_power = tpc.calculate_reactive_power(amplitude, phase)
print(f"Reactive Power (kVAR): {reactive_power}")

apparent_power = tpc.calculate_apparent_power(amplitude)
print(f"Apparent Power (kVA): {apparent_power}")

active_energy = tpc.calculate_active_energy(amplitude, phase, time)
print(f"Active Energy (kWh): {active_energy}")

phase_diff = tpc.phase_difference(30, 10)
print(f"Phase Difference (deg): {phase_diff}")
```

## API Overview

### Class: `ThreePhaseCalculations`

**Power and Energy**
- `calculate_power_factor(phase: List[float]) -> float`
- `calculate_active_power(amplitude: List[float], phase: List[float]) -> float`
- `calculate_reactive_power(amplitude: List[float], phase: List[float]) -> float`
- `calculate_apparent_power(amplitude: List[float]) -> float`
- `calculate_active_energy(amplitude: List[float], phase: List[float], time: float) -> float`
- `calculate_reactive_energy(amplitude: List[float], phase: List[float], time: float) -> float`
- `calculate_apparent_energy(amplitude: List[float], time: float) -> float`

**Current and Voltage**
- `calculate_average_current(amplitude: List[float]) -> float`
- `calculate_average_voltage(amplitude: List[float]) -> float`
- `calculate_rms_voltage(amplitude: float) -> float`
- `calculate_rms_voltage_for_imbalance(amplitude1: float, amplitude2: float, phase1: float, phase2: float) -> float`

**Phase Calculations**
- `phase_difference(phase1: float, phase2: float) -> float`
- `phase_sequence(phases: List[float]) -> str`
- `phase_angle_from_complex(real: float, imag: float) -> float`
- `phase_unbalance(phases: List[float]) -> float`

## Logging

The library uses Python's built-in `logging` module. You can control the verbosity by setting the logging level in your application:

```python
import logging
logging.basicConfig(level=logging.DEBUG)  # or INFO, WARNING, etc.
```

## Example Scripts

See the `example/` folder for a ready-to-run script demonstrating all major features.

## License

MIT
