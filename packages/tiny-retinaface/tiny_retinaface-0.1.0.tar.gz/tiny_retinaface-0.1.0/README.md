# Tiny RetinaFace

![ci](https://github.com/ddfabbro/tiny-retinaface/actions/workflows/ci.yaml/badge.svg)
![python](https://img.shields.io/badge/python-3.9+-blue)
![license](https://img.shields.io/badge/license-MIT-blue)

Tiny RetinaFace is a fast and simplified implementation of [biubug6/Pytorch_Retinaface](https://github.com/biubug6/Pytorch_Retinaface) inference module

## Installation

```
pip install tiny-retinaface
```

## Usage

```python
from retinaface import read_image, detect_faces

# Read image as RGB ndarray
image = read_image("images/test.jpg")

# Detect faces as list of Face objects
faces = detect_faces(image)
```

## Face object

```python
Face(
    score=0.9997380375862122,
    x=142,
    y=322,
    width=60,
    height=72,
    landmarks=[
        Point(x=160, y=348),
        Point(x=187, y=345),
        Point(x=177, y=362),
        Point(x=165, y=376),
        Point(x=188, y=374)
    ]
)
```

## Tiny RetinaFace Results on World Largest Selfie

```python
from retinaface import read_image_url, detect_faces, draw_faces

url = "https://github.com/yakhyo/retinaface-pytorch/blob/main/assets/large_selfi.jpg?raw=true"

image = read_image_url(url)
faces = detect_faces(image, score_threshold=0.1, nms_threshold=0.1)

draw_faces(image, faces, filename="images/results.jpg")
```

![largest_selfie](https://github.com/ddfabbro/tiny-retinaface/blob/master/images/results.jpg?raw=true)

## Acknowledgements

- Original RetinaFace implementation: [deepinsight/insightface](https://github.com/deepinsight/insightface)
- Pytorch RetinaFace implementation: [biubug6/Pytorch_Retinaface](https://github.com/biubug6/Pytorch_Retinaface)
- RetinaFace pretrained onnx weights: [yakhyo/retinaface-pytorch](https://github.com/yakhyo/retinaface-pytorch)

## References

```
@inproceedings{Deng2020CVPR,
title = {RetinaFace: Single-Shot Multi-Level Face Localisation in the Wild},
author = {Deng, Jiankang and Guo, Jia and Ververas, Evangelos and Kotsia, Irene and Zafeiriou, Stefanos},
booktitle = {CVPR},
year = {2020}
}
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
