"""Benchmark utilities: sweep error rates and compare codes."""

import pandas as pd
import numpy as np
from qec.shor import run_shor
from qec.surface import run_surface


def sweep_error_rates(
    code: str,
    error_rates: list,
    error_type: str,
    shots: int = 1024,
    **kwargs,
) -> pd.DataFrame:
    """Sweeps error rates for one code and returns DataFrame with columns [p_physical, p_logical]."""
    if code not in ("shor", "surface"):
        raise ValueError(f"code must be 'shor' or 'surface', got '{code}'")

    rows = []
    for p in error_rates:
        if code == "shor":
            p_logical = run_shor(p, error_type, shots)
        else:
            p_logical = run_surface(p, error_type, shots=shots)
        rows.append({"p_physical": p, "p_logical": p_logical})

    return pd.DataFrame(rows, columns=["p_physical", "p_logical"])


def compare_codes(
    error_rates: list,
    error_type: str = "depolarizing",
    shots: int = 1024,
) -> pd.DataFrame:
    """Compares Shor, Surface, and unprotected qubit. Returns DataFrame with columns [p_physical, p_logical, code]."""
    df_shor = sweep_error_rates("shor", error_rates, error_type, shots)
    df_shor["code"] = "shor"

    df_surface = sweep_error_rates("surface", error_rates, error_type, shots)
    df_surface["code"] = "surface"

    df_unprotected = pd.DataFrame({
        "p_physical": error_rates,
        "p_logical": error_rates,
        "code": "unprotected",
    })

    return pd.concat([df_shor, df_surface, df_unprotected], ignore_index=True)
