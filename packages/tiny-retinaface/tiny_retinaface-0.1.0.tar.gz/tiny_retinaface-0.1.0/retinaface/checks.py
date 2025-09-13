import numpy as np


def is_inputs_grayscale(inputs):
    return inputs.ndim == 2


def is_inputs_color(inputs):
    return inputs.ndim == 3 and inputs.shape[-1] == 3


def is_inputs_grayscale_batch(inputs):
    return inputs.ndim == 3 and inputs.shape[-1] not in (1, 2, 3, 4)


def is_inputs_color_batch(inputs):
    return inputs.ndim == 4 and inputs.shape[-1] == 3


def check_inputs(inputs):
    if not isinstance(inputs, np.ndarray):
        raise TypeError("Inputs must be an ndarray")

    if (
        not is_inputs_grayscale(inputs)
        and not is_inputs_color(inputs)
        and not is_inputs_grayscale_batch(inputs)
        and not is_inputs_color_batch(inputs)
    ):
        raise ValueError(f"Unsupported inputs shape: {inputs.shape}")
