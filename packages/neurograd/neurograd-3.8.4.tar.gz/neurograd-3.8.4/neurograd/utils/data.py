from neurograd import Tensor, float32
import numpy as np
from neurograd import xp
from typing import Optional, Union, Any, Dict, List
import random
import os

try:
    import datasets
    from datasets import Dataset as HFDataset, DatasetDict, load_dataset, load_from_disk
    from datasets.utils.logging import disable_progress_bar
    HF_AVAILABLE = True
    # Disable progress bars for cleaner output
    disable_progress_bar()
except ImportError:
    HF_AVAILABLE = False
    HFDataset = None
    DatasetDict = None

# Fallback for image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class Dataset:
    """NeuroGrad Dataset wrapper using HuggingFace datasets backend"""
    
    def __init__(self, X, y, dtype=float32):
        assert len(X) == len(y), "Mismatched input and label lengths"
        if HF_AVAILABLE:
            # Convert to HF dataset for efficient storage and operations
            self._hf_dataset = HFDataset.from_dict({
                'features': X,
                'labels': y
            })
        else:
            # Fallback to simple storage
            self._X = X
            self._y = y
        self.dtype = dtype
        self._length = len(X)

    def __len__(self):
        return self._length

    def __getitem__(self, idx):
        if HF_AVAILABLE:
            item = self._hf_dataset[idx]
            x_data = item['features']
            y_data = item['labels']
        else:
            x_data = self._X[idx]
            y_data = self._y[idx]
        
        return Tensor(x_data, dtype=self.dtype), Tensor(y_data, dtype=self.dtype)

    def __iter__(self):
        for idx in range(len(self)):
            yield self[idx]

    def shuffle(self, seed: Optional[int] = None):
        if HF_AVAILABLE:
            self._hf_dataset = self._hf_dataset.shuffle(seed=seed)
        else:
            # Fallback manual shuffle
            indices = list(range(len(self)))
            rng = random.Random(seed) if seed is not None else random.Random()
            rng.shuffle(indices)
            self._X = [self._X[i] for i in indices]
            self._y = [self._y[i] for i in indices]

    def __repr__(self):
        return f"<Dataset: {len(self)} samples, dtype={self.dtype}>"

    def __str__(self):
        preview_x, preview_y = self[0]
        return (f"Dataset:\n"
                f"  Total samples: {len(self)}\n"
                f"  Input preview: {preview_x}\n"
                f"  Target preview: {preview_y}")


