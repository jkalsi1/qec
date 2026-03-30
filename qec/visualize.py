"""Reusable plotting functions for QEC results."""

import pathlib
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from qiskit import QuantumCircuit


def plot_threshold(
    df: pd.DataFrame,
    title: str,
    output_dir: str = "results",
) -> Figure:
    """Plots logical vs physical error rate on a log-log scale. Returns Figure."""
    fig, ax = plt.subplots()

    for code in df["code"].unique():
        subset = df[df["code"] == code]
        ax.plot(subset["p_physical"], subset["p_logical"], marker="o", label=code)

    # Reference line y = x
    p_vals = df["p_physical"].sort_values().unique()
    ax.plot(p_vals, p_vals, linestyle="--", color="grey", label="no encoding")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Physical Error Rate")
    ax.set_ylabel("Logical Error Rate")
    ax.set_title(title)
    ax.legend()

    out = pathlib.Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{title.replace(' ', '_')}.png")

    return fig


def plot_circuit(
    qc: QuantumCircuit,
    filename: str,
    output_dir: str = "results",
) -> Figure:
    """Draws Qiskit circuit and saves to output_dir. Returns Figure."""
    fig = qc.draw("mpl")

    out = pathlib.Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{filename}.png")

    return fig
