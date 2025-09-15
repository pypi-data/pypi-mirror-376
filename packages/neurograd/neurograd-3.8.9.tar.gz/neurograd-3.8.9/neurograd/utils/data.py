from neurograd import Tensor, float32
import math
import random
import os
import cv2
# cv2.setNumThreads(1) # Good practice to avoid conflicts with other multithreading
import numpy as np
from neurograd import xp
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from collections import deque

# --- Hugging Face Datasets Import ---
# This is the new dependency we're adding.
from datasets import load_dataset


# ========================================================================
# UNCHANGED: Your custom base Dataset and DataLoader classes remain the same.
# They will work seamlessly with the new ImageFolder implementation.
# ========================================================================

class Dataset:
    def __init__(self, X, y, dtype = float32):
        assert len(X) == len(y), "Mismatched input and label lengths"
        self.X = Tensor(X, dtype=dtype)
        self.y = Tensor(y, dtype=dtype)
    def __len__(self):
        return len(self.X)
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]
    def __iter__(self):
        for idx in range(len(self)):
            yield self[idx]
    def shuffle(self, seed: Optional[int] = None):
        indices = list(range(len(self)))
        rng = random.Random(seed) if seed is not None else random.Random()
        rng.shuffle(indices)
        self.X = self.X[indices]
        self.y = self.y[indices]
    def __repr__(self):
        return f"<Dataset: {len(self)} samples, dtype={self.X.data.dtype}>"
    def __str__(self):
        preview_x = self.X[:1]
        preview_y = self.y[:1]
        return (f"Dataset:\n"
                f"  Total samples: {len(self)}\n"
                f"  Input preview: {preview_x}\n"
                f"  Target preview: {preview_y}")

