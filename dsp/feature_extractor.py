"""
Feature extraction from PMU-style signal dictionaries.
Takes raw voltage/frequency from signal_simulator and computes DSP-derived metrics.
"""

import numpy as np
from scipy import signal as scipy_signal
from scipy import fft


def bandpass_filter(signal, lowcut=45.0, highcut=55.0, fs=50, order=3):
    """
    Applies a Butterworth bandpass filter to isolate the fundamental (e.g. 50 Hz) and
    remove DC and high-frequency noise. Filtering between 45–55 Hz keeps the nominal
    frequency and attenuates the rest. If the signal is too short for the filter
    (e.g. fewer than ~3× filter length), returns the original signal unchanged.
    """
    signal = np.asarray(signal, dtype=np.float64)
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    if low >= 1 or high >= 1 or low <= 0 or high <= 0:
        return signal
    try:
        b, a = scipy_signal.butter(order, [low, high], btype="band")
        filtered = scipy_signal.filtfilt(b, a, signal)
        return filtered
    except (ValueError, np.linalg.LinAlgError):
        return signal


def compute_rms(signal):
    """
    Root Mean Square: sqrt(mean(signal²)). Measures the “average power” of the
    signal in a way that matches AC voltage definitions (e.g. 1 pu sine → ~0.707 RMS).
    Returns a single float rounded to 4 decimal places.
    """
    signal = np.asarray(signal, dtype=np.float64)
    if signal.size == 0:
        return 0.0
    rms = np.sqrt(np.mean(signal ** 2))
    return round(float(rms), 4)


def compute_thd(signal, fs=50, fundamental=50.0):
    """
    Total Harmonic Distortion (THD) as a percentage: how much of the signal energy
    is in harmonics (2×, 3×, … the fundamental) rather than the fundamental.
    Uses FFT to get the spectrum, finds the fundamental amplitude and the next
    few harmonic amplitudes, then THD% = 100 × sqrt(sum of harmonic squared amps) / fundamental_amp.
    Returns a float percentage rounded to 4 decimal places.
    """
    signal = np.asarray(signal, dtype=np.float64)
    n = len(signal)
    if n == 0:
        return 0.0
    # Zero-pad for finer frequency resolution so we can pick the fundamental and harmonics
    n_fft = max(n, 2 ** int(np.ceil(np.log2(n))))
    spectrum = np.abs(fft.fft(signal, n=n_fft))
    freqs = fft.fftfreq(n_fft, 1 / fs)
    # Use positive frequencies only (real signal)
    half = n_fft // 2
    spectrum = spectrum[: half + 1]
    freqs = freqs[: half + 1]
    # Find bin closest to fundamental
    fund_bin = int(round(fundamental * n_fft / fs))
    fund_bin = max(1, min(fund_bin, half))
    fund_amp = spectrum[fund_bin]
    if fund_amp <= 0:
        return 0.0
    # Sum squared amplitudes at 2×, 3×, 4×, 5× fundamental (standard THD)
    harmonic_amps_sq = 0.0
    for h in range(2, 6):
        bin_h = h * fund_bin
        if bin_h <= half:
            harmonic_amps_sq += spectrum[bin_h] ** 2
    thd_pct = 100.0 * np.sqrt(harmonic_amps_sq) / fund_amp
    return round(float(thd_pct), 4)


def compute_frequency_deviation(frequency_array):
    """
    Measures how far the reported frequency is from the nominal 50 Hz on average.
    Takes the mean of the absolute differences from 50 Hz; useful for detecting
    under/over-frequency events. Returns absolute deviation in Hz, rounded to 4 decimals.
    """
    arr = np.asarray(frequency_array, dtype=np.float64)
    if arr.size == 0:
        return 0.0
    deviation = np.mean(np.abs(arr - 50.0))
    return round(float(deviation), 4)


def extract_features(reading):
    """
    Takes a full reading dictionary from signal_simulator (keys: voltage, frequency,
    anomaly_type, severity) and returns a feature dictionary with: rms_voltage,
    thd_percent, frequency_deviation_hz, peak_voltage (max absolute value of the
    bandpass-filtered voltage), plus anomaly_type and severity passed through.
    RMS and THD use the raw voltage (filter at fs=50 with 50 samples zeros out the signal);
    only peak_voltage uses the filtered signal.
    """
    voltage = np.asarray(reading["voltage"], dtype=np.float64)
    frequency_array = reading["frequency"]
    filtered = bandpass_filter(voltage, lowcut=45.0, highcut=55.0, fs=50, order=3)
    rms_voltage = compute_rms(voltage)
    thd_percent = compute_thd(voltage, fs=50, fundamental=50.0)
    frequency_deviation_hz = compute_frequency_deviation(frequency_array)
    peak_voltage = round(float(np.max(np.abs(filtered))), 4)
    return {
        "rms_voltage": rms_voltage,
        "thd_percent": thd_percent,
        "frequency_deviation_hz": frequency_deviation_hz,
        "peak_voltage": peak_voltage,
        "anomaly_type": reading["anomaly_type"],
        "severity": reading["severity"],
    }
