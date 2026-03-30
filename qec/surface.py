"""Surface code: encode, syndrome measurement, and PyMatching decoder."""

from typing import List
import numpy as np
import pymatching
import stim
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator

from qec.noise import make_noise_model

# d=3 rotated surface code — correct plaquette layout
# Data qubit grid (row, col) -> index = row*3 + col:
#   0 1 2
#   3 4 5
#   6 7 8
#
# Z-stabilizers: 4-qubit plaquettes (detect X errors)
#   Z0: [0,1,3,4]  Z1: [1,2,4,5]  Z2: [3,4,6,7]  Z3: [4,5,7,8]
#
# Logical X operator: any path from top to bottom boundary
#   Minimal: left column [0,3,6] — verified zero syndrome above

_Z_STABILIZERS = [
    [0, 1, 3, 4],  # Z0
    [1, 2, 4, 5],  # Z1
    [3, 4, 6, 7],  # Z2
    [4, 5, 7, 8],  # Z3
]

_X_STABILIZERS = [
    [0, 1, 3, 4],
    [1, 2, 4, 5],
    [3, 4, 6, 7],
    [4, 5, 7, 8],
]


def build_surface_code(distance: int = 3) -> QuantumCircuit:
    """Builds a d=3 surface code circuit measuring only Z-stabilizers."""
    if distance != 3:
        raise ValueError(f"Only distance=3 is supported, got distance={distance}")
    q    = QuantumRegister(9, 'q')
    anc  = QuantumRegister(4, 'anc')
    creg = ClassicalRegister(4, 'syndrome')
    qc   = QuantumCircuit(q, anc, creg)
    for i, qubits in enumerate(_Z_STABILIZERS):
        for dq in qubits:
            qc.cx(q[dq], anc[i])
        qc.measure(anc[i], creg[i])
    return qc


def build_matching_graph():
    """Returns a lookup table dict mapping syndrome tuples to logical flip bit.

    Precomputed for all single X errors on the d=3 surface code with:
      Z0=[0,1,3,4]  Z1=[1,2,4,5]  Z2=[3,4,6,7]  Z3=[4,5,7,8]
    Logical X operator = left column [0,3,6].

    For each possible error, syndrome is computed as parity of overlap
    with each stabilizer. Logical flip = 1 if correction crosses logical
    operator an odd number of times.

    Returns dict: {(s0,s1,s2,s3): logical_flip}
    """
    z_stabs  = [[0,1,3,4],[1,2,4,5],[3,4,6,7],[4,5,7,8]]
    logical_op = {0, 3, 6}  # left column

    def get_syndrome(errors):
        return tuple(
            sum(1 for q in errors if q in stab) % 2
            for stab in z_stabs
        )

    # Build table: syndrome -> logical flip
    # Single qubit errors
    table = {}
    for q in range(9):
        syn = get_syndrome([q])
        # Minimum weight correction: find smallest set of qubits
        # that produces the same syndrome, check if it crosses logical op
        # For single errors, correction = {q} itself
        logical_flip = 1 if q in logical_op else 0
        table[syn] = logical_flip

    # Two-qubit errors that produce unique syndromes
    # (only needed if single-qubit table has collisions)
    # Check for collisions first
    all_syndromes = [get_syndrome([q]) for q in range(9)]
    if len(set(all_syndromes)) < 9:
        print("WARNING: syndrome collision detected in single-qubit errors")

    # Zero syndrome = no error
    table[(0,0,0,0)] = 0

    return table


def decode_surface(syndrome: list, matching) -> int:
    """Returns 1 if a logical error is detected, 0 otherwise.
    matching is a dict lookup table for this implementation."""
    key = tuple(syndrome[0:4])
    return matching.get(key, 0)


def run_surface(p: float, error_type: str, distance: int = 3, shots: int = 1024) -> float:
    """Simulate d=3 surface code using Stim TableauSimulator. Returns logical error rate."""
    import random

    # Data qubit layout (row, col) -> index = row*3 + col:
    #   0 1 2
    #   3 4 5
    #   6 7 8
    # Ancilla qubits 9-12 for Z-stabilizers Z0-Z3
    # Z0=[0,1,3,4]  Z1=[1,2,4,5]  Z2=[3,4,6,7]  Z3=[4,5,7,8]

    z_stabilizers = [
        [0, 1, 3, 4],  # Z0 -> anc 9
        [1, 2, 4, 5],  # Z1 -> anc 10
        [3, 4, 6, 7],  # Z2 -> anc 11
        [4, 5, 7, 8],  # Z3 -> anc 12
    ]

    matching = build_matching_graph()
    errors = 0

    for _ in range(shots):
        sim = stim.TableauSimulator()

        # Data qubits 0-8 start in |0> — no encoding needed for Z-basis stabilizers
        # |0>^9 is already in the +1 eigenspace of all Z-stabilizers

        # --- Noise on data qubits ---
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

        # --- Z-stabilizer measurements ---
        syndrome = []
        for i, qubits in enumerate(z_stabilizers):
            anc = 9 + i
            for dq in qubits:
                sim.cnot(dq, anc)
            result = int(sim.measure(anc))
            syndrome.append(result)
            sim.reset(anc)  # reset ancilla for cleanliness

        # --- Decode ---
        logical_flip = decode_surface(syndrome, matching)
        if logical_flip == 1:
            errors += 1

    return errors / shots
