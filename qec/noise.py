"""
Noise model factory for QEC simulations.

Provides `make_noise_model` to construct Qiskit NoiseModel objects
for depolarizing, bit-flip, phase-flip, and combined error channels.
Errors are applied after every gate and on measurement.
"""

from qiskit_aer.noise import (
    NoiseModel,
    depolarizing_error,
    pauli_error,
)
from qiskit_aer.noise.errors import ReadoutError
import numpy as np


def make_noise_model(error_type: str, p: float) -> NoiseModel:
    """
    Build a Qiskit NoiseModel for the given error channel and error rate.

    Parameters
    ----------
    error_type : str
        One of "depolarizing", "bit_flip", "phase_flip", or "combined".
        - "depolarizing"  : equal probability of X, Y, Z error after each gate
        - "bit_flip"      : X error after each gate
        - "phase_flip"    : Z error after each gate
        - "combined"      : X, Z errors each at rate p/2 (independent)
    p : float
        Physical error rate in [0, 1].

    Returns
    -------
    NoiseModel
        Configured Qiskit NoiseModel ready for use with AerSimulator.

    Raises
    ------
    ValueError
        If `error_type` is not one of the four supported values, or if
        `p` is outside [0, 1].
    """
    if not 0.0 <= p <= 1.0:
        raise ValueError(f"Error rate p must be in [0, 1], got {p}")

    supported = {"depolarizing", "bit_flip", "phase_flip", "combined"}
    if error_type not in supported:
        raise ValueError(
            f"error_type must be one of {supported}, got '{error_type}'"
        )

    noise_model = NoiseModel()

    if p == 0.0:
        return noise_model

    gate_error = _build_gate_error(error_type, p)
    readout_error = _build_readout_error(p)

    # Apply gate error to all single-qubit gates
    single_qubit_gates = ["u1", "u2", "u3", "x", "y", "z", "h", "s", "sdg", "t", "tdg", "rx", "ry", "rz"]
    for gate in single_qubit_gates:
        noise_model.add_all_qubit_quantum_error(gate_error, gate)

    # Apply gate error to two-qubit gates (tensor product of single-qubit errors)
    two_qubit_error = gate_error.tensor(gate_error)
    two_qubit_gates = ["cx", "cz", "swap"]
    for gate in two_qubit_gates:
        noise_model.add_all_qubit_quantum_error(two_qubit_error, gate)

    # Apply readout error on measurement
    noise_model.add_all_qubit_readout_error(readout_error)

    return noise_model


def _build_gate_error(error_type: str, p: float):
    """Construct the per-gate quantum error channel."""
    if error_type == "depolarizing":
        return depolarizing_error(p, 1)

    if error_type == "bit_flip":
        # X error with probability p, identity with probability 1-p
        return pauli_error([("X", p), ("I", 1 - p)])

    if error_type == "phase_flip":
        # Z error with probability p, identity with probability 1-p
        return pauli_error([("Z", p), ("I", 1 - p)])

    if error_type == "combined":
        # Independent X and Z errors each at p/2
        # Results in: I w.p. (1-p/2)^2, X w.p. p/2*(1-p/2), Z w.p. p/2*(1-p/2), Y w.p. (p/2)^2
        px = p / 2
        pz = p / 2
        p_i = (1 - px) * (1 - pz)
        p_x = px * (1 - pz)
        p_z = (1 - px) * pz
        p_y = px * pz
        return pauli_error([("I", p_i), ("X", p_x), ("Z", p_z), ("Y", p_y)])


def _build_readout_error(p: float) -> ReadoutError:
    """
    Construct a symmetric readout (measurement) error matrix.

    The readout error matrix has the form:
        [[1-p, p],
         [p,   1-p]]
    meaning each bit is flipped with probability p during measurement.
    """
    probabilities = [[1 - p, p], [p, 1 - p]]
    return ReadoutError(probabilities)
