import math, statistics, itertools, concurrent.futures
import logging, io ,json ,csv, threading, hashlib
from collections import defaultdict, OrderedDict
from functools import wraps
from itertools import starmap

logging.basicConfig(level=logging.INFO)

def cached(_func=None, *, maxsize=128, threshold=64):
    """
    Decorator cached untuk optimasi
    """
    def make_hashable(obj):
        if isinstance(obj, (int, float, str, bytes, tuple, frozenset, type(None))):
            return obj
        if isinstance(obj, list):
            if len(obj) > threshold:
                return ("list", id(obj), len(obj))
            return tuple(map(make_hashable, obj))
        if isinstance(obj, set):
            if len(obj) > threshold:
                return ("set", id(obj), len(obj))
            return frozenset(map(make_hashable, obj))
        if isinstance(obj, dict):
            if len(obj) > threshold:
                return ("dict", id(obj), len(obj))
            return tuple(sorted(starmap(lambda k, v: (k, make_hashable(v)), obj.items())))
        try:
            return hashlib.md5(repr(obj).encode()).hexdigest()
        except Exception:
            return str(id(obj))

    def decorator(func):
        cache = OrderedDict()
        lock = threading.RLock()
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (
                tuple(map(make_hashable, args)),
                tuple(starmap(lambda k, v: (k, make_hashable(v)), sorted(kwargs.items())))
            )
            with lock:
                if key in cache:
                    cache.move_to_end(key)
                    return cache[key]

            result = func(*args, **kwargs)
            with lock:
                cache[key] = result
                if len(cache) > maxsize:
                    cache.popitem(last=False)
            return result
        return wrapper

    # support @cached dan @cached(...)
    if _func is None:
        return decorator
    else:
        return decorator(_func)
    
# === 🔧 Scaling (ganti StandardScaler) ===
def scale_data(data):
    """Manual StandardScaler pakai pure Python"""
    n = len(data)
    m = len(data[0])
    means = [sum(row[j] for row in data) / n for j in range(m)]
    stdevs = [
        math.sqrt(sum((row[j] - means[j]) ** 2 for row in data) / n)
        for j in range(m)
    ]
    scaled = [
        [(row[j] - means[j]) / (stdevs[j] if stdevs[j] != 0 else 1) for j in range(m)]
        for row in data
    ]
    return scaled

