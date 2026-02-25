"""
PMU (Phasor Measurement Unit) signal simulator following IEEE C37.118 parameters.
Generates synthetic power grid sensor data for normal and anomalous conditions.
"""

import numpy as np

# -----------------------------------------------------------------------------
# IEEE C37.118–style constants (per unit, 50 Hz nominal)
# -----------------------------------------------------------------------------
NOMINAL_VOLTAGE = 1.0  # per unit
NOMINAL_FREQUENCY = 50.0  # Hz
SAMPLING_RATE = 50  # samples per second
SAMPLES_PER_READING = 50


def generate_normal_signal():
    """
    Returns a single PMU-style reading with no anomaly.
    Voltage is a clean 50 Hz sine at 1.0 pu; frequency has small random noise.
    """
    t = np.arange(SAMPLES_PER_READING) / SAMPLING_RATE
    phase_offset = np.pi / 4
    voltage = NOMINAL_VOLTAGE * np.sin(2 * np.pi * NOMINAL_FREQUENCY * t + phase_offset)
    frequency = NOMINAL_FREQUENCY + np.random.normal(0, 0.01, size=SAMPLES_PER_READING)
    return {
        "voltage": voltage,
        "frequency": frequency,
        "anomaly_type": "none",
        "severity": "none",
    }


def generate_point_anomaly():
    """
    Returns a PMU reading with one spiked sample (point anomaly).
    A single random index is set to 1.3–1.5 pu; severity is 'high' if > 1.4 else 'medium'.
    """
    t = np.arange(SAMPLES_PER_READING) / SAMPLING_RATE
    phase_offset = np.pi / 4
    voltage = NOMINAL_VOLTAGE * np.sin(2 * np.pi * NOMINAL_FREQUENCY * t + phase_offset).astype(np.float64)
    frequency = NOMINAL_FREQUENCY + np.random.normal(0, 0.01, size=SAMPLES_PER_READING)

    spike_value = np.random.uniform(1.3, 1.5)
    spike_index = np.random.randint(0, SAMPLES_PER_READING)
    voltage[spike_index] = spike_value

    severity = "high" if spike_value > 1.4 else "medium"
    return {
        "voltage": voltage,
        "frequency": frequency,
        "anomaly_type": "point",
        "severity": severity,
    }


def generate_trend_anomaly():
    """
    Returns a PMU reading with a gradual voltage drift (trend anomaly).
    Voltage envelope drifts from 1.0 pu to 1.2 pu over the 50 samples.
    """
    t = np.arange(SAMPLES_PER_READING) / SAMPLING_RATE
    phase_offset = np.pi / 4
    # Linear ramp from 1.0 to 1.2 over 50 samples
    envelope = np.linspace(NOMINAL_VOLTAGE, 1.2, SAMPLES_PER_READING)
    voltage = envelope * np.sin(2 * np.pi * NOMINAL_FREQUENCY * t + phase_offset)
    frequency = NOMINAL_FREQUENCY + np.random.normal(0, 0.01, size=SAMPLES_PER_READING)
    return {
        "voltage": voltage,
        "frequency": frequency,
        "anomaly_type": "trend",
        "severity": "medium",
    }


def generate_batch(n=100):
    """
    Returns a list of n PMU readings, randomly mixed:
    ~40% normal, ~35% point anomaly, ~25% trend anomaly.
    """
    readings = []
    n_normal = int(round(0.40 * n))
    n_point = int(round(0.35 * n))
    n_trend = n - n_normal - n_point  # remainder so total is exactly n

    for _ in range(n_normal):
        readings.append(generate_normal_signal())
    for _ in range(n_point):
        readings.append(generate_point_anomaly())
    for _ in range(n_trend):
        readings.append(generate_trend_anomaly())

    np.random.shuffle(readings)
    return readings
