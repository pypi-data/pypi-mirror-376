import onnxruntime as ort

from .checks import check_inputs, is_inputs_grayscale_batch, is_inputs_color_batch
from .preprocess import preprocess
from .postprocess import postprocess
from .utils import read_image, read_image_url, draw_faces
from .weights import WEIGHTS

ONNX_SESSION = None


def detect_faces(inputs, **kwargs):
    """
    Detect faces in an image or batch of images.

    This function supports both grayscale and RGB images, as well as batches
    of those images. It returns a list of `Face` objects for each detected face,
    containing bounding boxes, confidence scores, and facial landmarks.

    Args:
        inputs (numpy.ndarray): Input image or batch of images.
            - Grayscale image: `(H, W)`
            - RGB image: `(H, W, 3)`
            - Batch of grayscale images: `(N, H, W)`
            - Batch of RGB images: `(N, H, W, 3)`
        **kwargs: Additional configuration options.
            - score_threshold (float, default=0.9): Confidence score threshold.
            - top_scores (int, default=10000): Maximum number of top scores to consider.
            - nms_threshold (float, default=0.4): Non-maximum suppression threshold.

    Returns:
        list[Face] or list[list[Face]]: Detected faces.
            - For single images: a list of `Face` objects.
            - For batches: a list of lists, where each sublist corresponds to one image.

    Note:
        A `Face` object is a dataclass with the following fields:
            - score (float): Confidence score of the detection.
            - x (int): X-coordinate of the top-left corner of the bounding box.
            - y (int): Y-coordinate of the top-left corner of the bounding box.
            - width (int): Width of the bounding box.
            - height (int): Height of the bounding box.
            - landmarks (list[Point]): Facial landmarks.

        A `Point` is a dataclass with the following fields:
            - x (int): X-coordinate of the landmark.
            - y (int): Y-coordinate of the landmark.

    Example:
        >>> from retinaface import read_image, detect_faces
        >>> image = read_image("images/test.jpg")
        >>> faces = detect_faces(image)
    """
    global ONNX_SESSION

    check_inputs(inputs)

    processed_inputs = preprocess(inputs)

    if ONNX_SESSION is None:
        ONNX_SESSION = ort.InferenceSession(WEIGHTS)

    outputs = ONNX_SESSION.run(None, {"input": processed_inputs})
    results = postprocess(outputs, *processed_inputs.shape, **kwargs)

    if not is_inputs_grayscale_batch(inputs) and not is_inputs_color_batch(inputs):
        results = results[0]

    return results


__all__ = [
    detect_faces,
    read_image,
    read_image_url,
    draw_faces,
]