class DataLoader:
    """Efficient DataLoader using HuggingFace datasets backend"""
    
    def __init__(self, dataset: Dataset, batch_size: int = 32,
                 shuffle: bool = True, seed: Optional[int] = None,
                 num_workers: Optional[int] = None,
                 prefetch_batches: int = 2,
                 drop_last: bool = False):
        self.dataset = dataset
        self.batch_size = int(batch_size)
        self.shuffle = shuffle
        self.seed = seed
        self.prefetch_batches = max(0, int(prefetch_batches))
        self.drop_last = bool(drop_last)
        
        # Use HF datasets built-in multiprocessing if available
        if num_workers is None:
            self.num_workers = 1 if not HF_AVAILABLE else min(4, os.cpu_count() or 1)
        else:
            self.num_workers = int(num_workers)

    def __len__(self):
        n = len(self.dataset)
        if self.drop_last:
            return n // self.batch_size
        return (n + self.batch_size - 1) // self.batch_size

    def __getitem__(self, idx):
        """Get a specific batch by index"""
        if idx < 0 or idx >= len(self):
            raise IndexError(f"Batch index {idx} out of range [0, {len(self)})")
        
        start_idx = idx * self.batch_size
        end_idx = min(start_idx + self.batch_size, len(self.dataset))
        
        # Collect batch data
        batch_data = [self.dataset[i] for i in range(start_idx, end_idx)]
        Xs, ys = zip(*batch_data)
        
        # Stack into tensors
        X = Tensor(xp.stack([x.data for x in Xs], axis=0), dtype=Xs[0].dtype)
        y = Tensor(xp.stack([y.data for y in ys], axis=0), dtype=ys[0].dtype)
        return X, y

    def __iter__(self):
        """Iterate over batches efficiently using HF datasets"""
        n = len(self.dataset)
        indices = list(range(n))
        
        if self.shuffle:
            rng = random.Random(self.seed)
            rng.shuffle(indices)
        
        if self.drop_last:
            limit = (n // self.batch_size) * self.batch_size
            indices = indices[:limit]
        
        # Process in batches
        for i in range(0, len(indices), self.batch_size):
            batch_indices = indices[i:i + self.batch_size]
            
            # Load batch efficiently
            batch_data = [self.dataset[idx] for idx in batch_indices]
            Xs, ys = zip(*batch_data)
            
            # Stack into tensors
            X = Tensor(xp.stack([x.data for x in Xs], axis=0), dtype=Xs[0].dtype)
            y = Tensor(xp.stack([y.data for y in ys], axis=0), dtype=ys[0].dtype)
            yield X, y

    def __repr__(self):
        return (f"<DataLoader: {len(self)} batches, "
                f"batch_size={self.batch_size}, "
                f"shuffle={self.shuffle}, seed={self.seed}, "
                f"num_workers={self.num_workers}>")

    def close(self):
        """Compatibility method - HF datasets handle cleanup automatically"""
        pass


class ImageFolder(Dataset):
    """ImageFolder using HuggingFace datasets for efficient image loading"""
    
    def __init__(
        self,
        root: str,
        img_shape: tuple = None,
        img_mode: str = "RGB",
        img_normalize: bool = True,
        img_transform: callable = None,
        target_transform: callable = None,
        img_dtype=xp.float32,
        target_dtype=xp.int64,
        chw: bool = True
    ):
        self.root = root
        self.img_shape = img_shape
        self.img_mode = img_mode
        self.img_normalize = img_normalize
        self.img_transform = img_transform
        self.target_transform = target_transform
        self.img_dtype = img_dtype
        self.target_dtype = target_dtype
        self.chw = chw
        
        # Collect image paths and labels
        self.images = []
        self.targets = []
        self._collect_paths()
        
        # Create class mapping
        self.target_names = sorted(set(self.targets))
        self.target_mapping = {name: i for i, name in enumerate(self.target_names)}
        self.num_classes = len(self.target_names)
        
        # Convert to numeric targets
        numeric_targets = [self.target_mapping[t] for t in self.targets]
        
        if HF_AVAILABLE:
            # Create HF dataset with image paths and labels
            self._hf_dataset = HFDataset.from_dict({
                'image_path': self.images,
                'label': numeric_targets
            })
        else:
            self._images = self.images
            self._targets = numeric_targets

    def _collect_paths(self):
        """Collect image paths and their corresponding labels"""
        IMG_EXTS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tif', '.tiff', '.webp')
        
        for root, _, files in os.walk(self.root):
            for file in files:
                if file.lower().endswith(IMG_EXTS):
                    path = os.path.join(root, file)
                    class_name = os.path.basename(os.path.dirname(path))
                    self.images.append(path)
                    self.targets.append(class_name)

    def _load_image(self, path: str) -> np.ndarray:
        """Load and process image using PIL for compatibility"""
        if PIL_AVAILABLE:
            img = Image.open(path)
            if self.img_mode:
                img = img.convert(self.img_mode)
            
            # Resize if needed
            if self.img_shape:
                img = img.resize((self.img_shape[1], self.img_shape[0]))
            
            # Convert to numpy
            arr = np.array(img)
        else:
            # Fallback: basic loading without PIL
            raise ImportError("PIL is required for image loading. Install with: pip install Pillow")
        
        # Ensure proper dimensions
        if arr.ndim == 2:
            arr = arr[:, :, None]
        
        # Apply custom transforms
        if self.img_transform:
            arr = self._apply_img_transform(arr)
        
        # Channel ordering
        if self.chw and arr.ndim == 3:
            arr = np.transpose(arr, (2, 0, 1))
        
        # Normalize
        if self.img_normalize:
            arr = arr.astype(np.float32) / 255.0
        
        return arr

    def _apply_img_transform(self, arr: np.ndarray) -> np.ndarray:
        """Apply image transformations"""
        if self.img_transform is None:
            return arr
        
        # Try Albumentations-style call
        try:
            out = self.img_transform(image=arr)
            if isinstance(out, dict) and "image" in out:
                return out["image"]
        except (TypeError, AttributeError):
            pass
        
        # Fallback: plain callable
        return self.img_transform(arr)

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx: int):
        if HF_AVAILABLE:
            item = self._hf_dataset[idx]
            img_path = item['image_path']
            target = item['label']
        else:
            img_path = self._images[idx]
            target = self._targets[idx]
        
        # Load and process image
        image = self._load_image(img_path)
        
        # Apply target transform
        if self.target_transform:
            target = self.target_transform(target)
        
        return Tensor(image, dtype=self.img_dtype), Tensor(target, dtype=self.target_dtype)

    def shuffle(self, seed: Optional[int] = None):
        if HF_AVAILABLE:
            self._hf_dataset = self._hf_dataset.shuffle(seed=seed)
        else:
            # Manual shuffle
            indices = list(range(len(self)))
            rng = random.Random(seed)
            rng.shuffle(indices)
            self._images = [self._images[i] for i in indices]
            self._targets = [self._targets[i] for i in indices]

    def __repr__(self):
        shape = None
        if len(self) > 0:
            try:
                image, _ = self[0]
                shape = tuple(image.shape)
            except Exception:
                shape = None
        
        return (f"ImageFolder(root='{self.root}', samples={len(self)}, "
                f"classes={self.num_classes}, shape={shape}, "
                f"img_dtype={self.img_dtype}, target_dtype={self.target_dtype}, "
                f"mode='{self.img_mode}', normalize={self.img_normalize}, chw={self.chw})")

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]


# Utility functions for loading common datasets
def load_hf_dataset(dataset_name: str, split: str = "train", **kwargs) -> Dataset:
    """Load a dataset from HuggingFace Hub"""
    if not HF_AVAILABLE:
        raise ImportError("datasets package required. Install with: pip install datasets")
    
    hf_dataset = load_dataset(dataset_name, split=split, **kwargs)
    
    # Extract features and labels (adapt based on dataset structure)
    if 'image' in hf_dataset.features and 'label' in hf_dataset.features:
        # Image classification dataset
        images = []
        labels = []
        for item in hf_dataset:
            img = item['image']
            if hasattr(img, 'convert'):  # PIL Image
                img = np.array(img.convert('RGB'))
            images.append(img)
            labels.append(item['label'])
        return Dataset(images, labels)
    else:
        # Generic dataset - use first two features
        feature_names = list(hf_dataset.features.keys())
        if len(feature_names) >= 2:
            X = [item[feature_names[0]] for item in hf_dataset]
            y = [item[feature_names[1]] for item in hf_dataset]
            return Dataset(X, y)
        else:
            raise ValueError(f"Dataset {dataset_name} structure not supported")


def create_dataset_from_arrays(X: Union[List, np.ndarray], y: Union[List, np.ndarray], 
                              dtype=float32) -> Dataset:
    """Create Dataset from numpy arrays or lists"""
    return Dataset(X, y, dtype=dtype)