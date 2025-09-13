import os
import stat

import numpy as np

from mmap_ninja import generic, numpy as np_ninja, mmap_argsort


def test_numpy(tmp_path):
    arr = np.arange(10)
    memmap = np_ninja.from_ndarray(tmp_path / "numpy_mmap", arr)

    for i, el in enumerate(arr):
        assert el == memmap[i]


def test_numpy_from_empty(tmp_path):
    arr = np.arange(10)
    memmap = np_ninja._empty(tmp_path / "numpy_mmap", dtype=np.int64, shape=(10,), order="C")
    memmap[:] = arr


def test_numpy_extend(tmp_path):
    arr = np.arange(3)
    memmap = np_ninja.from_ndarray(tmp_path / "growable", arr)
    np_ninja.extend_dir(tmp_path / "growable", np.arange(11, 13))
    memmap = np_ninja.open_existing(tmp_path / "growable")
    assert memmap[0] == 0
    assert memmap[1] == 1
    assert memmap[2] == 2
    assert memmap[3] == 11
    assert memmap[4] == 12

    memmap2 = generic.open_existing(tmp_path / "growable")
    assert np.all(memmap == memmap2)


def test_numpy_append(tmp_path):
    arr = np.arange(3)
    memmap = np_ninja.from_ndarray(tmp_path / "growable", arr)
    np_ninja.append(memmap, np.asarray(4))
    memmap = np_ninja.open_existing(tmp_path / "growable")
    assert memmap[-1] == 4


def test_numpy_extend_alternative_api(tmp_path):
    arr = np.arange(3)
    memmap = np_ninja.from_ndarray(tmp_path / "growable", arr)
    np_ninja.extend(memmap, np.arange(11, 13))
    memmap = np_ninja.open_existing(tmp_path / "growable")
    assert memmap[0] == 0
    assert memmap[1] == 1
    assert memmap[2] == 2
    assert memmap[3] == 11
    assert memmap[4] == 12

    memmap2 = generic.open_existing(tmp_path / "growable", wrapper_fn=lambda x: x / 20.0)
    assert np.allclose(memmap / 20.0, memmap2)


def simple_gen():
    for i in range(30):
        yield i


def test_numpy_from_generator(tmp_path):
    memmap = np_ninja.from_generator(
        out_dir=tmp_path / "generator", sample_generator=simple_gen(), batch_size=4, verbose=True
    )
    memmap = np_ninja.open_existing(tmp_path / "generator")
    for i in range(30):
        assert i == memmap[i]


def test_read_only(tmp_path):
    out_path = tmp_path / "read_only_numpy_memmap"
    arr = np.arange(10)
    np_ninja.from_ndarray(out_path, arr)
    # Make all memmap files read-only for the user
    for p in out_path.glob(r"**/*"):
        if not p.is_file():
            continue
        os.chmod(p, stat.S_IRUSR)
    # Open in read-only mode
    memmap = np_ninja.open_existing(out_path, mode="r")
    for i, el in enumerate(arr):
        assert el == memmap[i]


def test_sorter(tmp_path):
    arr = np.asarray([13, 9, 91, 0, 711, 715])
    arr_mmap = np_ninja.from_ndarray(tmp_path / "example", arr)
    sorter = mmap_argsort(tmp_path / "example")
    res = np.searchsorted(arr_mmap, v=91, sorter=sorter)
    assert arr_mmap[sorter[res]] == 91
    res = np.searchsorted(arr_mmap, v=90, sorter=sorter)
    assert arr_mmap[sorter[res]] == 91