class DataLoader:
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

        if num_workers is None:
            cores = os.cpu_count() or 2
            self.num_workers = max(1, min(8, cores - 1))
        else:
            self.num_workers = int(num_workers)

        self._executor: Optional[ThreadPoolExecutor] = None

    def __len__(self):
        n = len(self.dataset)
        if self.drop_last:
            return n // self.batch_size
        return (n + self.batch_size - 1) // self.batch_size

    def __getitem__(self, idx):
        if idx < 0 or idx >= len(self):
            raise IndexError(f"Batch index {idx} out of range [0, {len(self)})")
        batches = list(self._batch_indices())
        batch_idxs = batches[idx]
        batch_data = [self.dataset[i] for i in batch_idxs]
        Xs, ys = zip(*batch_data)
        X = Tensor(xp.stack([x.data for x in Xs], axis=0), dtype=Xs[0].dtype)
        y = Tensor(xp.stack([y.data for y in ys], axis=0), dtype=ys[0].dtype)
        return X, y

    def _ensure_executor(self):
        if self.num_workers > 0 and self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=self.num_workers)

    def _batch_indices(self):
        n = len(self.dataset)
        order = list(range(n))
        if self.shuffle:
            # Note: If the underlying dataset is shuffled, this adds a second level of shuffling.
            # It's often better to shuffle the dataset once per epoch.
            rng = random.Random(self.seed) if self.seed is not None else random.Random()
            rng.shuffle(order)
        if self.drop_last:
            limit = (n // self.batch_size) * self.batch_size
        else:
            limit = n
        for start in range(0, limit, self.batch_size):
            end = min(start + self.batch_size, limit)
            yield order[start:end]

    def _schedule_batch(self, idxs):
        if self.num_workers > 0:
            self._ensure_executor()
            return [self._executor.submit(self.dataset.__getitem__, i) for i in idxs]
        else:
            return [(self.dataset[i], None) for i in idxs]

    def _gather_batch(self, futures_or_results):
        if self.num_workers > 0:
            batch = [f.result() for f in futures_or_results]
        else:
            batch = [r for (r, _) in futures_or_results]

        Xs, ys = zip(*batch)
        X = Tensor(xp.stack([x.data for x in Xs], axis=0), dtype=Xs[0].dtype)
        y = Tensor(xp.stack([y.data for y in ys], axis=0), dtype=ys[0].dtype)
        return X, y

    def __iter__(self):
        if self.shuffle:
            # It's more efficient to shuffle the underlying dataset once before iteration
            self.dataset.shuffle(seed=self.seed)

        batches = list(self._batch_indices())
        window = deque()
        next_to_submit = 0
        total = len(batches)
        
        pre = self.prefetch_batches if self.prefetch_batches > 0 else 0
        for _ in range(min(pre, total)):
            futs = self._schedule_batch(batches[next_to_submit])
            window.append(futs)
            next_to_submit += 1

        for b in range(total):
            if not window:
                futs = self._schedule_batch(batches[next_to_submit])
                window.append(futs)
                next_to_submit += 1
            futs = window.popleft()
            if next_to_submit < total and len(window) < self.prefetch_batches:
                next_futs = self._schedule_batch(batches[next_to_submit])
                window.append(next_futs)
                next_to_submit += 1
            X, y = self._gather_batch(futs)
            yield X, y

    def __repr__(self):
        return (f"<DataLoader: {len(self)} batches, "
                f"batch_size={self.batch_size}, "
                f"shuffle={self.shuffle}, seed={self.seed}, "
                f"num_workers={self.num_workers}, "
                f"prefetch_batches={self.prefetch_batches}>")

    def close(self):
        if self._executor is not None:
            self._executor.shutdown(wait=True)
            self._executor = None


# ========================================================================
# MODIFIED: ImageFolder class now uses Hugging Face datasets as a backend
# ========================================================================

class ImageFolder(Dataset):
    """
    A Dataset class that wraps Hugging Face's `datasets` library for fast,
    memory-efficient loading from an image folder structure, while conforming
    to the neurograd `Dataset` interface.
    """
    def __init__(
        self,
        root: str,
        img_shape: tuple = None,          # (H, W)
        img_mode: str = "RGB",            # "RGB", "L", etc.
        img_normalize: bool = True,       # /255 -> float
        img_transform: callable = None,   # after numpy conversion
        target_transform: callable = None,
        img_dtype=xp.float32,
        target_dtype=xp.int64,
        chw: bool = True                  # return CxHxW if True, else HxWxC
    ):
        print(f"Initializing ImageFolder with Hugging Face datasets backend (root: {root})")
        # Use Hugging Face datasets to quickly scan and map the directory.
        # This is extremely fast and memory-efficient. Data is loaded on access.
        self.hf_dataset = load_dataset("imagefolder", data_dir=root, split="train")

        self.root = root
        self.img_shape = img_shape
        self.img_mode = img_mode.upper()
        self.img_normalize = img_normalize
        self.img_transform = img_transform
        self.target_transform = target_transform
        self.img_dtype = img_dtype
        self.target_dtype = target_dtype
        self.chw = chw

        # Get class information directly from the loaded dataset's features
        self.target_names = self.hf_dataset.features['label'].names
        self.num_classes = self.hf_dataset.features['label'].num_classes
        print(f"Found {len(self)} images across {self.num_classes} classes: {self.target_names}")

    def __len__(self):
        """Returns the total number of samples in the dataset."""
        return len(self.hf_dataset)
    
    def _apply_img_transform(self, arr: np.ndarray) -> np.ndarray:
        """Applies user-defined transformations to the image numpy array."""
        if self.img_transform is None:
            return arr
        try: # Albumentations-style
            out = self.img_transform(image=arr)
            return out["image"] if isinstance(out, dict) and "image" in out else out
        except TypeError: # Plain callable
            return self.img_transform(arr)

    def __getitem__(self, idx: int):
        """
        Retrieves an item, processes it, and returns neurograd Tensors.
        """
        # 1. Fetch data from the Hugging Face dataset. This is very fast.
        item = self.hf_dataset[idx]
        pil_image = item['image']
        target = item['label']

        # 2. Convert PIL Image to a NumPy array, applying mode conversion
        arr = np.array(pil_image.convert(self.img_mode))

        # 3. Apply the same processing as the original class
        if self.img_shape is not None:
            h, w = self.img_shape
            arr = cv2.resize(arr, (int(w), int(h)), interpolation=cv2.INTER_LINEAR)
        
        if arr.ndim == 2: # Ensure grayscale has a channel dimension
            arr = arr[:, :, None]
            
        if self.img_transform:
            arr = self._apply_img_transform(arr)
            
        if self.chw and arr.ndim == 3:
            arr = np.transpose(arr, (2, 0, 1))  # HWC -> CHW
            
        if self.img_normalize:
            arr = arr.astype(np.float32) / 255.0

        if self.target_transform:
            target = self.target_transform(target)

        # 4. Convert to neurograd Tensors
        return Tensor(arr, dtype=self.img_dtype), Tensor(target, dtype=self.target_dtype)

    def shuffle(self, seed: Optional[int] = None):
        """
        Shuffles the dataset in-place using the efficient backend method.
        """
        print(f"Shuffling dataset with seed: {seed}")
        self.hf_dataset = self.hf_dataset.shuffle(seed=seed)

    def __repr__(self):
        shape = None
        if len(self) > 0:
            try:
                image, _ = self[0]
                shape = tuple(image.shape)
            except Exception:
                shape = "Error fetching shape"
        return (f"ImageFolder(root='{self.root}', samples={len(self)}, "
                f"classes={self.num_classes}, shape={shape}, backend='huggingface')")

    def __iter__(self):
        """Allows direct iteration over the dataset."""
        for i in range(len(self)):
            yield self[i]