import os
import csv
import zipfile
from pathlib import Path
from typing import Tuple, Optional
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import numpy as np
from volunteer_node.logger import logger

class CSVTabularDataset(Dataset):
    def __init__(self, csv_file: Path, label_column: Optional[str] = None):
        self.rows = []
        self.labels = []
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for r in reader:
                if not r:
                    continue
                try:
                    # Last column as label by default, preceding as float features
                    feats = [float(x) for x in r[:-1]]
                    lbl = int(float(r[-1]))
                    self.rows.append(feats)
                    self.labels.append(lbl)
                except ValueError:
                    continue
                    
        self.features_tensor = torch.tensor(self.rows, dtype=torch.float32)
        self.labels_tensor = torch.tensor(self.labels, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.features_tensor[idx], self.labels_tensor[idx]


class LocalPartitionImageDataset(Dataset):
    def __init__(self, partition_dir: Path, transform=None):
        self.samples = []
        self.transform = transform or transforms.Compose([
            transforms.Grayscale(num_output_channels=1),
            transforms.Resize((28, 28)),
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,))
        ])
        
        # Unwrap nested single directory wrappers if present
        current_dir = partition_dir
        while True:
            children = [d for d in current_dir.iterdir() if not d.name.startswith(".")]
            if len(children) == 1 and children[0].is_dir():
                current_dir = children[0]
            else:
                break

        # Discover class folders
        classes = sorted([d.name for d in current_dir.iterdir() if d.is_dir() and not d.name.startswith(".")])
        if classes:
            self.class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}
            for cls_name in classes:
                c_dir = current_dir / cls_name
                target_idx = self.class_to_idx[cls_name]
                for img_path in c_dir.rglob("*"):
                    if img_path.is_file() and img_path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp', '.npy'):
                        self.samples.append((img_path, target_idx))
        else:
            self.class_to_idx = {"default": 0}
            for img_path in current_dir.rglob("*"):
                if img_path.is_file() and img_path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp', '.npy'):
                    self.samples.append((img_path, 0))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, target = self.samples[idx]
        if img_path.suffix.lower() == ".npy":
            arr = np.load(img_path)
            arr = np.squeeze(arr)
            
            if arr.ndim == 0 or arr.size == 0:
                return torch.zeros(1, 28, 28), target

            if arr.ndim == 1:
                return torch.from_numpy(arr).float(), target
            elif arr.ndim == 2:
                arr_norm = ((arr - arr.min()) / (arr.max() - arr.min() + 1e-8) * 255).astype(np.uint8)
                img = Image.fromarray(arr_norm, mode="L").convert("RGB")
                if self.transform:
                    img = self.transform(img)
                return img, target
            elif arr.ndim == 3:
                if arr.shape[0] in (1, 3, 4) and arr.shape[0] < arr.shape[1]:
                    arr = np.transpose(arr, (1, 2, 0))
                
                if arr.shape[-1] == 1:
                    arr = arr[:, :, 0]
                    arr_norm = ((arr - arr.min()) / (arr.max() - arr.min() + 1e-8) * 255).astype(np.uint8)
                    img = Image.fromarray(arr_norm, mode="L").convert("RGB")
                    if self.transform:
                        img = self.transform(img)
                    return img, target
                elif arr.shape[-1] in (3, 4):
                    arr_norm = ((arr - arr.min()) / (arr.max() - arr.min() + 1e-8) * 255).astype(np.uint8)
                    mode = "RGBA" if arr.shape[-1] == 4 else "RGB"
                    img = Image.fromarray(arr_norm, mode=mode).convert("RGB")
                    if self.transform:
                        img = self.transform(img)
                    return img, target
                else:
                    return torch.from_numpy(arr.flatten()).float(), target
            else:
                return torch.from_numpy(arr.flatten()).float(), target
        else:
            img = Image.open(img_path).convert("RGB")
            if self.transform:
                img = self.transform(img)
        return img, target


