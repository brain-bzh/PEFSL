"""
"""
import time
import numpy as np

# from memory_profiler import profile
from args import get_args_evaluation
from performance_evaluation.few_shot_eval import get_features_numpy
from performance_evaluation.dataset_numpy import get_dataset_numpy
from backbone_loader.backbone_loader import get_model
from performance_evaluation.few_shot_eval import (
    define_runs,
)
from few_shot_model.few_shot_model import FewShotModel

# @profile#comment/uncoment and flag -m memory_profiler after python


def evaluate_model(backbone, kwargs: dict):
    assert kwargs.sample_per_class % kwargs.batch_size == 0

    data = get_dataset_numpy(kwargs.dataset_path)  #

    num_classes_data, num_exemples_data, h, w, c = np.shape(data)

    # check compatibility of arguments
    assert num_classes_data >= kwargs.num_classes
    assert num_exemples_data >= kwargs.sample_per_class

    # subset of the data if needed
    data = data[0 : kwargs.num_classes, 0 : kwargs.sample_per_class, :, :, :]

    # normalization (assume the backbone used miniimagnet normalisation during training)
    data = (data / 255 - np.array([0.485, 0.456, 0.406], dtype=data.dtype)) / np.array(
        [0.229, 0.224, 0.225], dtype=data.dtype
    )
    seconds = time.time()

    features = get_features_numpy(backbone, data, kwargs.batch_size)
    dt_inference = time.time() - seconds

    total_samples = kwargs.num_classes * kwargs.sample_per_class
    mean_speed = dt_inference / total_samples

    # sample_per_class=600
    classe, index = define_runs(
        kwargs.n_runs,
        kwargs.n_ways,
        kwargs.n_shots,
        kwargs.n_queries,
        kwargs.num_classes,
        [kwargs.sample_per_class] * kwargs.num_classes,
    )
    # cifar10 : 122mb
    # runs : 84kb

    index_shots, index_queries = (
        index[:, :, : kwargs.n_shots],
        index[:, :, kwargs.n_shots :],
    )
    extracted_shots = features[
        np.stack([classe] * kwargs.n_shots, axis=-1), index_shots
    ]  # compute features corresponding to each experiment shots
    extracted_queries = features[
        np.stack([classe] * kwargs.n_queries, axis=-1), index_queries
    ]  # compute features corresponding to each experiment queries

    mean_feature = np.mean(extracted_shots, axis=(1, 2))

    bs = kwargs.batch_size_fs
    fs_model = FewShotModel(kwargs.classifier_specs)
    perf = []

    for i in range(kwargs.n_runs // bs):
        # view, no data
        batch_q = extracted_queries[i * bs : (i + 1) * bs]
        batch_shot = extracted_shots[i * bs : (i + 1) * bs]
        batch_mean_feature = mean_feature[i * bs : (i + 1) * bs]

        predicted_class, _ = fs_model.predict_class_batch(
            batch_q, batch_shot, batch_mean_feature
        )
        perf.append(
            np.mean(predicted_class == np.expand_dims(np.arange(0, 5), axis=(0, 2)))
        )
    return np.mean(perf), np.std(perf), mean_speed


def launch_evaluation(kwargs: dict):
    """
    launch a evalution using feature a namespace kwargs, with attributes :
        - backbone_specs
        - dataset_path
        - num_classes_dataset
        - batch_size
        - num_classes
        - sample_per_class
        - n_shots
        - n_ways
        - n_queries
        - batch_size_fs
        - classifier_specs

    """
    # from lim_ram import set_limit
    backbone = get_model(kwargs.backbone_specs)

    return evaluate_model(backbone, kwargs)


if __name__ == "__main__":
    # set_limit(500*1024*1024)#simulate the memmory limitation of the pynk
    mean, std, mean_speed = launch_evaluation(get_args_evaluation())
    print(f"perf : {mean}, +-{std}")
    print(f"avg speed  : {mean_speed} s")
