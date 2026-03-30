"""Shor code: encode, syndrome measurement, and lookup-table decoder using Stim."""
import stim
import numpy as np
from typing import Optional, Tuple


def run_shor(p: float, error_type: str, shots: int = 1024) -> float:
    """Simulate Shor code using Stim TableauSimulator for correct mid-circuit
    classical feedforward. Returns logical error rate."""
    import random

    correction_table = {
        (1,0,0,0,0,0): 0,
        (1,1,0,0,0,0): 1,
        (0,1,0,0,0,0): 2,
        (0,0,1,0,0,0): 3,
        (0,0,1,1,0,0): 4,
        (0,0,0,1,0,0): 5,
        (0,0,0,0,1,0): 6,
        (0,0,0,0,1,1): 7,
        (0,0,0,0,0,1): 8,
    }

    errors = 0
    for _ in range(shots):
        sim = stim.TableauSimulator()

        # --- Encode ---
        sim.h(0)
        sim.cnot(0, 3); sim.cnot(0, 6)
        sim.h(3); sim.h(6)
        sim.cnot(0, 1); sim.cnot(0, 2)
        sim.cnot(3, 4); sim.cnot(3, 5)
        sim.cnot(6, 7); sim.cnot(6, 8)

        # --- Noise: apply errors independently per qubit ---
        if p > 0:
            for q in range(9):
                if error_type == "bit_flip":
                    if random.random() < p:
                        sim.x(q)
                elif error_type == "phase_flip":
                    if random.random() < p:
                        sim.z(q)
                elif error_type in ("depolarizing", "combined"):
                    r = random.random()
                    if r < p / 3:
                        sim.x(q)
                    elif r < 2 * p / 3:
                        sim.z(q)
                    elif r < p:
                        sim.y(q)

        # --- Syndrome measurement ---
        sim.cnot(0, 9);  sim.cnot(1, 9)
        sim.cnot(1, 10); sim.cnot(2, 10)
        sim.cnot(3, 11); sim.cnot(4, 11)
        sim.cnot(4, 12); sim.cnot(5, 12)
        sim.cnot(6, 13); sim.cnot(7, 13)
        sim.cnot(7, 14); sim.cnot(8, 14)

        s0 = sim.measure(9)
        s1 = sim.measure(10)
        s2 = sim.measure(11)
        s3 = sim.measure(12)
        s4 = sim.measure(13)
        s5 = sim.measure(14)
        syndrome = (int(s0), int(s1), int(s2), int(s3), int(s4), int(s5))

        # --- Classical correction ---
        qubit_to_fix = correction_table.get(syndrome, None)
        if qubit_to_fix is not None:
            sim.x(qubit_to_fix)

        # --- Decode ---
        sim.cnot(6, 8); sim.cnot(6, 7)
        sim.cnot(3, 5); sim.cnot(3, 4)
        sim.cnot(0, 2); sim.cnot(0, 1)
        sim.h(6); sim.h(3)
        sim.cnot(0, 6); sim.cnot(0, 3)
        sim.h(0)

        # --- Measure logical qubit ---
        logical = int(sim.measure(0))
        if logical == 1:
            errors += 1

    return errors / shots


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