class NumpyFeatureDataset(Dataset):
    """
    Dataset for pre-extracted feature datasets saved as paired .npy files:
      - features_*.npy (shape [N, 48, 256] or [N, D])
      - labels_*.npy   (shape [N])
    Also handles single multi-sample .npy files or paired numpy arrays.
    """
    def __init__(self, extract_dir: Path, transform=None):
        self.samples = []
        self.transform = transform
        
        npy_files = list(extract_dir.rglob("*.npy"))
        feature_files = [f for f in npy_files if "feature" in f.name.lower()]
        label_files = [f for f in npy_files if "label" in f.name.lower()]
        
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
                            for i in range(len(f_data)):
                                self.samples.append((f_data[i], int(l_data[i])))
                    except Exception as e:
                        logger.warning(f"Error loading paired npy files {f_file.name} / {matching_lbl.name}: {e}")
        elif npy_files:
            for f_file in npy_files:
                if "label" in f_file.name.lower():
                    continue
                try:
                    data = np.load(f_file)
                    if data.ndim >= 2:
                        for i in range(len(data)):
                            self.samples.append((data[i], 0))
                    else:
                        self.samples.append((data, 0))
                except Exception as e:
                    logger.warning(f"Error loading npy file {f_file.name}: {e}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        feat, target = self.samples[idx]
        if isinstance(feat, np.ndarray):
            if feat.ndim == 1:
                tensor_feat = torch.from_numpy(feat).float()
            elif feat.ndim == 2:
                tensor_feat = torch.from_numpy(feat).float().unsqueeze(0)
            elif feat.ndim == 3:
                if feat.shape[0] in (1, 3, 4) and feat.shape[0] < feat.shape[1]:
                    tensor_feat = torch.from_numpy(feat).float()
                elif feat.shape[-1] in (1, 3, 4):
                    tensor_feat = torch.from_numpy(np.transpose(feat, (2, 0, 1))).float()
                else:
                    tensor_feat = torch.from_numpy(feat).float()
            else:
                tensor_feat = torch.from_numpy(feat.flatten()).float()
        else:
            tensor_feat = torch.tensor(feat, dtype=torch.float32)

        return tensor_feat, target


def variable_length_collate_fn(batch):
    """
    Custom PyTorch DataLoader collate_fn that dynamically pads variable-length 1D
    feature vectors (e.g. MFCC/audio features [1269] vs [1268]) or multi-dimensional
    tensors to equal dimensions within each mini-batch before PyTorch attempts batch stacking.
    """
    items, targets = zip(*batch)
    
    if isinstance(items[0], torch.Tensor) and items[0].ndim == 1:
        max_len = max(item.shape[0] for item in items)
        padded_items = []
        for item in items:
            if item.shape[0] < max_len:
                pad_size = max_len - item.shape[0]
                padded = torch.nn.functional.pad(item, (0, pad_size), value=0.0)
                padded_items.append(padded)
            elif item.shape[0] > max_len:
                padded_items.append(item[:max_len])
            else:
                padded_items.append(item)
        stacked_data = torch.stack(padded_items, dim=0)
    elif isinstance(items[0], torch.Tensor):
        shapes = [item.shape for item in items]
        if any(s != shapes[0] for s in shapes):
            max_shape = [max(s[i] for s in shapes) for i in range(len(shapes[0]))]
            padded_items = []
            for item in items:
                pad_args = []
                for i in range(len(item.shape) - 1, -1, -1):
                    pad_diff = max_shape[i] - item.shape[i]
                    pad_args.extend([0, pad_diff])
                padded = torch.nn.functional.pad(item, pad_args, value=0.0)
                padded_items.append(padded)
            stacked_data = torch.stack(padded_items, dim=0)
        else:
            stacked_data = torch.stack(items, dim=0)
    else:
        stacked_data = torch.tensor(items)

    stacked_targets = torch.tensor(targets, dtype=torch.long)
    return stacked_data, stacked_targets


class DatasetLoader:
    @staticmethod
    def create_dataloader(partition_path: Path, batch_size: int = 32) -> Tuple[DataLoader, int]:
        """
        Extracts a ZIP partition or reads a CSV partition and returns
        (DataLoader, total_samples). Performs diagnostic validation before PyTorch DataLoader creation.
        """
        if not partition_path.exists():
            raise FileNotFoundError(f"Dataset partition path does not exist: {partition_path}")

        file_size_bytes = partition_path.stat().st_size if partition_path.is_file() else 0
        logger.info(f"[DATASET_LOADER] Loading partition from: {partition_path} (File size: {file_size_bytes} bytes)")

        extract_dir = partition_path
        is_zip_partition = partition_path.is_file() and zipfile.is_zipfile(partition_path)
        if is_zip_partition:
            extract_dir = partition_path.parent / f"extracted_{partition_path.stem}"
            extract_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(partition_path, "r") as z:
                z.extractall(extract_dir)

        if partition_path.is_file() and not is_zip_partition:
            csv_target = partition_path
            ds = CSVTabularDataset(csv_target)
        else:
            npy_ds = NumpyFeatureDataset(extract_dir)
            if len(npy_ds) > 0:
                ds = npy_ds
            else:
                ds = LocalPartitionImageDataset(extract_dir)

        total_samples = len(ds)
        logger.info(f"[DATASET_LOADER] Discovered {total_samples} samples in partition {partition_path.name}")

        if total_samples == 0:
            discovered_structure = []
            if extract_dir.is_dir():
                for sub in extract_dir.rglob("*"):
                    discovered_structure.append(str(sub.relative_to(extract_dir)))
            
            diagnostic_msg = (
                f"[DATASET_ERROR] Partition '{partition_path}' contains 0 valid samples (num_samples=0).\n"
                f"  - Partition File Exists: {partition_path.exists()}\n"
                f"  - Size: {file_size_bytes} bytes\n"
                f"  - Is Zip Archive: {is_zip_partition}\n"
                f"  - Extracted Path: {extract_dir}\n"
                f"  - Discovered Contents ({len(discovered_structure)} items): {discovered_structure[:15]}"
            )
            logger.error(diagnostic_msg)
            raise ValueError(f"Invalid dataset partition at {partition_path}: Found 0 valid training samples (num_samples=0). Cannot create PyTorch DataLoader.")

        should_shuffle = total_samples > 0
        loader = DataLoader(
            ds,
            batch_size=batch_size,
            shuffle=should_shuffle,
            drop_last=False,
            collate_fn=variable_length_collate_fn
        )
        return loader, total_samples

dataset_loader = DatasetLoader()
