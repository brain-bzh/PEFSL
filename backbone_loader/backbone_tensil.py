import os
import json
import numpy as np
from typing import Union
from pynq import Overlay
from tcu_pynq.driver import Driver
from tcu_pynq.architecture import Architecture
from tcu_pynq.data_type import DataType


class BackboneTensilWrapper:
    def __init__(
        self,
        overlay: Overlay,
        path_tmodel: Union[str, os.PathLike],
        onnx_output_name: str = "Output",
        debug=False,
    ):
        """
        Args :
            - path_bit : path of the bitstream, e.g : home/xilinx/bitstream.bit
            - path_tmodel : path of the tmodel, e.g : home/xilinx/model.tmodel
        """
        print(f"AXI DMA 0 : {overlay.axi_dma_0}")
	
        if not hasattr(overlay, "axi_dma_0"):
            raise RuntimeError("DMA was not found in overlay")
        with open(path_tmodel) as f:
            js = json.load(f)
            arch = js["arch"]
            arch["data_type"] = DataType[arch["data_type"]]
            self.tarch = Architecture(**arch)

        self.tcu = Driver(self.tarch, overlay.axi_dma_0, debug=debug)
        print("TCU successfully loaded.")

        with open(path_tmodel, "r") as f:
            outputs = json.loads(f.read())["outputs"]
            output_names = [output["name"] for output in outputs]
            if onnx_output_name not in output_names:
                raise Exception(f"{onnx_output_name} not in tmodel output names. Set the onnx output name as {onnx_output_name}")
            self.output_name = onnx_output_name
        self.tcu.load_model(path_tmodel)
        assert self.tcu.arch.array_size >= 3, "array size must be >=3"

    def __call__(self, single_image_batch: np.ndarray):
        assert len(single_image_batch.shape) == 4, "single image is not a batch"
        assert (
            single_image_batch.shape[0] == 1
        ), "img is supposed to be a batch of size one"
        assert single_image_batch.shape[-1] == 3, "last channel is not a rgb image"

        img = single_image_batch[0]
        img = img.reshape((-1, 3)) # 3 for rgb
        inputs = {"input.1": img}
        outputs = self.tcu.run(inputs)

        return outputs[self.output_name][None, :]
