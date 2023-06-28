"""
script will load models, save torchinfos and onnx (simplified version) for each resolution,
and replace ReduceMean with GlobalAveragePooling (since ReduceMean is not supported by tensil)

If you only need a converted onnx model, this can actually be done using one line of code :

res_height = 32
res_width = 32
torch.onnx.export(
            model,# your pytorch model
            torch.randn(1, 3, res_height, res_width, device="cpu"),
            path_model, # path to save
            verbose=False,
            opset_version=10, # mandatory for tensil
            output_names=["Output"],
)

You can check your model using netron. If you see that your model have Identity node, you need to use onnx-simplifier to simplify it.

from onnxsim import simplify

onnx_model = onnx.load(path_model)
model_simp, check = simplify(onnx_model)
onnx.save(model_simp, path_model)

If the model feature ReduceMean, use the function replace_reduce_mean.

"""

import argparse
import json
from pathlib import Path
import os
import torchinfo
import onnx
from onnxsim import simplify
import torch
import time
import numpy as np
from tqdm import tqdm
import warnings

from backbone_loader.backbone_pytorch.model import get_model


def replace_reduce_mean(
    onnx_model,
):
    """
    Replace all reduce_mean operation with GlobalAveragePool if they act on the last dimentions of the tensor
    do not change the name of this operation.
    Suppose that attribute has the following element :
        name: "axes"
        ints: -2 /2
        ints: -1 /3
        type: INTS

    Possible amelioration :
        - use more onnx helper
        - fix case where will cause another reshape to be
        - fix the case where the feature size is not the same as the last one in the reduce mean
    """

    if onnx_model.ir_version != 5:
        warnings.warn(
            "conversion of onnx was tested with ir_version 5, may not work with another one"
        )
    if len(onnx_model.graph.output) != 1:
        raise ValueError("only one output is supported")

    # find the batch size and output size
    output = onnx_model.graph.output[0]
    shape_output = output.type.tensor_type.shape.dim

    if len(shape_output) != 2:
        raise ValueError("only support output of shape (batch_size, output_size)")

    batch_size, num_feature_output = (
        shape_output[0].dim_value,
        shape_output[1].dim_value,
    )

    for pos, node in enumerate(onnx_model.graph.node):
        if node.name.find("ReduceMean") < 0:
            continue

        # check if node operate on the last op
        do_replace_mean = False
        number_attribute = len(node.attribute)
        index_keep_dims = -1
        for i in range(number_attribute):
            attribute = node.attribute[i]

            if attribute.name == "axes":
                x, y = attribute.ints
                if (x == 2 and y == 3) or (x == 3 and y == 2):
                    do_replace_mean = True
                if (x == -2 and y == -1) or (x == -1 and y == -2):
                    do_replace_mean = True
            if attribute.name == "keepdims":
                index_keep_dims = i

        # replace the node if needed
        if do_replace_mean:

            if index_keep_dims >= 0:
                if node.attribute[index_keep_dims].i == 0:

                    old_output_name = node.output.pop()

                    # reshape dimentions
                    reshape_data = onnx.helper.make_tensor(
                        name="Reshape_dim",
                        data_type=onnx.TensorProto.INT64,
                        dims=[2],
                        vals=np.array([batch_size, num_feature_output])
                        .astype(np.int64)
                        .tobytes(),
                        raw=True,
                    )
                    onnx_model.graph.initializer.append(reshape_data)

                    type_output = onnx.helper.make_tensor_type_proto(
                        onnx.TensorProto.FLOAT, shape=[batch_size, num_feature_output]
                    )

                    # print(type_output)

                    # new output layer
                    new_output_name = "reshape_output"  # onnx.helper.make_tensor_value_info("reshape_input", type_output)

                    node.output.append(new_output_name)
                    new_node = onnx.helper.make_node(
                        op_type="Reshape",
                        name=f"custom_resahpe_{pos}",
                        inputs=[new_output_name, "Reshape_dim"],
                        outputs=[old_output_name],
                    )

                    onnx_model.graph.node.insert(pos + 1, new_node)
            else:
                print("keep dim was not found")
                assert False
            for i in range(number_attribute):
                node.attribute.pop()

            node.op_type = "GlobalAveragePool"
            node.name = (
                "GlobalAveragePool" + node.name[len("ReduceMean") :]
            )  # ReduceMean_32 -> GlobalAveragePool_32
        else:
            print(
                "cant replace ReduceMean (do not recognize that the dimention are last)"
            )
    return onnx_model


