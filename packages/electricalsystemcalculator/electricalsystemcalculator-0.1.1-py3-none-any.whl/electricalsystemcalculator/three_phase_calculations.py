
"""
three_phase_calculations.py

Contains the ThreePhaseCalculations class for three-phase electrical system analysis.
"""

import math
import logging
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThreePhaseCalculations:
    """
    ThreePhaseCalculations provides methods for performing calculations
    relevant to three-phase electrical systems, such as power, energy,
    voltage, current, phase difference, phase sequence, and unbalance.
    """

    def calculate_power_factor(self, phase: List[float]) -> float:
        """
        Calculate the average power factor for a three-phase system.

        Args:
            phase (list): List of six phase angles in degrees
                [V_A, V_B, V_C, I_A, I_B, I_C]
        Returns:
            float: Average power factor
        """
        power_factor = (
            math.cos(math.radians(phase[0] - phase[3])) +
            math.cos(math.radians(phase[1] - phase[4])) +
            math.cos(math.radians(phase[2] - phase[5]))
        ) / 3
        logger.debug(
            f"Power factor calculation: phase={phase}, result={power_factor}"
        )
        return power_factor
    def calculate_active_power(
        self, amplitude: List[float], phase: List[float]
    ) -> float:
        """
        Calculate the total active (real) power in kW for a three-phase system.

        Args:
            amplitude (list): List of six amplitudes
                [V_A, V_B, V_C, I_A, I_B, I_C]
            phase (list): List of six phase angles in degrees
                [V_A, V_B, V_C, I_A, I_B, I_C]
        Returns:
            float: Total active power in kW
        """
        active_power = (
            amplitude[0] * amplitude[3] * math.cos(math.radians(phase[0] - phase[3])) +
            amplitude[1] * amplitude[4] * math.cos(math.radians(phase[1] - phase[4])) +
            amplitude[2] * amplitude[5] * math.cos(math.radians(phase[2] - phase[5]))
        ) / 1000
        logger.debug(
            f"Active power calculation: amplitude={amplitude}, phase={phase}, result={active_power}"
        )
        return active_power
    def calculate_reactive_power(
        self, amplitude: List[float], phase: List[float]
    ) -> float:
        """
        Calculate the total reactive power in kVAR for a three-phase system.

        Args:
            amplitude (list): List of six amplitudes
                [V_A, V_B, V_C, I_A, I_B, I_C]
            phase (list): List of six phase angles in degrees
                [V_A, V_B, V_C, I_A, I_B, I_C]
        Returns:
            float: Total reactive power in kVAR
        """
        reactive_power = (
            amplitude[0] * amplitude[3] * math.sin(math.radians(phase[0] - phase[3])) +
            amplitude[1] * amplitude[4] * math.sin(math.radians(phase[1] - phase[4])) +
            amplitude[2] * amplitude[5] * math.sin(math.radians(phase[2] - phase[5]))
        ) / 1000
        logger.debug(
            f"Reactive power calculation: amplitude={amplitude}, phase={phase}, result={reactive_power}"
        )
        return reactive_power
    def calculate_apparent_power(self, amplitude: List[float]) -> float:
        """
        Calculate the total apparent power in kVA for a three-phase system.

        Args:
            amplitude (list): List of six amplitudes
                [V_A, V_B, V_C, I_A, I_B, I_C]
        Returns:
            float: Total apparent power in kVA
        """
        apparent_power = (
            amplitude[0] * amplitude[3] +
            amplitude[1] * amplitude[4] +
            amplitude[2] * amplitude[5]
        ) / 1000
        logger.debug(
            f"Apparent power calculation: amplitude={amplitude}, result={apparent_power}"
        )
        return apparent_power
    def calculate_active_energy(
        self, amplitude: List[float], phase: List[float], time: float
    ) -> float:
        """
        Calculate the total active energy in kWh for a three-phase system over a given time.

        Args:
            amplitude (list): List of six amplitudes
                [V_A, V_B, V_C, I_A, I_B, I_C]
            phase (list): List of six phase angles in degrees
                [V_A, V_B, V_C, I_A, I_B, I_C]
            time (float): Time in hours
        Returns:
            float: Total active energy in kWh
        """
        active_energy = (
            amplitude[0] * amplitude[3] * math.cos(math.radians(phase[0] - phase[3])) +
            amplitude[1] * amplitude[4] * math.cos(math.radians(phase[1] - phase[4])) +
            amplitude[2] * amplitude[5] * math.cos(math.radians(phase[2] - phase[5]))
        ) / 1000 * float(time)
        logger.debug(
            f"Active energy calculation: amplitude={amplitude}, phase={phase}, time={time}, result={active_energy}"
        )
        return active_energy
    def calculate_reactive_energy(
        self, amplitude: List[float], phase: List[float], time: float
    ) -> float:
        """
        Calculate the total reactive energy in kVARh for a three-phase system over a given time.

        Args:
            amplitude (list): List of six amplitudes
                [V_A, V_B, V_C, I_A, I_B, I_C]
            phase (list): List of six phase angles in degrees
                [V_A, V_B, V_C, I_A, I_B, I_C]
            time (float): Time in hours
        Returns:
            float: Total reactive energy in kVARh
        """
        reactive_energy = (
            amplitude[0] * amplitude[3] * math.sin(math.radians(phase[0] - phase[3])) +
            amplitude[1] * amplitude[4] * math.sin(math.radians(phase[1] - phase[4])) +
            amplitude[2] * amplitude[5] * math.sin(math.radians(phase[2] - phase[5]))
        ) / 1000 * float(time)
        logger.debug(
            f"Reactive energy calculation: amplitude={amplitude}, phase={phase}, time={time}, result={reactive_energy}"
        )
        return reactive_energy
    def calculate_apparent_energy(
        self, amplitude: List[float], time: float
    ) -> float:
        """
        Calculate the total apparent energy in kVAh for a three-phase system over a given time.

        Args:
            amplitude (list): List of six amplitudes
                [V_A, V_B, V_C, I_A, I_B, I_C]
            time (float): Time in hours
        Returns:
            float: Total apparent energy in kVAh
        """
        apparent_energy = (
            amplitude[0] * amplitude[3] +
            amplitude[1] * amplitude[4] +
            amplitude[2] * amplitude[5]
        ) / 1000 * float(time)
        logger.debug(
            f"Apparent energy calculation: amplitude={amplitude}, time={time}, result={apparent_energy}"
        )
        return apparent_energy
    def calculate_average_current(self, amplitude: List[float]) -> float:
        """
        Calculate the average current for a three-phase system.

        Args:
            amplitude (list): List of six amplitudes
                [V_A, V_B, V_C, I_A, I_B, I_C]
        Returns:
            float: Average current (A)
        """
        average_current = (
            amplitude[3] + amplitude[4] + amplitude[5]
        ) / 3
        logger.debug(
            f"Average current calculation: amplitude={amplitude}, result={average_current}"
        )
        return average_current
    def calculate_average_voltage(self, amplitude: List[float]) -> float:
        """
        Calculate the average line-to-line voltage for a three-phase system.

        Args:
            amplitude (list): List of six amplitudes
                [V_A, V_B, V_C, I_A, I_B, I_C]
        Returns:
            float: Average voltage (V)
        """
        average_voltage = (
            amplitude[0] * 1.73 + amplitude[1] * 1.73 + amplitude[2] * 1.73
        ) / 3
        logger.debug(
            f"Average voltage calculation: amplitude={amplitude}, result={average_voltage}"
        )
        return average_voltage

    def calculate_rms_voltage(self, amplitude: float) -> float:
        """
        Calculate the RMS voltage for a given phase amplitude in a three-phase system.

        Args:
            amplitude (float): Phase voltage amplitude
        Returns:
            float: RMS voltage (V)
        """
        rms_voltage = float(amplitude) * 1.73
        logger.debug(
            f"RMS voltage calculation: amplitude={amplitude}, result={rms_voltage}"
        )
        return rms_voltage

    def calculate_rms_voltage_for_imbalance(
        self, amplitude1: float, amplitude2: float, phase1: float, phase2: float
    ) -> float:
        """
        Calculate the RMS voltage difference for imbalance between two phases.

        Args:
            amplitude1 (float): Amplitude of phase 1
            amplitude2 (float): Amplitude of phase 2
            phase1 (float): Phase angle of phase 1 (degrees)
            phase2 (float): Phase angle of phase 2 (degrees)
        Returns:
            float: RMS voltage difference (V)
        """
        x = round(
            amplitude2 * math.cos(math.radians(phase2)) -
            amplitude1 * math.cos(math.radians(phase1)), 2
        )
        y = round(
            amplitude2 * math.sin(math.radians(phase2)) -
            amplitude1 * math.sin(math.radians(phase1)), 2
        )
        result = round(math.sqrt(math.pow(x, 2) + math.pow(y, 2)), 2)
        logger.debug(
            f"RMS voltage for imbalance: amplitude1={amplitude1}, amplitude2={amplitude2}, phase1={phase1}, phase2={phase2}, result={result}"
        )
        return result

    def phase_difference(self, phase1: float, phase2: float) -> float:
        """
        Calculate the phase difference (in degrees) between two signals.

        Args:
            phase1 (float): Phase angle of first signal in degrees
            phase2 (float): Phase angle of second signal in degrees
        Returns:
            float: Phase difference in degrees (absolute value)
        """
        result = abs((phase1 - phase2) % 360)
        logger.debug(
            f"Phase difference: phase1={phase1}, phase2={phase2}, result={result}"
        )
        return result

    def phase_sequence(self, phases: List[float]) -> str:
        """
        Detect the phase sequence (ABC or ACB) for a three-phase system.

        Args:
            phases (list): List of three phase angles in degrees [A, B, C]
        Returns:
            str: 'ABC' for positive sequence, 'ACB' for negative sequence
        """
        if len(phases) != 3:
            logger.error('Invalid input: Must provide exactly three phase angles.')
            return 'Invalid input: Must provide exactly three phase angles.'

        # Normalize angles to be within a 360-degree range
        a, b, c = [p % 360 for p in phases]
        logger.debug(f"Normalized angles: a={a}, b={b}, c={c}")

        # Calculate the phase difference between A and B, and A and C
        diff_ab = (b - a + 360) % 360
        diff_ac = (c - a + 360) % 360
        logger.debug(f"Phase differences: diff_ab={diff_ab}, diff_ac={diff_ac}")

        # Check for ABC sequence: B leads A by 120 degrees
        if abs(diff_ab - 120) < 1.0:
            # In a balanced system, C leads A by 240 degrees (or lags by 120)
            if abs(diff_ac - 240) < 1.0 or abs(diff_ac - (-120)) < 1.0:
                logger.info(f"Phase sequence detected: ABC for phases={phases}")
                return 'ABC'

        # Check for ACB sequence: C leads A by 120 degrees
        elif abs(diff_ac - 120) < 1.0:
            # In a balanced system, B leads A by 240 degrees (or lags by 120)
            if abs(diff_ab - 240) < 1.0 or abs(diff_ab - (-120)) < 1.0:
                logger.info(f"Phase sequence detected: ACB for phases={phases}")
                return 'ACB'

        logger.warning(f"Unknown phase sequence for phases={phases}")
        return 'Unknown'

    def phase_angle_from_complex(self, real: float, imag: float) -> float:
        """
        Calculate phase angle (in degrees) from real and imaginary parts of a phasor.

        Args:
            real (float): Real part
            imag (float): Imaginary part
        Returns:
            float: Phase angle in degrees
        """
        result = math.degrees(math.atan2(imag, real))
        logger.debug(
            f"Phase angle from complex: real={real}, imag={imag}, result={result}"
        )
        return result

    def phase_unbalance(self, phases: List[float]) -> float:
        """
        Calculate phase unbalance as the maximum deviation from the average phase angle in a three-phase system.

        Args:
            phases (list): List of three phase angles in degrees [A, B, C]
        Returns:
            float: Maximum unbalance in degrees
        """
        avg = sum(phases) / 3
        result = max(abs(p - avg) for p in phases)
        logger.debug(
            f"Phase unbalance: phases={phases}, avg={avg}, result={result}"
        )
        return result