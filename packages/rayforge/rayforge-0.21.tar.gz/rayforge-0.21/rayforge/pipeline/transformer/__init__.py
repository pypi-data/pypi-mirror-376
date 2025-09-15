# flake8: noqa:F401
import inspect
from .base import OpsTransformer
from .multipass import MultiPassTransformer
from .arcwelder import ArcWeld
from .optimize import Optimize
from .smooth import Smooth

transformer_by_name = dict(
    (name, obj) for name, obj in locals().items()
    if inspect.isclass(obj) and
    issubclass(obj, OpsTransformer) and
    not inspect.isabstract(obj)
)

__all__ = [
    "OpsTransformer",
    "MultiPassTransformer",
    "ArcWeld",
    "Optimize",
    "Smooth",
    "transformer_by_name",
]
