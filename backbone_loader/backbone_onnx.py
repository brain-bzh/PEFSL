import numpy as np
import onnxruntime as ort
from typing import Union
import os


class BackboneOnnxWrapper:
    def __init__(self, model_path: Union[str, os.PathLike]):
        """
        Args :

            model_path : path to the onnx file

        """
        print(f"path to model : {model_path}")
        self.ort_session = ort.InferenceSession(model_path)

    def __call__(self, batch_image: np.ndarray):
        """
        img : batchified numpy img with channel last convention
        """
        assert len(batch_image.shape) == 4, "not a batch"
        channel_number = batch_image.shape[-1]
        assert batch_image.shape[0] == 1, "got sevral images in the batch"
        assert (channel_number == 3) or (
            channel_number == 1
        ), f"got numpy array of shape {batch_image.shape}, with {channel_number} channels, not the correct format (should be B C H W)"

        img = np.transpose(batch_image, (0, 3, 1, 2))  # onnx channel first convention

        outputs = self.ort_session.run(
            None,
            {"input.1": img.astype(np.float32)},
        )

        if len(outputs) > 1:
            print("warning : more than one output")
            return outputs[
                1
            ]  # return only the feature part (second part of the tuple output)
        return outputs[0]
