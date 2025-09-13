from .CompoundSet import FloatSet, Intersection, Union

__all__ = ["FloatSet", "Intersection", "Union"]


def __incertidumbres_debug():
    # helper function so we don't import os globally
    import os

    debug_str = os.getenv("AOS_DEBUG", "False")
    if debug_str in ("True", "False"):
        return eval(debug_str)
    else:
        raise RuntimeError("unrecognized value for AOS_DEBUG: %s" % debug_str)


AOS_DEBUG = __incertidumbres_debug()  # type: bool

# Clean up imports
import sys

del sys
