"""Surface code: encode, syndrome measurement, and PyMatching decoder."""

from typing import List
import numpy as np
import pymatching
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator

from qec.noise import make_noise_model

# Z-stabilizer plaquettes: each entry is the list of data qubit indices
_Z_STABILIZERS: List[List[int]] = [
    [0, 1, 3, 4],  # Z0: top-left
    [1, 2, 4, 5],  # Z1: top-right
    [3, 4, 6, 7],  # Z2: bottom-left
    [4, 5, 7, 8],  # Z3: bottom-right
]

# X-stabilizer plaquettes: same geometry, different basis
_X_STABILIZERS: List[List[int]] = [
    [0, 1, 3, 4],  # X0
    [1, 2, 4, 5],  # X1
    [3, 4, 6, 7],  # X2
    [4, 5, 7, 8],  # X3
]


def build_surface_code(distance: int = 3) -> QuantumCircuit:
    """Builds a d=3 surface code circuit measuring only Z-stabilizers."""
    if distance != 3:
        raise ValueError(f"Only distance=3 is supported, got distance={distance}")

    q    = QuantumRegister(9, 'q')
    anc  = QuantumRegister(4, 'anc')   # 4 ancilla, one per Z-stabilizer only
    creg = ClassicalRegister(4, 'syndrome')
    qc   = QuantumCircuit(q, anc, creg)

    # Z-stabilizer measurements only: CNOT data -> ancilla, then measure
    # |0> is in the +1 eigenspace of Z-stabilizers so no spurious syndromes
    # X-stabilizers omitted: |0> is NOT in their +1 eigenspace, causes false syndromes
    for i, qubits in enumerate(_Z_STABILIZERS):
        for dq in qubits:
            qc.cx(q[dq], anc[i])
        qc.measure(anc[i], creg[i])

    return qc


def build_matching_graph() -> pymatching.Matching:
    """Builds PyMatching graph for the d=3 Z-stabilizer layout using edge API."""
    matching = pymatching.Matching()

    # 4 Z-stabilizer nodes (indices 0-3):
    # Z0=[0,1,3,4]  Z1=[1,2,4,5]
    # Z2=[3,4,6,7]  Z3=[4,5,7,8]

    # Internal edges — stabilizer pairs that share a data qubit
    matching.add_edge(0, 1, fault_ids={1}, weight=1)
    matching.add_edge(0, 2, fault_ids={3}, weight=1)
    matching.add_edge(1, 3, fault_ids={5}, weight=1)
    matching.add_edge(2, 3, fault_ids={7}, weight=1)

    # Boundary edges
    matching.add_boundary_edge(0, fault_ids={0}, weight=1)
    matching.add_boundary_edge(1, fault_ids={2}, weight=1)
    matching.add_boundary_edge(2, fault_ids={6}, weight=1)
    matching.add_boundary_edge(3, fault_ids={8}, weight=1)

    return matching


def decode_surface(syndrome: list, matching: pymatching.Matching) -> int:
    """Returns 1 if a logical error is detected, 0 otherwise."""
    import numpy as np
    z_syndrome = np.array(syndrome[0:4], dtype=np.uint8)
    correction = matching.decode(z_syndrome)  # returns array of fault_ids flipped
    # logical error if an odd number of top-row qubits (0,1,2) are corrected
    top_row = {0, 1, 2}
    flipped_top = sum(1 for q in correction if q in top_row)
    return int(flipped_top % 2)


def run_surface(p: float, error_type: str, distance: int = 3, shots: int = 1024) -> float:
    """Runs end-to-end surface code simulation and returns logical error rate."""
    qc = build_surface_code(distance)
    matching = build_matching_graph()

    noise_model = make_noise_model(error_type, p) if p > 0 else None
    simulator = AerSimulator(noise_model=noise_model) if noise_model else AerSimulator()
    tqc = transpile(qc, simulator)
    counts = simulator.run(tqc, shots=shots).result().get_counts()

    errors = 0
    for bitstring, count in counts.items():
        # Format: single group, no space, length 4
        # "syn[3]syn[2]syn[1]syn[0]" — syn[0] is rightmost character
        # syn[i] = bitstring[3-i]
        syndrome = [int(bitstring[3 - i]) for i in range(4)]
        z_syndrome = np.array(syndrome, dtype=np.uint8)
        logical_flip = decode_surface(syndrome, matching)
        if logical_flip == 1:
            errors += count

    return errors / shots
