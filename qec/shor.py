"""Shor code: encode, syndrome measurement, and lookup-table decoder using Stim."""
import stim
import numpy as np
from typing import Optional, Tuple


def run_shor(p: float, error_type: str, shots: int = 1024) -> float:
    """Simulate the Shor code under noise and return the logical error rate."""
    circuit = stim.Circuit()

    # --- Encoding (noiseless) ---
    circuit.append("H", [0])
    circuit.append("CNOT", [0, 3])
    circuit.append("CNOT", [0, 6])
    circuit.append("H", [3])
    circuit.append("H", [6])
    circuit.append("CNOT", [0, 1])
    circuit.append("CNOT", [0, 2])
    circuit.append("CNOT", [3, 4])
    circuit.append("CNOT", [3, 5])
    circuit.append("CNOT", [6, 7])
    circuit.append("CNOT", [6, 8])

    # --- Noise applied ONLY to data qubits, ONLY after encoding ---
    if p > 0:
        if error_type == "bit_flip":
            circuit.append("X_ERROR", [0,1,2,3,4,5,6,7,8], p)
        elif error_type == "phase_flip":
            circuit.append("Z_ERROR", [0,1,2,3,4,5,6,7,8], p)
        elif error_type in ("depolarizing", "combined"):
            circuit.append("DEPOLARIZE1", [0,1,2,3,4,5,6,7,8], p)

    # --- Syndrome measurement (noiseless) ---
    circuit.append("CNOT", [0, 9])
    circuit.append("CNOT", [1, 9])
    circuit.append("CNOT", [1, 10])
    circuit.append("CNOT", [2, 10])
    circuit.append("CNOT", [3, 11])
    circuit.append("CNOT", [4, 11])
    circuit.append("CNOT", [4, 12])
    circuit.append("CNOT", [5, 12])
    circuit.append("CNOT", [6, 13])
    circuit.append("CNOT", [7, 13])
    circuit.append("CNOT", [7, 14])
    circuit.append("CNOT", [8, 14])
    circuit.append("M", [9, 10, 11, 12, 13, 14])

    # --- Decode circuit (noiseless) ---
    circuit.append("CNOT", [6, 8])
    circuit.append("CNOT", [6, 7])
    circuit.append("CNOT", [3, 5])
    circuit.append("CNOT", [3, 4])
    circuit.append("CNOT", [0, 2])
    circuit.append("CNOT", [0, 1])
    circuit.append("H", [6])
    circuit.append("H", [3])
    circuit.append("CNOT", [0, 6])
    circuit.append("CNOT", [0, 3])
    circuit.append("H", [0])

    # --- Measure logical qubit ---
    circuit.append("M", [0])

    sampler = circuit.compile_sampler()
    samples = sampler.sample(shots)

    # samples: (shots, 7) — cols 0-5 are syndrome, col 6 is logical
    logical_bits = samples[:, 6]
    return float(np.mean(logical_bits))


def encode_shor(qc, q) -> None:
    """Stub for Qiskit compatibility — encoding is handled inside run_shor via Stim."""
    qc.h(q[0])
    qc.cx(q[0], q[3])
    qc.cx(q[0], q[6])
    qc.h(q[3])
    qc.h(q[6])
    qc.cx(q[0], q[1])
    qc.cx(q[0], q[2])
    qc.cx(q[3], q[4])
    qc.cx(q[3], q[5])
    qc.cx(q[6], q[7])
    qc.cx(q[6], q[8])


def measure_syndrome_shor(qc, q, anc, creg) -> None:
    """Stub for Qiskit compatibility — syndrome measurement handled in run_shor via Stim."""
    qc.cx(q[0], anc[0]); qc.cx(q[1], anc[0])
    qc.cx(q[1], anc[1]); qc.cx(q[2], anc[1])
    qc.cx(q[3], anc[2]); qc.cx(q[4], anc[2])
    qc.cx(q[4], anc[3]); qc.cx(q[5], anc[3])
    qc.cx(q[6], anc[4]); qc.cx(q[7], anc[4])
    qc.cx(q[7], anc[5]); qc.cx(q[8], anc[5])
    qc.measure(anc[0], creg[0]); qc.measure(anc[1], creg[1])
    qc.measure(anc[2], creg[2]); qc.measure(anc[3], creg[3])
    qc.measure(anc[4], creg[4]); qc.measure(anc[5], creg[5])


def decode_shor(syndrome: list) -> Tuple[Optional[int], Optional[str]]:
    """Classical lookup table decoder for 6-bit Shor syndrome."""
    table = {
        (0,0,0,0,0,0): (None, None),
        (1,0,0,0,0,0): (0, 'X'),
        (1,1,0,0,0,0): (1, 'X'),
        (0,1,0,0,0,0): (2, 'X'),
        (0,0,1,0,0,0): (3, 'X'),
        (0,0,1,1,0,0): (4, 'X'),
        (0,0,0,1,0,0): (5, 'X'),
        (0,0,0,0,1,0): (6, 'X'),
        (0,0,0,0,1,1): (7, 'X'),
        (0,0,0,0,0,1): (8, 'X'),
    }
    return table.get(tuple(syndrome), (None, None))


def decode_circuit_shor(qc, q) -> None:
    """Stub for Qiskit compatibility — applies inverse encoding circuit."""
    qc.cx(q[6], q[8]); qc.cx(q[6], q[7])
    qc.cx(q[3], q[5]); qc.cx(q[3], q[4])
    qc.cx(q[0], q[2]); qc.cx(q[0], q[1])
    qc.h(q[6]); qc.h(q[3])
    qc.cx(q[0], q[6]); qc.cx(q[0], q[3])
    qc.h(q[0])
