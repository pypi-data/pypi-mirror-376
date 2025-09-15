
from llm_behavior_eval.evaluation_utils.dataset_config import PreprocessConfig


def test_preprocess_config_defaults() -> None:
    defaults = PreprocessConfig()
    assert defaults.max_length == 1024
    assert defaults.gt_max_length == 256
    assert defaults.preprocess_batch_size == 128