# === 🔧 Preprocessing Otomatis ===
def preprocess_data(data, n_jobs=-1, optimizer_args=None):
    # --- Konversi ke list of list jika input masih list of scalars ---
    if isinstance(data[0], (int, float)):
        data = [[x] for x in data]
    n_samples = len(data)
    n_features = len(data[0]) if data else 0

    # === Standard Scaler manual (setara fit_transform sklearn) ===
    def scale_batch(batch):
        cols = list(zip(*batch))
        means = [statistics.mean(col) for col in cols]
        stdevs = [statistics.pstdev(col) if statistics.pstdev(col) > 0 else 1.0 for col in cols]
        scaled = [[(x - m) / s for x, m, s in zip(row, means, stdevs)] for row in batch]
        return scaled
    if n_samples > 1000:
        batch_size = 200
        batches = [data[i:i + batch_size] for i in range(0, n_samples, batch_size)]
        # parallel pakai concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=None if n_jobs == -1 else n_jobs) as executor:
            scaled_batches = list(executor.map(scale_batch, batches))
        data_scaled = list(itertools.chain.from_iterable(scaled_batches))
    else:
        data_scaled = scale_batch(data)

    # === Optimizer manual ===
    if optimizer_args is not None:
        w, b, grad_w, grad_b, layer_idx = optimizer_args[:5]
        method = optimizer_args[5] if len(optimizer_args) > 5 else "sgd"
        learning_rate = optimizer_args[6] if len(optimizer_args) > 6 else 0.01
        beta1 = optimizer_args[7] if len(optimizer_args) > 7 else 0.9
        beta2 = optimizer_args[8] if len(optimizer_args) > 8 else 0.999
        epsilon = optimizer_args[9] if len(optimizer_args) > 9 else 1e-8
        state = optimizer_args[10] if len(optimizer_args) > 10 else defaultdict(dict)
        method = method.lower()
        if method == "sgd":
            w_new = [[wij - learning_rate * gwij for wij, gwij in zip(wrow, grow)] for wrow, grow in zip(w, grad_w)]
            b_new = [bj - learning_rate * gbj for bj, gbj in zip(b, grad_b)]

        elif method == "momentum":
            m_w, m_b = state["m_w"], state["m_b"]
            if layer_idx not in m_w:
                m_w[layer_idx] = [[0.0] * len(row) for row in grad_w]
                m_b[layer_idx] = [0.0] * len(grad_b)
            m_w[layer_idx] = [[beta1 * mwij + (1 - beta1) * gwij for mwij, gwij in zip(mrow, grow)]
                              for mrow, grow in zip(m_w[layer_idx], grad_w)]
            m_b[layer_idx] = [beta1 * mbj + (1 - beta1) * gbj for mbj, gbj in zip(m_b[layer_idx], grad_b)]
            w_new = [[wij - learning_rate * mwij for wij, mwij in zip(wrow, mrow)] for wrow, mrow in zip(w, m_w[layer_idx])]
            b_new = [bj - learning_rate * mbj for bj, mbj in zip(b, m_b[layer_idx])]
            state["m_w"], state["m_b"] = m_w, m_b

        elif method == "rmsprop":
            v_w, v_b = state["v_w"], state["v_b"]
            if layer_idx not in v_w:
                v_w[layer_idx] = [[0.0] * len(row) for row in grad_w]
                v_b[layer_idx] = [0.0] * len(grad_b)
            v_w[layer_idx] = [[beta2 * vwij + (1 - beta2) * (gwij ** 2) for vwij, gwij in zip(vrow, grow)]
                              for vrow, grow in zip(v_w[layer_idx], grad_w)]
            v_b[layer_idx] = [beta2 * vbj + (1 - beta2) * (gbj ** 2) for vbj, gbj in zip(v_b[layer_idx], grad_b)]
            w_new = [[wij - learning_rate * gwij / (math.sqrt(vwij) + epsilon)
                      for wij, gwij, vwij in zip(wrow, grow, vrow)]
                     for wrow, grow, vrow in zip(w, grad_w, v_w[layer_idx])]
            b_new = [bj - learning_rate * gbj / (math.sqrt(vbj) + epsilon)
                     for bj, gbj, vbj in zip(b, grad_b, v_b[layer_idx])]
            state["v_w"], state["v_b"] = v_w, v_b

        elif method == "adam":
            m_w, v_w, m_b, v_b = state["m_w"], state["v_w"], state["m_b"], state["v_b"]
            t = state.get("t", 1)
            if layer_idx not in m_w:
                m_w[layer_idx] = [[0.0] * len(row) for row in grad_w]
                v_w[layer_idx] = [[0.0] * len(row) for row in grad_w]
                m_b[layer_idx] = [0.0] * len(grad_b)
                v_b[layer_idx] = [0.0] * len(grad_b)
            m_w[layer_idx] = [[beta1 * mwij + (1 - beta1) * gwij for mwij, gwij in zip(mrow, grow)]
                              for mrow, grow in zip(m_w[layer_idx], grad_w)]
            v_w[layer_idx] = [[beta2 * vwij + (1 - beta2) * (gwij ** 2) for vwij, gwij in zip(vrow, grow)]
                              for vrow, grow in zip(v_w[layer_idx], grad_w)]
            m_b[layer_idx] = [beta1 * mbj + (1 - beta1) * gbj for mbj, gbj in zip(m_b[layer_idx], grad_b)]
            v_b[layer_idx] = [beta2 * vbj + (1 - beta2) * (gbj ** 2) for vbj, gbj in zip(v_b[layer_idx], grad_b)]
            m_w_hat = [[mwij / (1 - beta1 ** t) for mwij in mrow] for mrow in m_w[layer_idx]]
            v_w_hat = [[vwij / (1 - beta2 ** t) for vwij in vrow] for vrow in v_w[layer_idx]]
            m_b_hat = [mbj / (1 - beta1 ** t) for mbj in m_b[layer_idx]]
            v_b_hat = [vbj / (1 - beta2 ** t) for vbj in v_b[layer_idx]]
            t += 1
            state.update({"m_w": m_w, "v_w": v_w, "m_b": m_b, "v_b": v_b, "t": t})
            w_new = [[wij - learning_rate * mwij / (math.sqrt(vwij) + epsilon)
                      for wij, mwij, vwij in zip(wrow, mrow, vrow)]
                     for wrow, mrow, vrow in zip(w, m_w_hat, v_w_hat)]
            b_new = [bj - learning_rate * mbj / (math.sqrt(vbj) + epsilon)
                     for bj, mbj, vbj in zip(b, m_b_hat, v_b_hat)]
        else:
            raise ValueError(f"Optimizer '{method}' tidak dikenali.")

        return data_scaled, (w_new, b_new, state)
    return data_scaled

