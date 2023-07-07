print("importing torch")
import torch
import numpy as np
from typing import Union
import os

print("torch imported")

from backbone_loader.backbone_pytorch.model import get_model


class TorchBatchModelWrapper:
    """
    Wrapps a torch model to input/output ndarray
    """

    def __init__(self, model_name: Union[str, os.PathLike], weights, use_strides, device="cpu"):
        self.model = get_model(model_name, weights, use_strides, device=device)
        self.device = device

    def __call__(self, batch_img: np.ndarray):
        """
        return the features from an img
        args :
            - batch_img(np.ndarray) : represent a batch of image (channel last convention)
        """
        channel_number = batch_img.shape[3]
        assert len(batch_img.shape) == 4
        assert (channel_number == 3) or (
            channel_number == 1
        ), f"got numpy array of shape {batch_img.shape}, with {channel_number} channels, not the correct format (should be B C H W)"
        self.model.eval()

        # convertion to tensor with channel first convention
        batch_img = np.transpose(batch_img, (0, 3, 1, 2))
        batch_img = torch.from_numpy(batch_img)
        batch_img = batch_img.to(self.device)

        with torch.no_grad():
            features = self.model(batch_img)
        return features.cpu().numpy()
