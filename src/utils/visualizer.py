# visualizer.py
# Visualization utilities for ammeter test results.
# Generates time series, histogram, and comparison charts from a results dict.

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from datetime import datetime
import os


# Color per ammeter — consistent across all charts
AMMETER_COLORS = {
    "greenlee": "#2ecc71",
    "entes":    "#3498db",
    "circutor": "#e74c3c",
}


def plot_results(results: dict, save_path: str = None) -> str:
    """
    Generate a 7-panel visualization for all ammeter results:
    - Rows 1-3: Time series per ammeter (separate subplot, own scale)
    - Rows 4-6: Histogram per ammeter (separate subplot, own scale)
    - Row 7:    Bar chart comparing mean ± std across ammeters

    results: dict with ammeter_type as key:
        {
            "greenlee": {"measurements": [(value, timestamp), ...], "statistics": {...}},
            ...
        }
    save_path: optional path to save the figure. If None, saves to results/plots/
    Returns the path to the saved figure.
    """
    if not results:
        raise ValueError("results dict is empty — nothing to plot")

    ammeter_order = ["greenlee", "entes", "circutor"]
    n = len(ammeter_order)

    fig = plt.figure(figsize=(14, 18))
    fig.suptitle("NES Ammeter QA — Measurement Results", fontsize=14, fontweight="bold", y=0.99)

    gs = gridspec.GridSpec(7, 1, figure=fig, hspace=0.7,
                           height_ratios=[1, 1, 1, 1, 1, 1, 1.3])

    # Time series subplots
    ax_time = {name: fig.add_subplot(gs[i]) for i, name in enumerate(ammeter_order)}

    # Histogram subplots
    ax_hist = {name: fig.add_subplot(gs[i + n]) for i, name in enumerate(ammeter_order)}

    # Bar chart
    ax_bar = fig.add_subplot(gs[6])

    ammeter_names = []
    means = []
    stds  = []

    for ammeter_type in ammeter_order:
        if ammeter_type not in results:
            continue

        data         = results[ammeter_type]
        color        = AMMETER_COLORS.get(ammeter_type, "#95a5a6")
        measurements = data["measurements"]
        statistics   = data["statistics"]

        # Extract values and timestamps
        values     = [m[0] for m in measurements]
        timestamps = [m[1] for m in measurements]

        # Normalize timestamps to seconds from start
        t0    = timestamps[0]
        times = [t - t0 for t in timestamps]

        # ── Time series ───────────────────────────────────────────────
        ax = ax_time[ammeter_type]
        ax.plot(times, values, marker="o", color=color, linewidth=1.5, markersize=5)
        ax.set_title(f"{ammeter_type.capitalize()} — Current Over Time", fontsize=9)
        ax.set_xlabel("Time (s)", fontsize=8)
        ax.set_ylabel("Current (A)", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(True, alpha=0.3)

        # ── Histogram ─────────────────────────────────────────────────
        ax = ax_hist[ammeter_type]
        ax.hist(values, bins=max(3, len(values) // 2),
                color=color, alpha=0.8, edgecolor="white")
        ax.set_title(f"{ammeter_type.capitalize()} — Distribution", fontsize=9)
        ax.set_xlabel("Current (A)", fontsize=8)
        ax.set_ylabel("Frequency", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(True, alpha=0.3, axis="y")

        # Collect for bar chart
        ammeter_names.append(ammeter_type.capitalize())
        means.append(statistics["mean"])
        stds.append(statistics["std"])

    # ── Bar chart ─────────────────────────────────────────────────────
    x      = np.arange(len(ammeter_names))
    colors = [AMMETER_COLORS.get(name.lower(), "#95a5a6") for name in ammeter_names]
    bars   = ax_bar.bar(x, means, yerr=stds, capsize=6,
                        color=colors, alpha=0.8, edgecolor="white", linewidth=0.5)

    for bar, mean, std in zip(bars, means, stds):
        ax_bar.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + std + max(means) * 0.02,
                    f"{mean:.3f}A", ha="center", va="bottom", fontsize=9)

    ax_bar.set_title("Mean Current ± Std Dev per Ammeter (log scale)")
    ax_bar.set_xlabel("Ammeter")
    ax_bar.set_ylabel("Current (A)")
    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(ammeter_names)
    ax_bar.set_yscale("log")
    ax_bar.grid(True, alpha=0.3, axis="y")

    # ── Save ──────────────────────────────────────────────────────────
    if save_path is None:
        os.makedirs("results/plots", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = f"results/plots/plot_{timestamp}.png"

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Plot saved to: {save_path}")
    return save_path
