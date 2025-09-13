import math
from functools import lru_cache

import cv2
import numpy as np

from .types import create_face

ANCHOR_STRIDES = [8, 16, 32]
ANCHOR_SIZES = [(16, 32), (64, 128), (256, 512)]
V_C = 0.1
V_S = 0.2


@lru_cache(maxsize=len(ANCHOR_STRIDES))
def generate_anchors(stride, sizes, width, height, batch_size):
    nx = math.ceil(width / stride)
    ny = math.ceil(height / stride)
    ns = len(sizes)
    xx, yy = np.meshgrid(range(nx), range(ny))
    xy = np.column_stack((xx.ravel(), yy.ravel()))
    xy = (xy + 0.5) * stride / [width, height]
    wh = np.array(sizes)[:, np.newaxis] / [width, height]
    anchors = np.hstack((np.repeat(xy, ns, axis=0), np.tile(wh, (nx * ny, 1))))
    return np.repeat(anchors[np.newaxis, ...], batch_size, axis=0)


def rebuild_boxes(boxes, anchors):
    boxes[..., :2] = anchors[..., :2] + anchors[..., 2:] * boxes[..., :2] * V_C
    boxes[..., 2:] = anchors[..., 2:] * np.exp(boxes[..., 2:] * V_S)
    boxes[..., :2] -= boxes[..., 2:] / 2
    return boxes


def rebuild_pts(pts, anchors):
    pts[..., :2] = anchors[..., :2] + anchors[..., 2:] * pts[..., :2] * V_C
    pts[..., 2:4] = anchors[..., :2] + anchors[..., 2:] * pts[..., 2:4] * V_C
    pts[..., 4:6] = anchors[..., :2] + anchors[..., 2:] * pts[..., 4:6] * V_C
    pts[..., 6:8] = anchors[..., :2] + anchors[..., 2:] * pts[..., 6:8] * V_C
    pts[..., 8:10] = anchors[..., :2] + anchors[..., 2:] * pts[..., 8:10] * V_C
    return pts


def filter_results(boxes, scores, pts, **kwargs):
    score_threshold = kwargs.get("score_threshold", 0.9)
    top_scores = kwargs.get("top_scores", 10000)
    nms_threshold = kwargs.get("nms_threshold", 0.4)

    scores = scores[:, 1]

    indices = np.where(scores > score_threshold)
    boxes, scores, pts = boxes[indices], scores[indices], pts[indices]

    indices = scores.argsort()[::-1][:top_scores]
    boxes, scores, pts = boxes[indices], scores[indices], pts[indices]

    indices = cv2.dnn.NMSBoxes(boxes, scores, score_threshold, nms_threshold)
    boxes, scores, pts = boxes[indices], scores[indices], pts[indices]

    return boxes, scores, pts


def postprocess(outputs, batch_size, _, height, width, **kwargs):
    boxes, scores, pts = outputs

    start = 0
    for stride, sizes in zip(ANCHOR_STRIDES, ANCHOR_SIZES):
        anchors = generate_anchors(stride, sizes, width, height, batch_size)
        end = start + anchors.shape[1]
        boxes[:, start:end, :] = rebuild_boxes(boxes[:, start:end, :], anchors)
        pts[:, start:end, :] = rebuild_pts(pts[:, start:end, :], anchors)
        start = end

    boxes *= [width, height] * 2
    pts *= [width, height] * 5

    results = []
    for batch in zip(boxes, scores, pts):
        batch = filter_results(*batch, **kwargs)
        results.append([create_face(b, s, p) for b, s, p in zip(*batch)])

    return results
