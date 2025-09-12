import time
from typing import Optional, Tuple

import h5py
import numpy as np
import torch
from torch import Tensor
from torch.optim import SGD, Optimizer

from rbms.classes import EBM
from rbms.dataset.dataset_class import RBMDataset
from rbms.io import save_model
from rbms.map_model import map_model
from rbms.parser import default_args, set_args_default
from rbms.potts_bernoulli.classes import PBRBM
from rbms.potts_bernoulli.utils import ensure_zero_sum_gauge
from rbms.training.utils import initialize_model_archive, setup_training
from rbms.utils import check_file_existence, log_to_csv


def fit_batch_pcd(
    batch: Tuple[Tensor, Tensor],
    parallel_chains: dict[str, Tensor],
    params: EBM,
    gibbs_steps: int,
    beta: float,
    centered: bool = True,
    lambda_l1: float = 0.0,
    lambda_l2: float = 0.0,
) -> Tuple[dict[str, Tensor], dict]:
    """Sample the EBM and compute the gradient.

    Args:
        batch (Tuple[Tensor, Tensor]): Dataset samples and associated weights.
        parallel_chains (dict[str, Tensor]): Parallel chains used for gradient computation.
        params (EBM): Parameters of the EBM.
        gibbs_steps (int): Number of Gibbs steps to perform.
        beta (float): Inverse temperature.

    Returns:
        Tuple[dict[str, Tensor], dict]: A tuple containing the updated chains and the logs.
    """
    v_data, w_data = batch
    # Initialize batch
    curr_batch = params.init_chains(
        num_samples=v_data.shape[0],
        weights=w_data,
        start_v=v_data,
    )
    # sample permanent chains
    parallel_chains = params.sample_state(
        chains=parallel_chains, n_steps=gibbs_steps, beta=beta
    )
    params.compute_gradient(
        data=curr_batch,
        chains=parallel_chains,
        centered=centered,
        lambda_l1=lambda_l1,
        lambda_l2=lambda_l2,
    )
    params.normalize_grad()
    logs = {}
    return parallel_chains, logs


def train(
    train_dataset: RBMDataset,
    test_dataset: Optional[RBMDataset],
    model_type: str,
    args: dict,
    dtype: torch.dtype,
    checkpoints: np.ndarray,
    optim: Optimizer = SGD,
    map_model: dict[str, EBM] = map_model,
    default_args: dict = default_args,
) -> None:
    """Train an EBM.

    Args:
        dataset (RBMDataset): The training dataset.
        test_dataset (RBMDataset): The test dataset (not used).
        model_type (str): Type of RBM used (BBRBM or PBRBM)
        args (dict): A dictionary of training arguments.
        dtype (torch.dtype): The data type for the parameters.
        checkpoints (np.ndarray): An array of checkpoints for saving model states.
    """

    if not (args["overwrite"]):
        check_file_existence(args["filename"])

    # Create a first archive with the initialized model
    if not (args["restore"]):
        initialize_model_archive(
            args=args,
            model_type=model_type,
            train_dataset=train_dataset,
            test_dataset=test_dataset,
            dtype=dtype,
        )
    (
        params,
        parallel_chains,
        args,
        num_updates,
        start,
        elapsed_time,
        log_filename,
        pbar,
        train_dataset,
        test_dataset,
    ) = setup_training(
        args,
        map_model=map_model,
        train_dataset=train_dataset,
        test_dataset=test_dataset,
    )
    args = set_args_default(args=args, default_args=default_args)

    optimizer = optim(params.parameters(), lr=args["learning_rate"], maximize=True)

    # Continue the training
    with torch.no_grad():
        for idx in range(num_updates + 1, args["num_updates"] + 1):
            rand_idx = torch.randperm(len(train_dataset))[: args["batch_size"]]
            batch = (train_dataset.data[rand_idx], train_dataset.weights[rand_idx])
            if args["training_type"] == "rdm":
                
                parallel_chains = params.init_chains(parallel_chains["visible"].shape[0])
            elif args["training_type"] == "cd":
                parallel_chains = params.init_chains(batch[0].shape[0],weights=batch[1], start_v=batch[0])
            optimizer.zero_grad(set_to_none=False)

            
            parallel_chains, logs = fit_batch_pcd(
                batch=batch,
                parallel_chains=parallel_chains,
                params=params,
                gibbs_steps=args["gibbs_steps"],
                beta=args["beta"],
                centered=not (args["no_center"]),
                lambda_l1=args["L1"],
                lambda_l2=args["L2"],
            )
            optimizer.step()
            if isinstance(params, PBRBM):
                ensure_zero_sum_gauge(params)

            # Save current model if necessary
            if idx in checkpoints:
                curr_time = time.time() - start
                save_model(
                    filename=args["filename"],
                    params=params,
                    chains=parallel_chains,
                    num_updates=idx,
                    time=curr_time + elapsed_time,
                    flags=["checkpoint"],
                )

            # Save some logs
            learning_rates = np.array([optimizer.param_groups[0]["lr"]])
            with h5py.File(args["filename"], "a") as f:
                if "learning_rate" in f.keys():
                    learning_rates = np.append(f["learning_rate"][()], learning_rates)
                    del f["learning_rate"]
                f["learning_rate"] = learning_rates
                if hasattr(optimizer, "cosine_similarity"):
                    if "cosine_similarities" in f.keys():
                        cosine_similarities = np.append(
                            f["cosine_similarities"][()],
                            optimizer.cosine_similarity,
                        )
                        del f["cosine_similarities"]
                    f["cosine_similarities"] = cosine_similarities

            if args["log"]:
                log_to_csv(logs, log_file=log_filename)
            pbar.set_postfix_str(f"lr: {optimizer.param_groups[0]['lr']:.6f}")
            # Update progress bar
            pbar.update(1)