def evaluate_model(model, data, labels=None, task=None, threshold=0.5, optimizer_args=None):
    # --- Forward pass model ---
    y_pred = model.forward(data)

    # --- Optimizer logic ---
    optimizer_result = None
    if optimizer_args is not None:
        w, b, grad_w, grad_b, layer_idx = optimizer_args[:5]
        method = optimizer_args[5] if len(optimizer_args) > 5 else "sgd"
        learning_rate = optimizer_args[6] if len(optimizer_args) > 6 else 0.01
        beta1 = optimizer_args[7] if len(optimizer_args) > 7 else 0.9
        beta2 = optimizer_args[8] if len(optimizer_args) > 8 else 0.999
        epsilon = optimizer_args[9] if len(optimizer_args) > 9 else 1e-8
        state = optimizer_args[10] if len(optimizer_args) > 10 else defaultdict(dict)
        method = method.lower()

        # pastikan semua berbentuk list
        if not isinstance(grad_w[0], list):
            grad_w = [grad_w]
            w = [w]

        if method == "sgd":
            w_new = [[wij - learning_rate * gwij for wij, gwij in zip(wrow, grow)]
                     for wrow, grow in zip(w, grad_w)]
            b_new = [bj - learning_rate * gbj for bj, gbj in zip(b, grad_b)]
        elif method == "momentum":
            m_w = state.get("m_w", {})
            m_b = state.get("m_b", {})
            if layer_idx not in m_w:
                m_w[layer_idx] = [[0.0 for _ in grow] for grow in grad_w]
                m_b[layer_idx] = [0.0 for _ in grad_b]
            m_w[layer_idx] = [[beta1 * mw + (1 - beta1) * gw for mw, gw in zip(mrow, grow)]
                               for mrow, grow in zip(m_w[layer_idx], grad_w)]
            m_b[layer_idx] = [beta1 * mb + (1 - beta1) * gb for mb, gb in zip(m_b[layer_idx], grad_b)]
            w_new = [[wij - learning_rate * mw for wij, mw in zip(wrow, mrow)]
                     for wrow, mrow in zip(w, m_w[layer_idx])]
            b_new = [bj - learning_rate * mb for bj, mb in zip(b, m_b[layer_idx])]
            state["m_w"], state["m_b"] = m_w, m_b
        elif method == "rmsprop":
            v_w = state.get("v_w", {})
            v_b = state.get("v_b", {})
            if layer_idx not in v_w:
                v_w[layer_idx] = [[0.0 for _ in grow] for grow in grad_w]
                v_b[layer_idx] = [0.0 for _ in grad_b]
            v_w[layer_idx] = [[beta2 * vw + (1 - beta2) * (gw ** 2) for vw, gw in zip(vrow, grow)]
                               for vrow, grow in zip(v_w[layer_idx], grad_w)]
            v_b[layer_idx] = [beta2 * vb + (1 - beta2) * (gb ** 2) for vb, gb in zip(v_b[layer_idx], grad_b)]
            w_new = [[wij - learning_rate * gw / (math.sqrt(vw) + epsilon)
                      for wij, gw, vw in zip(wrow, grow, vrow)]
                     for wrow, grow, vrow in zip(w, grad_w, v_w[layer_idx])]
            b_new = [bj - learning_rate * gb / (math.sqrt(vb) + epsilon)
                     for bj, gb, vb in zip(b, grad_b, v_b[layer_idx])]
            state["v_w"], state["v_b"] = v_w, v_b
        elif method == "adam":
            m_w = state.get("m_w", {})
            v_w = state.get("v_w", {})
            m_b = state.get("m_b", {})
            v_b = state.get("v_b", {})
            t = state.get("t", 1)
            if layer_idx not in m_w:
                m_w[layer_idx] = [[0.0 for _ in grow] for grow in grad_w]
                v_w[layer_idx] = [[0.0 for _ in grow] for grow in grad_w]
                m_b[layer_idx] = [0.0 for _ in grad_b]
                v_b[layer_idx] = [0.0 for _ in grad_b]
            m_w[layer_idx] = [[beta1 * mw + (1 - beta1) * gw for mw, gw in zip(mrow, grow)]
                               for mrow, grow in zip(m_w[layer_idx], grad_w)]
            v_w[layer_idx] = [[beta2 * vw + (1 - beta2) * (gw ** 2) for vw, gw in zip(vrow, grow)]
                               for vrow, grow in zip(v_w[layer_idx], grad_w)]
            m_b[layer_idx] = [beta1 * mb + (1 - beta1) * gb for mb, gb in zip(m_b[layer_idx], grad_b)]
            v_b[layer_idx] = [beta2 * vb + (1 - beta2) * (gb ** 2) for vb, gb in zip(v_b[layer_idx], grad_b)]
            m_w_hat = [[mw / (1 - beta1 ** t) for mw in mrow] for mrow in m_w[layer_idx]]
            v_w_hat = [[vw / (1 - beta2 ** t) for vw in vrow] for vrow in v_w[layer_idx]]
            m_b_hat = [mb / (1 - beta1 ** t) for mb in m_b[layer_idx]]
            v_b_hat = [vb / (1 - beta2 ** t) for vb in v_b[layer_idx]]
            w_new = [[wij - learning_rate * mw / (math.sqrt(vw) + epsilon)
                      for wij, mw, vw in zip(wrow, mrow, vrow)]
                     for wrow, mrow, vrow in zip(w, m_w_hat, v_w_hat)]
            b_new = [bj - learning_rate * mb / (math.sqrt(vb) + epsilon)
                     for bj, mb, vb in zip(b, m_b_hat, v_b_hat)]
            state.update({"m_w": m_w, "v_w": v_w, "m_b": m_b, "v_b": v_b, "t": t + 1})
        else:
            raise ValueError(f"Optimizer '{method}' tidak dikenali.")
        optimizer_result = (w_new, b_new, state)

    # --- Task detection ---
    if labels is not None and task is None:
        unique = set(labels)
        task = "classification" if unique <= {0, 1} else "regression"
        logging.info(f"[Auto Task Detection] Deteksi tugas: {task}")

    # --- Metrics ---
    result = {}
    if labels is None:
        result = {"output_mean": float(sum(y_pred) / len(y_pred))}
    elif task == "regression":
        mse = sum((yp - yt) ** 2 for yp, yt in zip(y_pred, labels)) / len(labels)
        mean_y = sum(labels) / len(labels)
        ss_tot = sum((yt - mean_y) ** 2 for yt in labels)
        ss_res = sum((yp - yt) ** 2 for yp, yt in zip(y_pred, labels))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        mean_err = sum(abs(yp - yt) for yp, yt in zip(y_pred, labels)) / len(labels)
        result.update({"mse": mse, "r2": r2, "mean_error": mean_err})
    elif task == "classification":
        y_class = [1 if yp > threshold else 0 for yp in y_pred]
        tp = sum(1 for yc, yt in zip(y_class, labels) if yc == yt == 1)
        tn = sum(1 for yc, yt in zip(y_class, labels) if yc == yt == 0)
        fp = sum(1 for yc, yt in zip(y_class, labels) if yc == 1 and yt == 0)
        fn = sum(1 for yc, yt in zip(y_class, labels) if yc == 0 and yt == 1)
        accuracy = (tp + tn) / len(labels)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        cm = [[tn, fp], [fn, tp]]
        report = {
            "0": {"precision": tn / (tn + fn) if (tn + fn) else 0.0,
                  "recall": tn / (tn + fp) if (tn + fp) else 0.0},
            "1": {"precision": precision, "recall": recall}
        }
        result.update({"accuracy": accuracy, "precision": precision, "recall": recall,
                       "f1_score": f1, "confusion_matrix": cm, "report": report})
    else:
        raise ValueError("task harus 'regression' atau 'classification'")
    return (result, optimizer_result) if optimizer_result is not None else result

