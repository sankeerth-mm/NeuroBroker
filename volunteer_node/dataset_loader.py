import os
import csv
import zipfile
from pathlib import Path
from typing import Tuple, Optional
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image

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
        
        # Discover class folders
        classes = sorted([d.name for d in partition_dir.iterdir() if d.is_dir() and not d.name.startswith(".")])
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}
        
        for cls_name in classes:
            c_dir = partition_dir / cls_name
            target_idx = self.class_to_idx[cls_name]
            for img_path in c_dir.iterdir():
                if img_path.is_file() and img_path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp'):
                    self.samples.append((img_path, target_idx))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, target = self.samples[idx]
        img = Image.open(img_path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, target


class DatasetLoader:
    @staticmethod
    def create_dataloader(partition_path: Path, batch_size: int = 32) -> Tuple[DataLoader, int]:
        """
        Extracts partition if zipped and returns (DataLoader, total_samples).
        """
        extract_dir = partition_path
        if partition_path.is_file() and partition_path.suffix == ".zip":
            extract_dir = partition_path.parent / f"extracted_{partition_path.stem}"
            extract_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(partition_path, "r") as z:
                z.extractall(extract_dir)
                
        if partition_path.suffix == ".csv" or (isinstance(extract_dir, Path) and extract_dir.is_file() and extract_dir.suffix == ".csv"):
            csv_target = partition_path if partition_path.suffix == ".csv" else extract_dir
            ds = CSVTabularDataset(csv_target)
        else:
            ds = LocalPartitionImageDataset(extract_dir)
            
        loader = DataLoader(ds, batch_size=batch_size, shuffle=True, drop_last=False)
        return loader, len(ds)

dataset_loader = DatasetLoader()
