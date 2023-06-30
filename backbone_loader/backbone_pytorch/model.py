"""
Define all the models.

Keys of EASY_SPECS/BRAIN_RESNET12_SPECS/BRAIN_RESNET9_SPECS : name of the implemented model
attrributes : keywords arguments passed to the corresponding model

available models :
EASY : 
easy_resnet12_small, easy_resnet12, easy_resnet12_tiny
BRAIN : 

resnet9 :
"brain_resnet9_small", "brain_resnet9", "brain_resnet9_tiny", "brain_resnet9_small_strided", "brain_resnet9_strided", 
"brain_resnet9_tiny_strided", 

resnet12 :
"brain_resnet12_small", "brain_resnet12", "brain_resnet12_tiny", "brain_resnet12_small_strided"
"brain_resnet12_strided", "brain_resnet12_tiny_strided"

"""
import torch
from backbone_loader.backbone_pytorch.resnet12 import ResNet12
from backbone_loader.backbone_pytorch.resnet12_brain import ResNet12Brain, ResNet9
EASY_SPECS = {
    "easy_resnet12_small": {
        "feature_maps": 45,
        "num_classes": 64,
    },
    "easy_resnet12": {
        "feature_maps": 64,
        "num_classes": 64,
    },
    "easy_resnet12_tiny": {
        "feature_maps": 32,
        "num_classes": 64,
    },
}

# ------------------ BUILT - IN CONFIGS -----------------------------
EASY_SPECS = {
    "easy_resnet12_small": {
        "feature_maps": 45,
        "num_classes": 64,
    },
    "easy_resnet12": {
        "feature_maps": 64,
        "num_classes": 64,
    },
    "easy_resnet12_tiny": {
        "feature_maps": 32,
        "num_classes": 64,
    },
}


BRAIN_RESNET12_SPECS = {
    "brain_resnet12_small": {
        "feature_maps": 45,
    },
    "brain_resnet12": {
        "feature_maps": 64,
    },
    "brain_resnet12_tiny": {
        "feature_maps": 32,
    },
    "brain_resnet12_small_strided": {"feature_maps": 45, "use_strides": True},
    "brain_resnet12_strided": {
        "feature_maps": 64,
        "use_strides": True,
    },
    "brain_resnet12_tiny_strided": {
        "feature_maps": 32,
        "use_strides": True,
    },
}

BRAIN_RESNET9_SPECS = {
    "brain_resnet9_small": {
        "feature_maps": 45,
    },
    "brain_resnet9": {
        "feature_maps": 64,
    },
    "brain_resnet9_tiny": {
        "feature_maps": 32,
    },
    "brain_resnet9_small_strided": {"feature_maps": 45, "use_strides": True},
    "brain_resnet9_strided": {
        "feature_maps": 64,
        "use_strides": True,
    },
    "brain_resnet9_tiny_strided": {
        "feature_maps": 32,
        "use_strides": True,
    },
}
# ------------------ MODEL FROM PYTORCH HUB -----------------------------
# NOTE :
# we do not delete the last convolutional layer, wich correspond to classification, and can induce
# less performance in few-shot / more consumtion.


MODEL_LOC = {
    "mobilenet_v2": "pytorch/vision:v0.10.0",
    "mobilenet_v3_small": "pytorch/vision:v0.10.0",
    "mobilenet_v3_large": "pytorch/vision:v0.10.0",
    "mnasnet0_5": "pytorch/vision:v0.10.0",
    "mnasnet0_75": "pytorch/vision:v0.10.0",
    "mnasnet1_0": "pytorch/vision:v0.10.0",
    "inception_v3": "pytorch/vision:v0.10.0",
    "googlenet": "pytorch/vision:v0.10.0",
    "densenet121": "pytorch/vision:v0.10.0",
    "squeezenet1_1": "pytorch/vision:v0.10.0",
    "shufflenet_v2_x0_5": "pytorch/vision:v0.10.0",
    "shufflenet_v2_x1_0": "pytorch/vision:v0.10.0",
    "efficientnet_b0": "pytorch/vision:v0.10.0",
    "nvidia_efficientnet_b0": "NVIDIA/DeepLearningExamples:torchhub",
    "nvidia_gpunet": "NVIDIA/DeepLearningExamples:torchhub",
}
# github model may require specific version of package (torch for exemple) to work
# <repo_owner/repo_name[:ref]> with an optional ref (a tag or a branch).

