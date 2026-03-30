"""Tests for qec/shor.py — implemented in Phase 5."""

import pytest
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator

from qec.shor import encode_shor, measure_syndrome_shor, decode_shor, run_shor


def test_encode_shor_qubit_count():
    q = QuantumRegister(9, 'q')
    qc = QuantumCircuit(q)
    encode_shor(qc, q)
    assert qc.num_qubits == 9


def test_syndrome_no_error():
    q = QuantumRegister(9, 'q')
    anc = QuantumRegister(6, 'anc')
    c = ClassicalRegister(6, 'c')
    qc = QuantumCircuit(q, anc, c)

    encode_shor(qc, q)
    measure_syndrome_shor(qc, q, anc, c)

    simulator = AerSimulator()
    tqc = transpile(qc, simulator)
    counts = simulator.run(tqc, shots=256).result().get_counts()

    most_common = max(counts, key=counts.get)
    assert most_common.replace(' ', '') == '000000'


def test_syndrome_detects_x_error():
    q = QuantumRegister(9, 'q')
    anc = QuantumRegister(6, 'anc')
    c = ClassicalRegister(6, 'c')
    qc = QuantumCircuit(q, anc, c)

    encode_shor(qc, q)
    qc.x(q[0])
    measure_syndrome_shor(qc, q, anc, c)

    simulator = AerSimulator()
    tqc = transpile(qc, simulator)
    counts = simulator.run(tqc, shots=256).result().get_counts()

    most_common = max(counts, key=counts.get)
    assert most_common.replace(' ', '') != '000000'


def test_decode_no_error():
    result = decode_shor([0, 0, 0, 0, 0, 0])
    assert result == (None, None)


def test_encode_q0_is_superposition():
    """q[0] alone should be 50/50 after encoding — do NOT use it as logical readout."""
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit_aer import AerSimulator
    q = QuantumRegister(9, 'q')
    log = ClassicalRegister(1, 'log')
    qc = QuantumCircuit(q, log)
    encode_shor(qc, q)
    qc.measure(q[0], log[0])
    counts = AerSimulator().run(qc, shots=512).result().get_counts()
    p0 = counts.get('0', 0) / 512
    # q[0] should be in superposition — neither 0 nor 1 with certainty
    # This test DOCUMENTS the failure mode: do not use q[0] as logical readout
    assert 0.3 < p0 < 0.7, (
        f"q[0] measured {p0:.2f} — confirms q[0] alone is not a valid logical readout"
    )

def test_encode_all9_valid_codewords():
    """All 9-qubit measurement outcomes must be valid Shor |0> codewords."""
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit_aer import AerSimulator
    q = QuantumRegister(9, 'q')
    c = ClassicalRegister(9, 'c')
    qc = QuantumCircuit(q, c)
    encode_shor(qc, q)
    qc.measure(q, c)
    counts = AerSimulator().run(qc, shots=256).result().get_counts()
    # Valid Shor |0> codewords: each block must be all-0 or all-1
    valid = {'000000000', '111000000', '000111000', '000000111',
             '111111000', '111000111', '000111111', '111111111'}
    for bitstring in counts:
        assert bitstring in valid, (
            f"Invalid codeword '{bitstring}' — encoding is incorrect"
        )

def test_run_shor_low_noise_beats_baseline():
    """Shor code logical error rate must be below physical rate at p=0.005.
    Using p=0.005 instead of p=0.01 gives clear margin above statistical
    noise at shots=1024. The Shor code comfortably corrects single-qubit
    bit-flip errors well below this rate."""
    from qec.shor import run_shor
    rate = run_shor(0.005, "bit_flip", shots=1024)
    assert rate < 0.005, (
        f"Shor logical error rate {rate:.4f} >= physical rate 0.005 — "
        f"correction is not working"
    )

def test_run_shor_zero_noise():
    """At p=0, logical error rate must be exactly 0."""
    rate = run_shor(0.0, "depolarizing", shots=256)
    assert rate == 0.0, f"Got {rate} with zero noise — encoding or readout is broken"
