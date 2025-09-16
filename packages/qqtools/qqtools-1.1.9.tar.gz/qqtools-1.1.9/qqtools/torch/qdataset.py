import copy
import functools
import os
import pickle
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import List, Sequence, Union

import numpy as np
import torch
import torch.utils
from torch import Tensor
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

import qqtools as qt

from ..qdict import qDict


def _get_data_splits(
    total_num,
    sizes=None,
    ratios=None,
    seed=1,
):
    """Split data into train/validation/test sets based on either sizes or ratios.

    Args:
        total_num (_type_): _description_
        sizes (Sequence[int], optional): Absolute sizes for splits, e.g., [800, 100, 100].
            If sizes only has 2 elements, the return value of test indices will be None.
            If sizes[2] is -1, test size will be calculated as total_num - train - val.
            Mutually exclusive with ratios parameter.
        ratios (Sequence[float], optional): Relative ratios for splits, e.g., [0.8, 0.1, 0.1].
            If ratios only has 2 elements, the return value of test indices will be None.
            The sum of ratios should not exceed 1 (with small tolerance for floating point errors).
            Mutually exclusive with sizes parameter.
        seed (int, optional): Random seed for reproducibility. Defaults to 1.

    Returns:
        tuple: Three elements containing:
            - train_idx (ndarray): Indices for training set
            - valid_idx (ndarray): Indices for validation set
            - test_idx (ndarray or None): Indices for test set (None if not specified)

    Examples:
        >>> # Size-based splitting
        >>> train, val, test = get_data_splits(1000, sizes=[800, 100, 100])
        >>> # Ratio-based splitting
        >>> train, val, test = get_data_splits(1000, ratios=[0.8, 0.1, 0.1])
        >>> # Without test set
        >>> train, val, _ = get_data_splits(1000, ratios=[0.9, 0.1])
    """
    rng = np.random.RandomState(seed)
    indices = rng.permutation(total_num)

    if sizes is not None:
        # Handle size-based splitting
        assert len(sizes) in [2, 3], "sizes must have length 2 or 3"
        assert all(isinstance(s, int) for s in sizes), "sizes must be integers"
        assert sum(sizes) <= total_num, "Sum of sizes exceeds total number of samples"
        train_size = sizes[0]
        val_size = sizes[1]
        if len(sizes) > 2:
            if sizes[2] == -1:
                test_size = total_num - train_size - val_size
                assert test_size >= 0, "Calculated test size is negative"
            else:
                test_size = sizes[2]
        else:
            test_size = None
        # Verify total size
        total_split = train_size + val_size + (test_size if test_size is not None else 0)
        assert total_split <= total_num, f"Sum of sizes ({total_split}) exceeds total number of samples ({total_num})"
        # Split indices
        train_end = train_size
        valid_end = train_end + val_size
        train_idx = indices[:train_end]
        valid_idx = indices[train_end:valid_end]

        if test_size is not None:
            test_idx = indices[valid_end : valid_end + test_size]
        else:
            test_idx = None

    elif ratios is not None:
        assert len(ratios) in [2, 3], "ratio must have length 2 or 3"
        assert sum(ratios) <= 1 + 1e-6, "Sum of ratios exceeds 1"

        train_end = int(ratios[0] * total_num)
        valid_end = train_end + int(ratios[1] * total_num)
        train_idx = indices[:train_end]
        valid_idx = indices[train_end:valid_end]

        if len(ratios) > 2:
            test_end = valid_end + int(ratios[2] * total_num)
            test_idx = indices[valid_end:test_end]
        else:
            test_idx = None
    else:
        raise ValueError("Either sizes or ratio must be provided")
    return train_idx, valid_idx, test_idx


class qData(qDict):

    def to(self, device):
        for k, v in self.items():
            if isinstance(v, torch.Tensor):
                self[k] = v.to(device)
        return self

    @staticmethod
    def get_data_splits(
        total_num,
        sizes=None,
        ratios=None,
        seed=1,
    ):
        return _get_data_splits(total_num, sizes, ratios, seed)


def qbatch_collate(data_list):
    """no pad, assume all data have same length"""
    v = data_list[0]
    if isinstance(v, torch.Tensor):
        res = torch.stack(data_list)  # (bz,)
    elif isinstance(v, (np.ndarray, np.generic)):
        res = np.stack(data_list)  # (bz, *)
        res = torch.as_tensor(res)
    else:
        raise TypeError(f"type {type(v)}")
    return res


def qdict_pad_collate_fn(batch_list: List[dict], padding: dict, target_keys):
    """
    maybe need multi type support
    """
    output = qData(default_function=list)
    for p in batch_list:
        for k, v in p.items():
            if target_keys is not None and k not in target_keys:
                continue
            if isinstance(v, (list, np.ndarray, np.generic, torch.Tensor)):
                output[k].append(torch.as_tensor(v))
            elif isinstance(v, str):
                continue
            else:
                raise TypeError(f"{type(v)}")
    for k, v in output.items():
        if isinstance(v[0], torch.Tensor):
            if v[0].dim() == 0:
                output[k] = torch.stack(v)  # (bz,)
            else:
                output[k] = torch.nn.utils.rnn.pad_sequence(v, True, padding[k])

            # TODO remove... tempory fix
            if output[k].dtype == torch.uint8:
                output[k] = output[k].type(torch.int64)

    return output


