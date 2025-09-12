from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import torch

from rbms.dataset.dataset_class import RBMDataset
from rbms.dataset.load_fasta import load_FASTA
from rbms.dataset.load_h5 import load_HDF5
from rbms.dataset.utils import get_subset_labels, get_unique_indices


def load_dataset(
    dataset_name: str,
    test_dataset_name: Optional[str] = None,
    subset_labels: Optional[List[int]] = None,
    use_weights: bool = False,
    binarize: bool = False,
    alphabet="protein",
    device: str = "cpu",
    dtype: torch.dtype = torch.float32,
) -> Tuple[RBMDataset, RBMDataset | None]:
    return_datasets = []
    for dset_name in [dataset_name, test_dataset_name]:
        data = None
        is_binary = True
        labels = None
        weights = None
        names = None

        if dset_name is not None:
            dset_name = Path(dset_name)
            print(f"Reading dataset from {str(dset_name)}...")
            match dset_name.suffix:
                case ".h5":
                    data, labels = load_HDF5(filename=dset_name, binarize=binarize)
                case ".fasta":
                    data, weights, names = load_FASTA(
                        filename=dset_name,
                        binarize=binarize,
                        use_weights=use_weights,
                        alphabet=alphabet,
                        device=device,
                    )
                    if not binarize:
                        is_binary = False
                case ".dat":
                    data = np.genfromtxt(dset_name)
                    is_binary = False
                case _:
                    raise ValueError(
                        """
                    Dataset could not be loaded as the type is not recognized.
                    It should be either:
                        - '.h5',
                        - '.fasta'
                    """
                    )

            # Select subset of dataset w.r.t. labels
            if subset_labels is not None and labels is not None:
                data, labels = get_subset_labels(data, labels, subset_labels)

            if weights is None:
                weights = np.ones(data.shape[0])
            if names is None:
                names = np.arange(data.shape[0])
            if labels is None:
                labels = -np.ones(data.shape[0])

            # Remove duplicates and internally shuffle the dataset
            unique_ind = get_unique_indices(torch.from_numpy(data)).cpu().numpy()

            idx = torch.randperm(unique_ind.shape[0])
            data = data[unique_ind[idx]]
            labels = labels[unique_ind[idx]]
            weights = weights[unique_ind[idx]]
            names = names[unique_ind[idx]]

            return_datasets.append(
                RBMDataset(
                    data=data,
                    labels=labels,
                    weights=weights,
                    names=names,
                    dataset_name=dataset_name,
                    is_binary=is_binary,
                    device=device,
                    dtype=dtype,
                )
            )
            print("    Done")
        else:
            return_datasets.append(None)
    return tuple(return_datasets)