def model_to_onnx(args):
    # create model path
    # one model = sevral possible resolutions
    # generate summary and save it

    # args arguments
    input_resolution = [int(i) for i in args.input_resolution]

    if args.from_hub:
        model_name = f"hub_{args.model_type}_{args.model_specification}"
    else:
        model_name = f"{args.model_type}"

    # handling path
    model = get_model(args.model_type, args.model_specification)

    parent_path = Path.cwd() / "onnx"
    parent_path.mkdir(parents=False, exist_ok=True)
    info_path = parent_path / "infos"
    info_path.mkdir(parents=False, exist_ok=True)
    weight_desc_file = info_path / f"{model_name}_description.json"

    min_res = 32
    max_res = 100  # max(input_resolution)#TODO res is to be set in function of maximum identified resolution for fpga

    number_eval = 100
    step_res = 10
    possible_res = [i for i in range(min_res, max_res, step_res)]

    # not sure it's needed, but it might be for uninitilized network
    dummy_input = torch.randn(1, 3, min_res, min_res, device="cpu")
    _ = model(dummy_input)

    # for each input, create the corresponding file
    for input_resolution in input_resolution:
        ans=torchinfo.summary(model,(3,input_resolution,input_resolution),batch_dim = 0,verbose=0,device="cpu",col_names=
            ["input_size",
            "output_size",
            "num_params",
            "kernel_size",
            "mult_adds"])




        dummy_input = torch.randn(1, 3, input_resolution,input_resolution, device="cpu")


        with open(info_path/ f"{args.save_name}_{input_resolution}x{input_resolution}_torchinfo.txt","w",encoding="utf-8") as file:
            to_write= str(ans)
            file.write(to_write)

        # generate onnx
        path_model=parent_path/ f"{args.save_name}_{input_resolution}x{input_resolution}.onnx"#f"{model_name}_{weight_name}_{input_resolution}_{input_resolution}.onnx"
        #path_model_simp=parent_path/ f"simp_{model_name}_{input_resolution}_{input_resolution}.onnx"
        torch.onnx.export(model, dummy_input, path_model, verbose=False, opset_version=10, output_names=[args.output_names])

        #load onnx

        onnx_model = onnx.load(path_model)
        onnx_model = replace_reduce_mean(onnx_model)
        # convert model
        model_simp, check = simplify(onnx_model)
        print("model was simplified")
        assert check, "Simplified ONNX model could not be validated"

        onnx.save(model_simp, path_model)



if __name__ == "__main__":
    # Define the command line arguments for the script

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-resolution",
        nargs="+",
        required=True,
        help="Input resolution(s) of the images (squared images), ex: 32 64",
    )
    parser.add_argument(
        "--from-hub", action="store_true", help="if true, add hub- to name"
    )
    parser.add_argument(
        "--model-type", type=str, required=True, help="Specification of the model"
    )
    parser.add_argument(
        "--model-specification",
        type=str,
        required=True,
        help="additional specs for model. 1. easy_resnet, path to weight 2. one of hardcoded kwargs in model.py",
    )
    parser.add_argument(
        "--output-names", default="Output", help="Name of the output layer"
    )
    parser.add_argument(
        "--check-perf",
        action="store_true",
        help="if specified, will perform inference evaluations",
    )
    parser.add_argument("--save-name", required=True, help="Name of the save model")
    args = parser.parse_args()

    model_to_onnx(args)
