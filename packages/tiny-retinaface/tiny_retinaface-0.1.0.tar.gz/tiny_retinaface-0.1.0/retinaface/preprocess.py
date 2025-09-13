import numpy as np

from .checks import is_inputs_grayscale, is_inputs_grayscale_batch, is_inputs_color

MEAN = np.array([104, 117, 127], dtype=np.int16)


def preprocess(inputs):
    # Grayscale -> color
    if is_inputs_grayscale(inputs) or is_inputs_grayscale_batch(inputs):
        inputs = np.stack([inputs] * 3, axis=-1)

    # Add batch dim
    if is_inputs_color(inputs):
        inputs = inputs[np.newaxis, :]

    # RGB -> BGR
    inputs = inputs[..., [2, 1, 0]]

    # Subtract mean
    inputs = inputs.astype(np.int16)
    np.subtract(inputs, MEAN, out=inputs)

    # Cast to fp32
    inputs = inputs.astype(np.float32)

    # NHWC -> NCHW
    inputs = np.transpose(inputs, (0, 3, 1, 2))

    return inputs