# how to get the pretrained weight (pytorch hub only)
MODEL_SPECS = {
    "pretrained": {"pretrained": True},
    "random_init": {"pretrained": False},
    "mobilenet_v2_imagenet": {"weights": "MobileNet_V2_Weights.IMAGENET1K_V2"},
    "mobilenet_v3_small_imagenet": {
        "weights": "MobileNet_V3_Small_Weights.IMAGENET1K_V1"
    },
    "mobilenet_v3_large_imagenet": {
        "weights": "MobileNet_V3_Large_Weights.IMAGENET1K_V2"
    },
    "mnasnet0_5_imagenet": {"weights": "MNASNet0_5_Weights.IMAGENET1K_V1"},
    "mnasnet0_75_imagenet": {"weights": "MNASNet0_75_Weights.IMAGENET1K_V1"},
    "mnasnet1_0_imagenet": {"weights": "MNASNet1_0_Weights.IMAGENET1K_V1"},
}


def load_model_weights(
    model, path, device=None, verbose=False, raise_error_incomplete=True
):
    """
    load the weight given by the path
    if the weight is not correct, raise an errror
    if the weight is not correct, may have no loading at all
        args:
            model(torch.nn.Module) : model on wich the weights should be loaded
            path(...) : a file-like object (path of the weights)
            device(torch.device) : the device on wich the weights should be loaded (optional)
    """
    pretrained_dict = torch.load(path, map_location=device)
    model_dict = model.state_dict()
    # pretrained_dict = {k: v for k, v in pretrained_dict.items() if k in model_dict}
    new_dict = {}
    for k, weight in pretrained_dict.items():
        if k in model_dict:
            if verbose:
                print(f"loading weight name : {k}", flush=True)

            if "bn" in k:
                new_dict[k] = weight.to(torch.float16)
            else:
                new_dict[k] = weight.to(torch.float16)
        else:
            if raise_error_incomplete:
                raise TypeError("the weights does not correspond to the same model")
            print("weight with name : {k} not loaded (not in model)")
    model_dict.update(new_dict)
    model.load_state_dict(model_dict)


def load_model_pytorch_hub(model_name, model_spec_name, device="cpu"):
    """

    load a model. currently only pytorch_hub keyword supported : pretrained and weights
    model_spec_name : should be a key of MODEL_SPECS
    """
    assert model_spec_name in MODEL_SPECS.keys(), "model spec not hardcoded"

    model_kwargs = MODEL_SPECS[model_spec_name]
    model = torch.hub.load(MODEL_LOC[model_name], model_name, **model_kwargs)
    model.to(device)

    return model


def get_model(model_name, model_spec, device="cpu"):
    """
    get a model from pytorch_hub or from custom arch, using hardcoded specifications
    model_name : name of the model. Should either be "easy_resnet12_"+(small_cifar/cifar/tiny_cifar) or a key of MODEL_LOC
    model_spec : either path to weight for easy_resnet12 or key of MODEL_SPECS for pytorch hub
    """

    if model_name.find("easy_resnet12") >= 0:  # if str contains the model
        model = ResNet12(**EASY_SPECS[model_name]).to(device)
        load_model_weights(model, model_spec, device=device)
    elif model_name.find("brain_resnet12") >= 0:
        model = ResNet12Brain(**BRAIN_RESNET12_SPECS[model_name]).to(device)
        load_model_weights(model, model_spec, device=device)
    elif model_name.find("brain_resnet9") >= 0:
        model = ResNet9(**BRAIN_RESNET9_SPECS[model_name]).to(device)
        load_model_weights(model, model_spec, device=device)
    elif model_name in MODEL_LOC.keys():
        print("model is found in pytorch_hub model specifications")
        model = load_model_pytorch_hub(model_name, model_spec, device=device)
    else:
        raise NotImplementedError(f"model {model_name} is not implemented")
    model.eval()
    return model
