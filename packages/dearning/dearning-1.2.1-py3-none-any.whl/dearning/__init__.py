# dearning/__init__.py
import importlib, builtins

# === 🛡️ Protection ===
builtins.__dafe_protect__ = True

class _LazyLoader:
    def __init__(self, module_name, exports):
        self._module_name = module_name
        self._exports = exports
        self._module = None
    def _load(self):
        if self._module is None:
            self._module = importlib.import_module(self._module_name)
        return self._module
    def __getattr__(self, attr):
        if attr in self._exports:
            return getattr(self._load(), attr)
        raise AttributeError(f"'{self._module_name}' has no attribute '{attr}'")

# === 📦 Register Lazy Modules ===
_model = _LazyLoader("dearning.model", [
    "CustomAIModel", "Dense", "Activation", "Dropout", "DOtensor"
])

_utils = _LazyLoader("dearning.utils", [
    "preprocess_data", "evaluate_model", "Adapter", "cached"
])

_training = _LazyLoader("dearning.training", [
    "LogEkstrainnix"
])

_AI_tools = _LazyLoader("dearning.AI_tools", [
    "DLP", "AImemory", "TTS", "RLTools", "Qkanalyze", "video", "audio", "image", "video"
])

_AI_core = _LazyLoader("dearning.AI_core", [
    "CodeTracker", "BinaryConverter", "ByteConverter"
])

_multymodel = _LazyLoader("dearning.multymodel", [
    "AImodel"
])

_quantum = _LazyLoader("dearning.Quantum", [
    "Quantum", "Quan"
])

_testing = _LazyLoader("dearning.testing", [
    "test_model"
])
_DOOM = _LazyLoader("Memory.DOMM", [
    "DOMM"
])

# === 🌐 Public API Expose ===
CustomAIModel = _model.CustomAIModel
Dense = _model.Dense
Activation = _model.Activation
Dropout = _model.Dropout
DOtensor = _model.DOtensor

cached = _utils.cached
preprocess_data = _utils.preprocess_data
evaluate_model = _utils.evaluate_model
Adapter = _utils.Adapter

LogEkstrainnix = _training.LogEkstrainnix

DLP = _AI_tools.DLP
AImemory = _AI_tools.AImemory
TTS = _AI_tools.TTS
RLTools = _AI_tools.RLTools
audio = _AI_tools.audio
image = _AI_tools.image
video = _AI_tools.video
Qkanalyze = _AI_tools.Qkanalyze

CodeTracker = _AI_core.CodeTracker
BinaryConverter = _AI_core.BinaryConverter
ByteConverter = _AI_core.ByteConverter

AImodel = _multymodel.AImodel

Quantum = _quantum.Quantum
Quan = _quantum.Quan

test_model = _testing.test_model

DOMM = _DOOM.DOMM

__all__ = [
    "CustomAIModel", "Dense", "Activation", "Dropout", "DOtensor", "cached",
    "Adapter", "DOMM",
    "DLP", "AImemory", "TTS", "RLTools", "audio", "image", "video", "Qkanalyze",
    "CodeTracker", "BinaryConverter", "ByteConverter", "AImodel", "Quantum",
    "Quan", "preprocess_data", "evaluate_model", "LogEkstrainnix", "test_model"
]
globals().update({name: globals()[name] for name in __all__})