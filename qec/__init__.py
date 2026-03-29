"""
Quantum Error Correction (QEC) package.

Implements Shor Code and Surface Code simulations using Qiskit,
with noise modeling, benchmarking, and visualization utilities.
"""

from qec import noise, shor, surface, benchmark, visualize

__all__ = ["noise", "shor", "surface", "benchmark", "visualize"]