class Adapter:
    # --- Format dasar ---
    @staticmethod
    def json(data):
        import json
        if isinstance(data, str):
            return json.loads(data)
        return json.dumps(data)

    @staticmethod
    def csv(data):
        import io, csv
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        if isinstance(data, list):
            for row in data:
                writer.writerow(row)
        return buffer.getvalue()

    # --- Numerical ---
    @staticmethod
    def numpy(data):
        try:
            import numpy as np
            return np.array(data)
        except ImportError:
            return data

    @staticmethod
    def scipyspar(data):
        try:
            from scipy import sparse
            return sparse.csr_matrix(data)
        except ImportError:
            return data

    # --- Data Processing ---
    @staticmethod
    def pandas(data):
        try:
            import pandas as pd
            return pd.DataFrame(data)
        except ImportError:
            return data

    @staticmethod
    def polars(data):
        try:
            import polars as pl
            return pl.DataFrame(data)
        except ImportError:
            return data

    @staticmethod
    def pyarrow(data):
        try:
            import pyarrow as pa
            return pa.array(data)
        except ImportError:
            return data

    # --- Audio ---
    @staticmethod
    def librosa(path):
        try:
            import librosa
            return librosa.load(path)
        except ImportError:
            return None

    # --- Vision ---
    @staticmethod
    def pillow(data):
        try:
            from PIL import Image
            return Image.open(data) if isinstance(data, str) else Image.fromarray(data)
        except ImportError:
            return data
