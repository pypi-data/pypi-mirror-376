import os.path
from typing import Optional

import torch
from torch import nn
from torch.nn import DataParallel
from torch.nn.parallel import DistributedDataParallel
from torch.optim import Optimizer

from jbag.io import ensure_output_file_dir_existence
from jbag.log import logger

MODEL = "model"
OPTIMIZER = "optimizer"


def get_unwrapped_model(model: nn.Module):
    if isinstance(model, (DataParallel, DistributedDataParallel)):
        model = model.module
    return model


def save_weights(file: str, model: nn.Module, optimizer: Optional[Optimizer] = None,
                 **kwargs):
    checkpoint = {MODEL: get_unwrapped_model(model).state_dict()}
    if optimizer:
        checkpoint[OPTIMIZER] = optimizer.state_dict()
    for k, v in kwargs.items():
        if k in checkpoint:
            raise KeyError(f"Get duplicated key {k}.")
        checkpoint[k] = v
    ensure_output_file_dir_existence(file)
    torch.save(checkpoint, file)


def load_weights(input_weights_file: str, model: Optional[nn.Module] = None,
                 optimizer: Optional[Optimizer] = None, map_location=None):
    if not os.path.isfile(input_weights_file):
        raise FileNotFoundError(f"Input weights file {input_weights_file} does not exist.")
    checkpoint = torch.load(input_weights_file, map_location=map_location)
    if model:
        if MODEL not in checkpoint:
            logger.warning(f"{input_weights_file} does not include model weights.")
        else:
            model = get_unwrapped_model(model)
            model.load_state_dict(checkpoint[MODEL])
            logger.info(f"Loading model weights from {input_weights_file}.")

    if optimizer:
        if OPTIMIZER not in checkpoint:
            logger.warning(f"{input_weights_file} does not include optimizer weights.")
        else:
            optimizer.load_state_dict(checkpoint[OPTIMIZER])
            logger.info(f"Loading optimizer weights from {input_weights_file}.")
    return checkpoint
