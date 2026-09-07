import sys
import os
import zipfile
import importlib.util
from pathlib import Path
from typing import Any
import torch
import torch.nn as nn
from volunteer_node.logger import logger
from volunteer_node.security import sandbox_security

class ModelLoader:
    @staticmethod
    def load_model_from_package(package_path_or_dir: Path) -> nn.Module:
        """
        Dynamically extracts and loads model from model_package zip or directory.
        Looks for model.py defining `build_model() -> nn.Module` or standard class.
        """
        extract_dir = package_path_or_dir
        if package_path_or_dir.is_file() and package_path_or_dir.suffix == ".zip":
            extract_dir = package_path_or_dir.parent / f"extracted_{package_path_or_dir.stem}"
            extract_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(package_path_or_dir, "r") as z:
                z.extractall(extract_dir)
                
        # Find model.py
        model_py_candidates = list(extract_dir.rglob("model.py"))
        if not model_py_candidates:
            raise FileNotFoundError(f"model.py not found in package {package_path_or_dir}")
            
        model_py = model_py_candidates[0]
        module_dir = str(model_py.parent)
        
        # Add to sys.path temporarily
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)
            
        spec = importlib.util.spec_from_file_location("dynamic_user_model", str(model_py))
        if not spec or not spec.loader:
            raise ImportError(f"Could not load module spec for {model_py}")
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, "build_model"):
            model = module.build_model()
        elif hasattr(module, "Net"):
            model = module.Net()
        elif hasattr(module, "Model"):
            model = module.Model()
        else:
            raise AttributeError("model.py must define 'build_model()' or 'Net' class.")
            
        return model

model_loader = ModelLoader()
