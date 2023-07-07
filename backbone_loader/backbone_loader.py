"""
get the backbone with the specified framework, using argument from

-> input : numpy or torch tensor img (preprocessed)
-> output : numpy img
"""


def get_model(model_specs: dict):
    """
    get the model specified in input
    args :
        - model_specs
        - device
    returns :
        resnet(torch.nn.Module) :
        neural network corespounding to parameters
            takes a batch
    """

    if model_specs["type"] == "pytorch":
        from backbone_loader.backbone_loader_pytorch import TorchBatchModelWrapper

        device = model_specs["device"]
        model_name = model_specs["model_name"]
        weight = model_specs["weight"]
        use_strides = model_specs["use_strides"]
        return TorchBatchModelWrapper(model_name, weight, use_strides, device=device)
    elif model_specs["type"] == "tensil":
        from backbone_loader.backbone_tensil import BackboneTensilWrapper

        return BackboneTensilWrapper(
            model_specs["overlay"],
            model_specs["path_tmodel"],
        )
    elif model_specs["type"] == "onnx":
        from backbone_loader.backbone_onnx import BackboneOnnxWrapper

        return BackboneOnnxWrapper(model_specs["path_onnx"])

    else:
        raise UserWarning("model type=" + model_specs["type"] + "is not defined")
