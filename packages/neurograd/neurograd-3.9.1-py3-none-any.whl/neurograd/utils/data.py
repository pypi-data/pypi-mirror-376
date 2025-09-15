from neurograd import Tensor, float32
import math
import random
import os
import cv2
cv2.setNumThreads(0)  # Disable OpenCV's internal threading
import numpy as np
from neurograd import xp
from typing import Optional, List, Tuple, Any
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from multiprocessing.queues import Queue
import time
import threading

class Dataset:
    def __init__(self, X, y, dtype=float32):
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

        self._executor = None
        self._batch_indices_cache = None

    def __len__(self):
        n = len(self.dataset)
        if self.drop_last:
            return n // self.batch_size
        return (n + self.batch_size - 1) // self.batch_size

    def __getitem__(self, idx):
        if idx < 0 or idx >= len(self):
            raise IndexError(f"Batch index {idx} out of range [0, {len(self)})")
        
        if self._batch_indices_cache is None:
            self._batch_indices_cache = list(self._batch_indices())
            
        batch_idxs = self._batch_indices_cache[idx]
        batch_data = [self.dataset[i] for i in batch_idxs]
        Xs, ys = zip(*batch_data)
        X = Tensor(xp.stack([x.data for x in Xs], axis=0), dtype=Xs[0].dtype)
        y = Tensor(xp.stack([y.data for y in ys], axis=0), dtype=ys[0].dtype)
        return X, y

    def _batch_indices(self):
        n = len(self.dataset)
        order = list(range(n))
        if self.shuffle:
            rng = random.Random(self.seed) if self.seed is not None else random.Random()
            rng.shuffle(order)
        
        if self.drop_last:
            limit = (n // self.batch_size) * self.batch_size
        else:
            limit = n
            
        for start in range(0, limit, self.batch_size):
            end = min(start + self.batch_size, limit)
            yield order[start:end]

    def __iter__(self):
        # Precompute all batch indices
        batches = list(self._batch_indices())
        self._batch_indices_cache = batches
        
        # Use process pool for parallel loading
        if self.num_workers > 0:
            with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
                # Submit all batch loading tasks
                future_to_batch = {
                    executor.submit(self._load_batch, batch): i 
                    for i, batch in enumerate(batches)
                }
                
                # Yield batches as they complete
                for future in as_completed(future_to_batch):
                    yield future.result()
        else:
            # Sequential loading
            for batch in batches:
                yield self._load_batch(batch)

    def _load_batch(self, indices):
        batch_data = [self.dataset[i] for i in indices]
        Xs, ys = zip(*batch_data)
        X = Tensor(xp.stack([x.data for x in Xs], axis=0), dtype=Xs[0].dtype)
        y = Tensor(xp.stack([y.data for y in ys], axis=0), dtype=ys[0].dtype)
        return X, y

    def __repr__(self):
        return (f"<DataLoader: {len(self)} batches, "
                f"batch_size={self.batch_size}, "
                f"shuffle={self.shuffle}, seed={self.seed}, "
                f"num_workers={self.num_workers}, "
                f"prefetch_batches={self.prefetch_batches}>")


IMG_EXTS = (
    '.png', '.jpg', '.jpeg', '.bmp', '.gif',
    '.tif', '.tiff', '.webp', '.jfif', '.avif',
    '.heif', '.heic'
)


class ImageFolder:
    def __init__(
        self,
        root: str,
        img_shape: tuple = None,
        img_mode: str = "RGB",
        img_normalize: bool = True,
        img_transform: callable = None,
        target_transform: callable = None,
        img_dtype=np.float32,  # Changed to numpy dtype
        target_dtype=np.int64,  # Changed to numpy dtype
        chw: bool = True,
        preload: bool = False
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
        self.preload = preload

        self.images: List[str] = []
        self.targets: List[str] = []
        self._collect_paths()

        # Preload images if requested
        self.preloaded_data = None
        if preload:
            self._preload_images()

        # stable class mapping
        self.target_names = sorted(set(self.targets))
        self.target_mapping = {name: i for i, name in enumerate(self.target_names)}
        self.num_classes = len(self.target_names)

    def _collect_paths(self):
        for r, _, files in os.walk(self.root):
            for f in files:
                if f.lower().endswith(IMG_EXTS):
                    p = os.path.join(r, f)
                    cls = os.path.basename(os.path.dirname(p))
                    self.images.append(p)
                    self.targets.append(cls)

    def _preload_images(self):
        """Preload all images into memory as numpy arrays"""
        print(f"Preloading {len(self.images)} images...")
        self.preloaded_data = []
        
        for i, img_path in enumerate(self.images):
            if i % 1000 == 0:
                print(f"Preloaded {i}/{len(self.images)} images")
                
            image = self._load_image(img_path)
            target_name = self.targets[i]
            target = self.target_mapping[target_name]
            
            if self.target_transform:
                target = self.target_transform(target)
                
            self.preloaded_data.append((image, target))
        print("Preloading complete!")

    def __len__(self):
        return len(self.images)

    def _apply_img_transform(self, arr: np.ndarray) -> np.ndarray:
        if self.img_transform is None:
            return arr
        try:
            out = self.img_transform(image=arr)
            if isinstance(out, dict) and "image" in out:
                return out["image"]
        except TypeError:
            pass
        return self.img_transform(arr)

    def _load_image(self, path: str) -> np.ndarray:
        # Read image directly as numpy array for faster processing
        mode = (self.img_mode or "RGB").upper()
        if mode in ("L", "GRAY", "GREY", "GRAYSCALE"):
            flag = cv2.IMREAD_GRAYSCALE
        elif mode == "RGBA":
            flag = cv2.IMREAD_UNCHANGED
        else:
            flag = cv2.IMREAD_COLOR

        # Use imdecode for faster reading
        with open(path, 'rb') as f:
            img_array = np.frombuffer(f.read(), dtype=np.uint8)
            arr = cv2.imdecode(img_array, flag)

        if arr is None:
            raise ValueError(f"Failed to read image: {path}")

        # Convert channel order
        if mode == "RGB" and arr.ndim == 3 and arr.shape[2] == 3:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
        elif mode == "RGBA" and arr.ndim == 3 and arr.shape[2] == 4:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGRA2RGBA)

        # Resize if needed
        if self.img_shape is not None:
            h, w = self.img_shape
            arr = cv2.resize(arr, (int(w), int(h)), interpolation=cv2.INTER_AREA)

        if arr.ndim == 2:
            arr = arr[:, :, None]
            
        if self.img_transform:
            arr = self._apply_img_transform(arr)
            
        if self.chw:
            arr = np.transpose(arr, (2, 0, 1))
            
        if self.img_normalize:
            arr = arr.astype(np.float32) / 255.0
            
        return arr.astype(self.img_dtype)

    def __getitem__(self, idx: int):
        if self.preloaded_data:
            image, target = self.preloaded_data[idx]
            return image, target  # Return numpy arrays, not Tensors
        
        img_path = self.images[idx]
        target_name = self.targets[idx]

        image = self._load_image(img_path)
        target = self.target_mapping[target_name]

        if self.target_transform:
            target = self.target_transform(target)

        return image, np.array(target, dtype=self.target_dtype)  # Return numpy arrays, not Tensors

    def shuffle(self, seed: Optional[int] = None):
        rng = random.Random(seed) if seed is not None else random.Random()
        idxs = list(range(len(self)))
        rng.shuffle(idxs)
        self.images = [self.images[i] for i in idxs]
        self.targets = [self.targets[i] for i in idxs]
        
        if self.preloaded_data:
            self.preloaded_data = [self.preloaded_data[i] for i in idxs]

    def __repr__(self):
        shape = None
        if len(self) > 0:
            try:
                image, _ = self[0]
                shape = tuple(image.shape)
            except Exception:
                shape = None
        return (f"ImageFolder(root='{self.root}', samples={len(self)}, "
                f"classes={getattr(self, 'num_classes', 0)}, "
                f"shape={shape}, img_dtype={self.img_dtype}, target_dtype={self.target_dtype}, "
                f"mode='{self.img_mode}', normalize={self.img_normalize}, chw={self.chw}, "
                f"preload={self.preload})")

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]


class ImageDataLoader(DataLoader):
    """Specialized DataLoader for ImageFolder that handles numpy to Tensor conversion efficiently"""
    def __init__(self, dataset: ImageFolder, batch_size: int = 32,
                 shuffle: bool = True, seed: Optional[int] = None,
                 num_workers: Optional[int] = None,
                 prefetch_batches: int = 2,
                 drop_last: bool = False):
        super().__init__(dataset, batch_size, shuffle, seed, num_workers, prefetch_batches, drop_last)
        
    def _load_batch(self, indices):
        # Load batch data as numpy arrays
        batch_data = [self.dataset[i] for i in indices]
        Xs, ys = zip(*batch_data)
        
        # Convert to Tensor at batch level (more efficient)
        X = Tensor(xp.asarray(np.stack(Xs, axis=0)), dtype=float32)
        y = Tensor(xp.asarray(np.stack(ys, axis=0)), dtype=xp.int64)
        
        return X, y