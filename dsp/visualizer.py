"""
Plots PMU signals and extracted features for visual verification.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from dsp.signal_simulator import (
    generate_normal_signal,
    generate_point_anomaly,
    generate_trend_anomaly,
    generate_batch,
    SAMPLING_RATE,
)
from dsp.feature_extractor import extract_features


def plot_signal(reading, title="PMU Signal"):
    """
    Creates a figure with voltage and frequency subplots, annotates anomaly info,
    saves to outputs/signal_plot.png and displays.
    """
    t = np.arange(len(reading["voltage"])) / SAMPLING_RATE
    fig, (ax_voltage, ax_freq) = plt.subplots(2, 1, figsize=(8, 6))

    ax_voltage.plot(t, reading["voltage"], color="steelblue")
    ax_voltage.set_ylabel("Voltage (pu)")
    ax_voltage.set_xlabel("Time (s)")
    ax_voltage.grid(True)
    textstr = f"anomaly_type: {reading['anomaly_type']}\nseverity: {reading['severity']}"
    ax_voltage.text(0.02, 0.98, textstr, transform=ax_voltage.transAxes, fontsize=9,
                    verticalalignment="top", bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))

    ax_freq.plot(t, reading["frequency"], color="darkgreen")
    ax_freq.set_ylabel("Frequency (Hz)")
    ax_freq.set_xlabel("Time (s)")
    ax_freq.grid(True)

    fig.suptitle(title)
    fig.tight_layout()

    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "signal_plot.png")
    plt.show()


def plot_batch_summary(batch, features_list):
    """
    Creates a 2x2 summary figure: histograms of rms_voltage, peak_voltage,
    frequency_deviation_hz, and a bar chart of anomaly_type counts.
    """
    rms_vals = [f["rms_voltage"] for f in features_list]
    peak_vals = [f["peak_voltage"] for f in features_list]
    freq_dev_vals = [f["frequency_deviation_hz"] for f in features_list]
    anomaly_types = [f["anomaly_type"] for f in features_list]

    type_order = ["none", "point", "trend"]
    type_counts = [anomaly_types.count(t) for t in type_order]
    colors = ["#2ecc71", "#e74c3c", "#3498db"]

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))

    ax1.hist(rms_vals, bins=15, color="steelblue", edgecolor="white")
    ax1.set_xlabel("RMS Voltage (pu)")
    ax1.set_ylabel("Count")
    ax1.set_title("RMS Voltage")
    ax1.grid(True, alpha=0.3)

    ax2.hist(peak_vals, bins=15, color="coral", edgecolor="white")
    ax2.set_xlabel("Peak Voltage (pu)")
    ax2.set_ylabel("Count")
    ax2.set_title("Peak Voltage")
    ax2.grid(True, alpha=0.3)

    ax3.hist(freq_dev_vals, bins=15, color="mediumseagreen", edgecolor="white")
    ax3.set_xlabel("Frequency deviation (Hz)")
    ax3.set_ylabel("Count")
    ax3.set_title("Frequency deviation")
    ax3.grid(True, alpha=0.3)

    bars = ax4.bar(type_order, type_counts, color=colors, edgecolor="white")
    ax4.set_xlabel("Anomaly type")
    ax4.set_ylabel("Count")
    ax4.set_title("Anomaly type counts")
    ax4.grid(True, alpha=0.3, axis="y")

    fig.suptitle("PMU Batch Summary", fontsize=14)
    fig.tight_layout()

    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "batch_summary.png")
    plt.show()


if __name__ == "__main__":
    normal = generate_normal_signal()
    point = generate_point_anomaly()
    trend = generate_trend_anomaly()

    plot_signal(normal, title="PMU Signal — Normal")
    plot_signal(point, title="PMU Signal — Point Anomaly")
    plot_signal(trend, title="PMU Signal — Trend Anomaly")

    batch = generate_batch(100)
    features_list = [extract_features(r) for r in batch]
    plot_batch_summary(batch, features_list)
