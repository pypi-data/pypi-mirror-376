import os
from pathlib import Path

import numpy as np
import pytest

from retinaface import read_image, read_image_url, detect_faces, draw_faces


@pytest.fixture
def test_image_path():
    root = Path(__file__).parent.parent
    return root / "images" / "test.jpg"


@pytest.fixture
def test_image_url():
    return "https://raw.githubusercontent.com/biubug6/Pytorch_Retinaface/refs/heads/master/curve/test.jpg"


def test_detect_face_color(test_image_path):
    image = read_image(test_image_path)
    faces = detect_faces(image)

    assert len(faces) == 22


def test_detect_face_grayscale(test_image_path):
    image = read_image(test_image_path, color_mode="GRAYSCALE")
    faces = detect_faces(image)

    assert len(faces) == 17


@pytest.mark.parametrize("batch_size", [1, 2, 4, 8])
def test_detect_face_color_batch(test_image_path, batch_size):
    image = read_image(test_image_path)
    input_batch = np.stack([image] * batch_size, axis=0)

    output_batch = detect_faces(input_batch)

    assert len(output_batch) == batch_size

    for faces in output_batch:
        assert len(faces) == 22


@pytest.mark.parametrize("batch_size", [1, 2, 4, 8])
def test_detect_face_grayscale_batch(test_image_path, batch_size):
    image = read_image(test_image_path, color_mode="GRAYSCALE")
    input_batch = np.stack([image] * batch_size, axis=0)

    output_batch = detect_faces(input_batch)

    assert len(output_batch) == batch_size

    for faces in output_batch:
        assert len(faces) == 17


def test_detect_face_image_url(test_image_url):
    image = read_image_url(test_image_url)
    faces = detect_faces(image)

    assert len(faces) == 22


def test_draw_faces(test_image_path):
    image = read_image(test_image_path)
    faces = detect_faces(image)

    draw_faces(image, faces, "tmp.jpg")

    os.remove("tmp.jpg")


@pytest.mark.parametrize(
    "image, exception",
    [
        ("test.jpg", TypeError),  # Image path
        (np.zeros((230400)), ValueError),  # Flat image
        (np.zeros((320, 240, 1)), ValueError),  # Invalid number of channels
        (np.zeros((320, 240, 2)), ValueError),  # Grayscale alpha batch
        (np.zeros((320, 240, 4)), ValueError),  # RGBA batch
        (np.zeros((1, 320, 240, 1)), ValueError),  # Invalid number of channels
        (np.zeros((1, 320, 240, 2)), ValueError),  # Grayscale alpha batch
        (np.zeros((1, 320, 240, 4)), ValueError),  # RGBA batch
        (np.zeros((1, 320, 240, 5)), ValueError),  # Invalid number of channels
        (np.zeros((1, 1, 320, 240, 3)), ValueError),  # Unsupported array
    ],
)
def test_invalid_inputs(image, exception):
    with pytest.raises(exception):
        detect_faces(image)
