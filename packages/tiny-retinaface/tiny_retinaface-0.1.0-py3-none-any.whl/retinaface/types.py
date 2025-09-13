from dataclasses import dataclass


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Face:
    score: float
    x: int
    y: int
    width: int
    height: int
    landmarks: list[Point]


def create_face(box, score, pts):
    landmarks = [Point(int(x), int(y)) for x, y in pts.reshape(-1, 2)]
    x, y, width, height = [int(i) for i in box]
    return Face(float(score), x, y, width, height, landmarks)
