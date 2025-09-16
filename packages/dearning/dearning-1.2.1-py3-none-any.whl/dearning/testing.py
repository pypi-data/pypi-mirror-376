# dearning/testing.py
import cmath, statistics
from dataclasses import dataclass, field, asdict
from math import log, exp, sqrt
from dearning.utils import evaluate_model

def test_model(model, X, y, formula=None, verbose=True):
    """
    Fungsi testing model AI dengan Alogekstest-Phymetrix (pure Python).
    Kombinasi: aljabar + logaritma + eksponensial +
               Phytagoras + geometri + matrix.
    """
    # --- Forward pass model ---
    preds = model.forward(X)  # list of float atau list of list
    # --- Transformasi log & eksponensial ---
    transformed = []
    for row in preds:
        if isinstance(row, (int, float)):  # kasus 1D
            val = log(row + 1) if row > 0 else row
            transformed.append([exp(val)])
        else:  # kasus 2D
            new_row = []
            for v in row:
                val = log(v + 1) if v > 0 else v
                new_row.append(exp(val))
            transformed.append(new_row)

    # --- Multi-dimensional Pythagoras ---
    py_values = [sqrt(sum(v ** 2 for v in row)) for row in transformed]

    # --- Normalisasi ke 0–1 ---
    max_val = max(py_values) if py_values else 1.0
    final_preds = [pv / (max_val + 1e-8) for pv in py_values]

    # --- Evaluasi model ---
    result = evaluate_model(model, X, y, task="classification")

    # --- Insight tambahan ---
    insight = {
        "mean_prediction": float(statistics.mean(final_preds)) if final_preds else 0.0,
        "max_prediction": float(max(final_preds)) if final_preds else 0.0,
        "min_prediction": float(min(final_preds)) if final_preds else 0.0,
    }
    result.update({
        "formula_used": formula or "aljabar+logaritma+eksponensial+phytagoras+geometri+matrix",
        "final_preds": final_preds,
        "insight": insight
    })

    if verbose:
        print("📊 Alogekstest-Phymetrix Evaluation:")
        print(f"Accuracy: {result.get('accuracy', 'N/A')}")
        print(f"Loss: {result.get('loss', 'N/A')}")
        print(f"Mean Prediction: {insight['mean_prediction']:.4f}")
    return result
