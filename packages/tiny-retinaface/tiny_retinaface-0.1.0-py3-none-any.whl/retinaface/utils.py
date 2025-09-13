from urllib.request import urlopen

import cv2
import numpy as np

COLOR_MODES = {
    "GRAYSCALE": cv2.IMREAD_GRAYSCALE,
    "COLOR": cv2.IMREAD_COLOR_RGB,
}

SCALING_FACTOR = 0.2
TEXT_FONT = cv2.FONT_HERSHEY_DUPLEX
TEXT_SCALING = 0.12
TEXT_COLOR = (255, 255, 255)
BOX_COLOR = (0, 0, 255)
LANDMARKS_COLORS = [
    (0, 0, 255),  # Right eye (Red)
    (0, 255, 255),  # Left eye (Yellow)
    (255, 0, 255),  # Nose (Magenta)
    (0, 255, 0),  # Right mouth (Green)
    (255, 0, 0),  # Left mouth (Blue)
]


def decode_image(image, color_mode):
    image = np.frombuffer(image, np.uint8)
    image = cv2.imdecode(image, COLOR_MODES[color_mode])
    return image


def read_image(path, color_mode="COLOR"):
    with open(path, "rb") as f:
        image = f.read()

    image = decode_image(image, color_mode)

    return image


def read_image_url(url, color_mode="COLOR"):
    with urlopen(url) as response:
        image = response.read()

    image = decode_image(image, color_mode)

    return image


def draw_faces(image, faces, filename=None):
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    for face in faces:
        face_area = face.width * face.height
        rel_size = max(1, int(face_area**SCALING_FACTOR))

        pt1 = (face.x, face.y)
        pt2 = (face.x + face.width, face.y + face.height)
        cv2.rectangle(image, pt1, pt2, BOX_COLOR, rel_size)

        text = f"{face.score:.5f}"
        org = (face.x, int(face.y + face.height * TEXT_SCALING))
        text_size = rel_size * TEXT_SCALING
        cv2.putText(image, text, org, TEXT_FONT, text_size, TEXT_COLOR)

        for landmarks, color in zip(face.landmarks, LANDMARKS_COLORS):
            center = (landmarks.x, landmarks.y)
            cv2.circle(image, center, rel_size, color, -1)

    if filename:
        cv2.imwrite(filename, image)

    return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
