import os
import time

from perf_utils import perf


def test_perf_decorator(tmp_path):
    with perf(name="test", output_dir=str(tmp_path)):
        time.sleep(0.5)
    assert os.path.exists(tmp_path + "test.svg")
