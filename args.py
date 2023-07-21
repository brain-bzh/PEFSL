"""
adapted from :
EASY - Ensemble Augmented-Shot Y-shaped Learning: State-Of-The-Art Few-Shot Classification with Simple Ingredients.
(https://github.com/ybendou/easy)
(to load a model without training)
"""

import argparse
import os
import sys


def convert_to_absolute(path):
    return os.path.abspath(path)


def create_args(parser):
    ### FRAMEWORK ###
    parser.add_argument("--framework", type=str, required=True, choices=["pytorch","tensil","onnx"], help="Framework to use for the backbone.")

    ### BACKBONE ###
    parser.add_argument("--backbone", type=str, default="resnet9", help="Specify the model of backbone used. Can only be resnet9 or resnet12.")

    ### MODEL ###
    parser.add_argument("--resolution-input", type=int, default=32, help="Resolution of the input image.")
    parser.add_argument("--classifier-type", type=str, default="ncm", help="Type of classifier, ncm or knn.")   
    parser.add_argument("--number-neiboors", type=int, default=5, help="number of neiboors for knn classifier.")

    ### PYTORCH ###
    parser.add_argument("--device-pytorch", type=str, default="cpu", help="Device on which the backbone will be run. Can be cudo:0, cuda:1, cpu, ...")
    parser.add_argument("--path-pytorch-weight", type=str, default="../resnet9_strided_16fmaps.pt", help="Path of the pytorch weight.")
    parser.add_argument("--no-strides", action="store_false", default=False, help="If you want to use maxpooling instead of strides.")

    ### TENSIL ###
    parser.add_argument("--path-bit", type=str, default="/home/xilinx/design.bit", help="The bitstream name or absolute path as a string.")
    parser.add_argument("--path-tcu", type=str, default="/home/xilinx", help="The path to the driver (added to the path).")
    parser.add_argument("--path-tmodel", type=str, default="/home/xilinx/resnet9_strided_16fmaps_onnx_custom_perf.tmodel", help="Path of the tmodel. The tprog and tdata must be in the same folder.")

    ### ONNX ###
    parser.add_argument("--path-onnx", type=str, default="../resnet9_strided_16fmaps.onnx", help="Path of the .onnx file. Input image resolution should match the resolution of the model.")

    ### PARAMETERS FOR THE DEMO ###
    # Camera
    parser.add_argument("--camera-specification", type=int, default=0, help="Specification of the camera. 0 for the first camera, 1 for the second ...")
    parser.add_argument("--camera-resolution", type=str, default="640x480", help="Camera resolution. Must be 16:9 and less or equal to resolution max.")
    # Buttons
    parser.add_argument("--button", type=str, default="keyboard", help="Input device for the button. Can be keyboard (on computer), pynq (on pynq) or keyboard-pynq (simulate pynq on computer).")
    # Output
    parser.add_argument("--output-resolution", type=str, default="800x540", help="Output resolution of the frame (width/height).")
    parser.add_argument("--general-scale", type=float, default=1, help="General scale (=1 for the pynq screen).")
    parser.add_argument("--hdmi-display", action="store_true", help="To display on the hdmi screen of the pynq. If False, display on the computer screen.")


def framework_choice(args):
    """
    Give the correct backbone specifications according to the framework choose by the user
    """
    if args.framework == "pytorch":
        # backbone arguments
        args.backbone_specs = {"type":args.framework, "device":args.device_pytorch, "model_name":args.backbone, "use_strides":not args.no_strides}
        # weights path
        args.backbone_specs["weight"] = args.path_pytorch_weight
        print("Backbone specification :",args.backbone_specs)
    
    elif args.framework == "tensil":
        args.path_bit = convert_to_absolute(args.path_bit)
        args.path_tcu = convert_to_absolute(args.path_tcu)
        print("Bitstream path :",args.path_bit)
        from pynq import Overlay
        args.overlay = Overlay(args.path_bit)
        sys.path.append(args.path_tcu)
        # backbone arguments
        args.backbone_specs = {"type":args.framework, "overlay":args.overlay, "path_tmodel":args.path_tmodel}
        print("Backbone specification :",args.backbone_specs)

    elif args.framework == "onnx":
        args.backbone_specs = {"type":args.framework, "path_onnx":args.path_onnx}
        print("Backbone specification :",args.backbone_specs)
    
    else:
        raise f"Framework {args.framework} is not defined."
    
    # classifier arguments
    args.classifier_specs = {"model_name":args.classifier_type}
    if args.classifier_type == "knn":
        args.classifier_specs["kwargs"] = {"number_neighboors":args.number_neiboors}


def args_treatement(args):
    args.output_resolution = tuple(map(int,args.output_resolution.split('x'))) # Tuple conversion
    args.camera_resolution = tuple(map(int,args.camera_resolution.split('x'))) # Tuple conversion
    args.padding = tuple(args.padding) # Tuple conversion
    args.resolution_input = (args.resolution_input, args.resolution_input)


def get_args_demo():
    parser = argparse.ArgumentParser(description="Get the arguments for the demo",formatter_class=argparse.RawTextHelpFormatter)
    create_args(parser)
    args = parser.parse_args() # read arguments
    framework_choice(args)
    args_treatement(args)
    return args