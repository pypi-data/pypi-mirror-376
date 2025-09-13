from pathlib import Path
from typing import Union
from .numpy import open_existing, from_ndarray

import numpy as np


def mmap_argsort(out_dir: Union[str, Path], mode="r"):
    sorter = np.argsort(open_existing(out_dir, mode))
    return from_ndarray(out_dir / "_sorter", sorter)

