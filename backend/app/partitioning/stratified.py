import os
import io
import shutil
import zipfile
import random
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from backend.app.config import settings
from backend.app.security.checksum import compute_sha256

class StratifiedPartitioner:
    @staticmethod
    def partition_image_dataset(
        extracted_dataset_dir: Path,
        job_id: int,
        partition_weights: List[float],
        output_base_dir: Path = settings.PARTITIONS_DIR
    ) -> List[Dict[str, Any]]:
        """
        Partitions an image classification directory structure (class_name/img1.jpg, ...)
        into K stratified sub-dataset zip packages according to partition_weights.
        """
        K = len(partition_weights)
        if K == 0:
            return []
        
        # Normalize weights
        total_w = sum(partition_weights)
        norm_weights = [w / total_w for w in partition_weights]
        
        # First, unwrap single top-level directory wrapper if present (e.g., dataset_archive/dataset_name/class_dirs...)
        root_dir = extracted_dataset_dir
        while True:
            children = [c for c in root_dir.iterdir() if not c.name.startswith(".")]
            if len(children) == 1 and children[0].is_dir():
                root_dir = children[0]
            else:
                break

        # Check if dataset contains multi-sample .npy feature/label files
        npy_files = list(root_dir.rglob("*.npy"))
        feature_files = [f for f in npy_files if "feature" in f.name.lower()]
        label_files = [f for f in npy_files if "label" in f.name.lower()]
        if (feature_files and label_files) or any(f.parent == root_dir for f in npy_files if not f.name.startswith(".")):
            npy_manifests = StratifiedPartitioner.partition_npy_dataset(
                extracted_dataset_dir=root_dir,
                job_id=job_id,
                partition_weights=partition_weights,
                output_base_dir=output_base_dir
            )
            if npy_manifests:
                return npy_manifests



        # Discover classes and files
        class_files: Dict[str, List[Path]] = defaultdict(list)
        for entry in root_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith("."):
                class_name = entry.name
                for file_path in entry.rglob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp', '.npy'):
                        class_files[class_name].append(file_path)
            elif entry.is_file() and entry.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp', '.npy'):
                # Single directory fallback
                class_files["default"].append(entry)
        
        # Allocate files per class proportionally
        partitions_data: List[Dict[str, List[Path]]] = [defaultdict(list) for _ in range(K)]
        
        for class_name, files in class_files.items():
            # Shuffle deterministically or randomly
            shuffled_files = list(files)
            random.shuffle(shuffled_files)
            
            total_class_samples = len(shuffled_files)
            start_idx = 0
            
            for k in range(K):
                if k == K - 1:
                    # Last partition gets remaining samples
                    allocated = shuffled_files[start_idx:]
                else:
                    count = int(round(norm_weights[k] * total_class_samples))
                    end_idx = min(start_idx + count, total_class_samples)
                    allocated = shuffled_files[start_idx:end_idx]
                    start_idx = end_idx
                
                partitions_data[k][class_name].extend(allocated)

        # Tiny datasets can exhaust a class before the final partition even
        # when the dataset has enough total samples for every selected worker.
        # Move whole samples from the largest partitions into empty partitions
        # so workers never receive an unusable zero-sample archive.
        partition_totals = [
            sum(len(files) for files in partition.values())
            for partition in partitions_data
        ]
        for empty_index, empty_total in enumerate(partition_totals):
            if empty_total or sum(partition_totals) < K:
                continue
            donor_index = max(
                (index for index, total in enumerate(partition_totals) if total > 1),
                key=lambda index: partition_totals[index],
                default=None,
            )
            if donor_index is None:
                break
            donor_classes = [
                name for name, files in partitions_data[donor_index].items() if files
            ]
            donor_class = max(
                donor_classes,
                key=lambda name: len(partitions_data[donor_index][name]),
            )
            moved_file = partitions_data[donor_index][donor_class].pop()
            partitions_data[empty_index][donor_class].append(moved_file)
            partition_totals[donor_index] -= 1
            partition_totals[empty_index] += 1
        
        # Build Zip files for each partition
        partition_manifests = []
        job_partition_dir = output_base_dir / f"job_{job_id}"
        job_partition_dir.mkdir(parents=True, exist_ok=True)
        
        for k in range(K):
            partition_zip_path = job_partition_dir / f"partition_{k}.zip"
            class_dist = {}
            total_samples = 0
            
            with zipfile.ZipFile(partition_zip_path, "w", zipfile.ZIP_DEFLATED) as pzip:
                for class_name, file_list in partitions_data[k].items():
                    class_dist[class_name] = len(file_list)
                    total_samples += len(file_list)
                    for fpath in file_list:
                        # Arcname: class_name / filename
                        arcname = f"{class_name}/{fpath.name}"
                        pzip.write(fpath, arcname)
            
            checksum = compute_sha256(partition_zip_path)
            partition_manifests.append({
                "partition_index": k,
                "file_path": str(partition_zip_path),
                "checksum_sha256": checksum,
                "sample_count": total_samples,
                "class_distribution": class_dist,
            })
            
        return partition_manifests

    @staticmethod
    def partition_npy_dataset(
        extracted_dataset_dir: Path,
        job_id: int,
        partition_weights: List[float],
        output_base_dir: Path = settings.PARTITIONS_DIR
    ) -> List[Dict[str, Any]]:
        import numpy as np

        K = len(partition_weights)
        if K == 0:
            return []

        total_w = sum(partition_weights)
        norm_weights = [w / total_w for w in partition_weights]

        root_dir = extracted_dataset_dir
        while True:
            children = [c for c in root_dir.iterdir() if not c.name.startswith(".")]
            if len(children) == 1 and children[0].is_dir():
                root_dir = children[0]
            else:
                break

        npy_files = list(root_dir.rglob("*.npy"))
        feature_files = sorted([f for f in npy_files if "feature" in f.name.lower()])
        label_files = sorted([f for f in npy_files if "label" in f.name.lower()])

        all_features = []
        all_labels = []

        if feature_files and label_files:
            for f_file in feature_files:
                suffix = ""
                for s in ["train", "test", "val", "validation"]:
                    if s in f_file.name.lower():
                        suffix = s
                        break
                matching_lbl = None
                for l_file in label_files:
                    if suffix and suffix in l_file.name.lower():
                        matching_lbl = l_file
                        break
                if not matching_lbl and label_files:
                    matching_lbl = label_files[0]

                if matching_lbl:
                    try:
                        f_data = np.load(f_file)
                        l_data = np.load(matching_lbl)
                        if len(f_data) == len(l_data):
                            all_features.append(f_data)
                            all_labels.append(l_data)
                    except Exception:
                        pass
        elif npy_files:
            for f_file in npy_files:
                if "label" in f_file.name.lower():
                    continue
                try:
                    data = np.load(f_file)
                    if data.ndim >= 2:
                        all_features.append(data)
                        all_labels.append(np.zeros(len(data), dtype=np.int64))
                except Exception:
                    pass

        if not all_features:
            return []

        X = np.concatenate(all_features, axis=0)
        y = np.concatenate(all_labels, axis=0)
        total_samples = len(y)

        class_indices = defaultdict(list)
        for idx, lbl in enumerate(y):
            class_indices[int(lbl)].append(idx)

        partition_indices: List[List[int]] = [[] for _ in range(K)]

        for cls, idxs in class_indices.items():
            shuffled = list(idxs)
            random.shuffle(shuffled)
            n_cls = len(shuffled)
            start = 0
            for k in range(K):
                if k == K - 1:
                    allocated = shuffled[start:]
                else:
                    count = int(round(norm_weights[k] * n_cls))
                    end = min(start + count, n_cls)
                    allocated = shuffled[start:end]
                    start = end
                partition_indices[k].extend(allocated)

        partition_manifests = []
        job_partition_dir = output_base_dir / f"job_{job_id}"
        job_partition_dir.mkdir(parents=True, exist_ok=True)

        for k in range(K):
            idxs = partition_indices[k]
            if len(idxs) == 0 and total_samples >= K:
                largest_k = max(range(K), key=lambda i: len(partition_indices[i]))
                if len(partition_indices[largest_k]) > 1:
                    idxs = [partition_indices[largest_k].pop()]
                    partition_indices[k] = idxs

            X_k = X[idxs] if len(idxs) > 0 else X[:0]
            y_k = y[idxs] if len(idxs) > 0 else y[:0]

            partition_zip_path = job_partition_dir / f"partition_{k}.zip"

            temp_feat_file = job_partition_dir / f"temp_features_{k}.npy"
            temp_lbl_file = job_partition_dir / f"temp_labels_{k}.npy"
            np.save(temp_feat_file, X_k)
            np.save(temp_lbl_file, y_k)

            class_dist = defaultdict(int)
            for lbl in y_k:
                class_dist[str(int(lbl))] += 1

            with zipfile.ZipFile(partition_zip_path, "w", zipfile.ZIP_DEFLATED) as pzip:
                pzip.write(temp_feat_file, "features_train.npy")
                pzip.write(temp_lbl_file, "labels_train.npy")

            temp_feat_file.unlink(missing_ok=True)
            temp_lbl_file.unlink(missing_ok=True)

            checksum = compute_sha256(partition_zip_path)
            partition_manifests.append({
                "partition_index": k,
                "file_path": str(partition_zip_path),
                "checksum_sha256": checksum,
                "sample_count": len(idxs),
                "class_distribution": dict(class_dist),
            })

        return partition_manifests

    @staticmethod
    def partition_csv_dataset(
        csv_file_path: Path,
        label_column: str,
        job_id: int,
        partition_weights: List[float],
        output_base_dir: Path = settings.PARTITIONS_DIR
    ) -> List[Dict[str, Any]]:
        """
        Partitions a CSV dataset stratifying on label_column according to partition_weights.
        """
        K = len(partition_weights)
        total_w = sum(partition_weights)
        norm_weights = [w / total_w for w in partition_weights]
        
        # Read CSV
        with open(csv_file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)
        
        if not fieldnames or label_column not in fieldnames:
            label_column = fieldnames[-1] # Fallback to last column
            
        class_rows = defaultdict(list)
        for row in rows:
            label = str(row.get(label_column, "unknown"))
            class_rows[label].append(row)
            
        partitions_rows: List[List[Dict[str, Any]]] = [[] for _ in range(K)]
        
        for label, rlist in class_rows.items():
            shuffled = list(rlist)
            random.shuffle(shuffled)
            total = len(shuffled)
            start_idx = 0
            
            for k in range(K):
                if k == K - 1:
                    allocated = shuffled[start_idx:]
                else:
                    count = int(round(norm_weights[k] * total))
                    end_idx = min(start_idx + count, total)
                    allocated = shuffled[start_idx:end_idx]
                    start_idx = end_idx
                partitions_rows[k].extend(allocated)
                
        partition_manifests = []
        job_partition_dir = output_base_dir / f"job_{job_id}"
        job_partition_dir.mkdir(parents=True, exist_ok=True)
        
        for k in range(K):
            partition_csv_path = job_partition_dir / f"partition_{k}.csv"
            class_dist = defaultdict(int)
            for row in partitions_rows[k]:
                class_dist[str(row.get(label_column, "unknown"))] += 1
                
            with open(partition_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(partitions_rows[k])
                
            checksum = compute_sha256(partition_csv_path)
            partition_manifests.append({
                "partition_index": k,
                "file_path": str(partition_csv_path),
                "checksum_sha256": checksum,
                "sample_count": len(partitions_rows[k]),
                "class_distribution": dict(class_dist),
            })
            
        return partition_manifests

stratified_partitioner = StratifiedPartitioner()
