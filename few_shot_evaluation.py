"""
exemple : 
python few_shot_evaluation.py --framework_backbone onnx --path-onnx weight/resnet12_32_32_64.onnx --dataset-path data/cifar-10-batches-py/test_batch
python few_shot_evaluation.py --framework_backbone pytorch --backbone_type easy-resnet12-small-cifar  --dataset-path data/cifar-10-batches-py/test_batch


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

def evaluate_model(backbone,kwargs):
    data = get_dataset_numpy(kwargs.dataset_path)
    num_classes, num_exemples, _, _, _ = np.shape(data)
    # normalization
    data = (data / 255 - np.array([0.485, 0.456, 0.406], dtype=data.dtype)) / np.array(
        [0.229, 0.224, 0.225], dtype=data.dtype
    )
    seconds = time.time()

    features = get_features_numpy(backbone, data, kwargs.batch_size)
    dt = time.time() - seconds

    mean_speed = dt / (num_classes * num_exemples)

    sample_per_class = features.shape[1]
    nshots = kwargs.n_shots
    num_classes = kwargs.num_classes_dataset
    # sample_per_class=600
    classe, index = define_runs(
        kwargs.n_runs,
        kwargs.n_ways,
        nshots,
        kwargs.n_queries,
        num_classes,
        [sample_per_class] * num_classes,
    )
    # cifar10 : 122mb
    # runs : 84kb

    index_shots, index_queries = index[:, :, :nshots], index[:, :, nshots:]
    extracted_shots = features[
        np.stack([classe] * nshots, axis=-1), index_shots
    ]  # compute features corresponding to each experiment
    extracted_queries = features[
        np.stack([classe] * kwargs.n_queries, axis=-1), index_queries
    ]  # compute features corresponding to each experiment

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


def launch_evaluation(kwargs):
    """
    launch a evalution using feature a namespace kwargs, with attributes :
        - backbone_specs
        - dataset_path
        - num_classes_dataset
        - batch_size
        - n_shots
        - n_ways
        - n_queries
        - batch_size_fs
        - classifier_specs

    """
    # from lim_ram import set_limit
    backbone = get_model(kwargs.backbone_specs)
    

    return evaluate_model(backbone,kwargs)

    


if __name__ == "__main__":
    # set_limit(500*1024*1024)#simulate the memmory limitation of the pynk
    mean, std, mean_speed = launch_evaluation(get_args_evaluation())
    print(f"perf : {mean}, +-{std}")
    print(f"avg speed  : {mean_speed} s")
