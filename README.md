# Quantum Error Correction

## Overview

This project simulates quantum error correction codes to measure logical error rates under various noise models. The Shor code (9-qubit) and surface code (d=3) are implemented using Stim for circuit simulation and PyMatching for decoding.

## Installation

```
pip install -e ".[dev]"
```

Requires Python 3.9+.

## Usage

```
jupyter notebook notebooks/01_shor_code.ipynb
jupyter notebook notebooks/02_surface_code.ipynb
jupyter notebook notebooks/03_benchmarking.ipynb
```

Run tests:

```
pytest tests/
```

## Results

Contained in each notebook

## Codes Implemented

- **Shor Code (9-qubit)**: Encodes one logical qubit into nine physical qubits and corrects arbitrary single-qubit errors using three-qubit repetition codes for both bit-flip and phase-flip protection.
- **Surface Code (d=3)**: A topological code that arranges nine data qubits on a 3×3 grid with four Z-stabilizer plaquettes, decoded via minimum-weight perfect matching to correct single X errors.

## References

- Nielsen, M. A. & Chuang, I. L. (2010). Quantum Computation and Quantum Information.
- Fowler, A. et al. (2012). Surface codes: Towards practical large-scale quantum computation. PRA 86, 032324.
