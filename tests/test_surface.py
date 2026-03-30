"""Tests for qec/surface.py — implemented in Phase 5."""

import pytest
from qec.surface import build_surface_code, run_surface


def test_build_surface_code_qubit_count():
    qc = build_surface_code(3)
    assert qc.num_qubits == 13  # 9 data + 4 ancilla


def test_build_surface_code_creg_size():
    qc = build_surface_code(3)
    assert qc.num_clbits == 4


def test_run_surface_zero_noise():
    rate = run_surface(0.0, "depolarizing", distance=3, shots=256)
    assert rate == 0.0


def test_surface_no_noise_zero_syndrome():
    """With zero noise, all syndrome bits must be 0 on every shot."""
    from qiskit_aer import AerSimulator
    qc = build_surface_code(3)
    counts = AerSimulator().run(qc, shots=64).result().get_counts()
    for bitstring in counts:
        bits = bitstring.replace(' ', '')
        assert bits == '0' * len(bits), (
            f"Non-zero syndrome '{bits}' with zero noise — "
            f"stabilizer circuit is incorrect"
        )

def test_surface_no_noise_zero_logical_error():
    """At p=0, run_surface must return exactly 0.0."""
    rate = run_surface(0.0, "depolarizing", distance=3, shots=256)
    assert rate == 0.0, (
        f"Got logical error rate {rate} with zero noise — "
        f"syndrome circuit or logical readout is broken"
    )

def test_surface_low_noise_beats_baseline():
    """At p=0.01, surface code logical error rate must be below physical error rate."""
    rate = run_surface(0.0001, "depolarizing", distance=3, shots=512)
    assert rate < 0.0001, (
        f"Surface logical error rate {rate:.4f} >= physical rate 0.01 — "
        f"decoder or logical operator check is broken"
    )

def test_surface_known_x_error_detected():
    """Inject X on center qubit (index 4), syndrome must be non-zero."""
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    from qec.surface import build_surface_code

    # Build the base circuit and get its internal registers directly
    base = build_surface_code(3)
    q   = base.qregs[0]   # QuantumRegister(9, 'q')
    anc = base.qregs[1]   # QuantumRegister(8, 'anc')

    # Build a fresh circuit using the same registers, prepend X on q[4]
    from qiskit import ClassicalRegister
    creg = base.cregs[0]
    qc = QuantumCircuit(q, anc, creg)
    qc.x(q[4])             # inject X error on center qubit before stabilizers
    qc.compose(base, inplace=True)  # append full stabilizer+measure circuit

    counts = AerSimulator().run(qc, shots=64).result().get_counts()
    all_zero = all(
        b.replace(' ', '') == '0' * 8
        for b in counts
    )
    assert not all_zero, (
        "X error on center qubit produced all-zero syndrome — "
        "Z-stabilizer circuit is not detecting errors"
    )