class qDictDataset(torch.utils.data.Dataset, ABC):
    """
    self.datalist : List[dict]

    We employ the same filepath convention with the pyg package.

    override `get()` and `len()` to customize the dataset.
    """

    def __init__(self, root):
        self.root = root
        self.data_list: List[dict] = []
        self._indices = None
        self.processed_dir.mkdir(exist_ok=True, parents=True)
        if not self.processed_files_exists():
            with qt.Timer("Process raw files", prefix="[qDataset]"):
                self._process()

    @property
    @abstractmethod
    def raw_file_names(self):
        raise NotImplementedError()

    @property
    @abstractmethod
    def processed_file_names(self):
        raise NotImplementedError()

    @property
    def raw_dir(self):
        return Path(self.root).joinpath("raw").absolute()

    @property
    def processed_dir(self):
        return Path(self.root).joinpath("processed").absolute()

    @property
    def raw_paths(self):
        return [str(self.raw_dir / fn) for fn in self.raw_file_names]

    @property
    def processed_paths(self):
        return [str(self.processed_dir / fn) for fn in self.processed_file_names]

    def __getitem__(self, idx) -> Union[dict, torch.utils.data.Dataset]:
        if (
            isinstance(idx, (int, np.integer))
            or (isinstance(idx, torch.Tensor) and idx.dim() == 0)
            or (isinstance(idx, np.ndarray) and np.isscalar(idx))
        ):
            if self._indices is not None:
                idx = self._indices[idx]
            return self.get(idx)
        else:
            return self.index_select(idx)

    def get(self, true_idx):
        return self.data_list[true_idx]

    def len(self):
        return len(self.data_list)

    def __len__(self) -> int:
        return len(self.indices())

    def indices(self) -> Sequence:
        return range(self.len()) if self._indices is None else self._indices

    def __iter__(self):
        for idx in self.indices():
            yield self.__getitem__(idx)

    def index_select(self, idx: Union[slice, Tensor, np.ndarray, Sequence]) -> torch.utils.data.Dataset:
        indices = self.indices()

        if isinstance(idx, slice):
            indices = indices[idx]

        elif isinstance(idx, Tensor) and idx.dtype == torch.long:
            return self.index_select(idx.flatten().tolist())

        elif isinstance(idx, Tensor) and idx.dtype == torch.bool:
            idx = idx.flatten().nonzero(as_tuple=False)
            return self.index_select(idx.flatten().tolist())

        elif isinstance(idx, np.ndarray) and idx.dtype == np.int64:
            return self.index_select(idx.flatten().tolist())

        elif isinstance(idx, np.ndarray) and idx.dtype == bool:
            idx = idx.flatten().nonzero()[0]
            return self.index_select(idx.flatten().tolist())

        elif isinstance(idx, Sequence) and not isinstance(idx, str):
            indices = [indices[i] for i in idx]

        else:
            raise IndexError(
                f"Only slices (':'), list, tuples, torch.tensor and "
                f"np.ndarray of dtype long or bool are valid indices (got "
                f"'{type(idx).__name__}')"
            )

        dataset = copy.copy(self)
        dataset._indices = indices
        return dataset

    def processed_files_exists(self):
        return all([Path(f).exists() for f in self.processed_paths])

    def raw_files_exists(self):
        return all([Path(f).exists() for f in self.raw_paths])

    def _process(self):
        if hasattr(self, "process"):
            self.process()

    def shuffle(
        self,
    ) -> "torch.utils.data.Dataset":
        perm = torch.randperm(len(self))
        dataset = self.index_select(perm)
        return dataset

    def collate(self, batch_size, target_keys=None, padding: dict = None):
        """prepare"""
        if padding is None:
            padding = self.padding if hasattr(self, "padding") else defaultdict(lambda: 0)

        def yield_batch_data(iterable_sequence: List[dict], batch_size, target_keys, padding):
            batch = []
            i = 0
            for d in iterable_sequence:
                batch.append(d)
                i += 1
                if i == batch_size:
                    i = 0
                    yield qdict_pad_collate_fn(batch, padding, target_keys)
                    batch = []

            if len(batch) > 0:
                yield qdict_pad_collate_fn(batch, padding, target_keys)

        yield_fn = functools.partial(
            yield_batch_data,
            batch_size=batch_size,
            target_keys=target_keys,
            padding=padding,
        )
        return qDictDataloader(self, batch_size, yield_fn)

    def get_norm_factor(self, target):
        vs = [self.data_list[i][target] for i in self.indices()]
        val = qbatch_collate(vs)
        mean = torch.mean(val).item()
        std = torch.std(val).item()
        return (mean, std)

    def get_splits(self, ratio=[0.8, 0.1, 0.1], seed=None):
        total_num = self.__len__()
        return _get_data_splits(total_num, seed)


class qDictDataloader(torch.utils.data.DataLoader):
    def __init__(self, dataset, batch_size, yield_fn=None, shuffle=False, **kwargs):
        self.yield_fn = yield_fn
        self.batch_list = None
        super().__init__(dataset, batch_size, shuffle=shuffle, collate_fn=qdict_pad_collate_fn, **kwargs)

    def __iter__(self):
        if self.batch_list is not None:
            return iter(self.batch_list)
        elif self.yield_fn is not None:
            return self.yield_fn(iter(self.dataset))
        else:
            return super().__iter__()

    def cache(self):
        assert self.yield_fn is not None
        self.batch_list = list(self.yield_fn(iter(self.dataset)))
        return self
