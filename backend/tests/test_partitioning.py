import pytest
import tempfile
import zipfile
import csv
from pathlib import Path
from backend.app.partitioning.stratified import stratified_partitioner
from backend.app.partitioning.non_iid_detector import non_iid_detector

def test_non_iid_entropy_calculation():
    balanced_dist = {"0": 100, "1": 100, "2": 100, "3": 100}
    is_skewed, msg = non_iid_detector.is_skewed(balanced_dist)
    assert is_skewed is False
    
    imbalanced_dist = {"0": 1000, "1": 20, "2": 10, "3": 5}
    is_skewed, msg = non_iid_detector.is_skewed(imbalanced_dist)
    assert is_skewed is True

def test_stratified_csv_partitioning():
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test_data.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["f1", "f2", "label"])
            for _ in range(50):
                writer.writerow([1.0, 2.0, "cat"])
                writer.writerow([3.0, 4.0, "dog"])
                
        weights = [0.5, 0.5]
        partitions = stratified_partitioner.partition_csv_dataset(
            csv_file_path=csv_path,
            label_column="label",
            job_id=999,
            partition_weights=weights,
            output_base_dir=Path(tmpdir)
        )
        assert len(partitions) == 2
        assert partitions[0]["sample_count"] == 50
        assert partitions[1]["sample_count"] == 50
        assert partitions[0]["class_distribution"]["cat"] == 25
        assert partitions[0]["class_distribution"]["dog"] == 25
