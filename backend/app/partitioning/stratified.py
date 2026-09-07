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
        
        # Discover classes and files
        class_files: Dict[str, List[Path]] = defaultdict(list)
        for entry in extracted_dataset_dir.iterdir():
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
