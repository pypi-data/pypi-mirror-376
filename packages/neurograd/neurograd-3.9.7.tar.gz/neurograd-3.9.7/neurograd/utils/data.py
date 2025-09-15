from neurograd import Tensor, float32
import math
import random
import os
import cv2
# cv2.setNumThreads(1)
import numpy as np
from neurograd import xp
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

class Dataset:
    def __init__(self, X, y, dtype=float32):
        assert len(X) == len(y), "Mismatched input and label lengths"
        # Store as numpy arrays, not Tensors
        self.X = np.asarray(X)
        self.y = np.asarray(y)
        self.dtype = dtype
        
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        # Return numpy arrays, not Tensors
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
        return f"<Dataset: {len(self)} samples, dtype={self.X.dtype}>"
    
    def __str__(self):
        preview_x = self.X[:1]
        preview_y = self.y[:1]
        return (f"Dataset:\n"
                f"  Total samples: {len(self)}\n"
                f"  Input preview: {preview_x}\n"
                f"  Target preview: {preview_y}")


from collections import deque
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
        self.dtype = dataset.dtype

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
        # Convert to Tensor only at batch level
        X = Tensor(xp.stack([x for x in Xs], axis=0), dtype=self.dtype)
        y = Tensor(xp.stack([y for y in ys], axis=0), dtype=self.dtype)
        return X, y

    def _ensure_executor(self):
        if self.num_workers > 0 and self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=self.num_workers)

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
        # Convert to Tensor only at batch level
        X = Tensor(xp.stack([x for x in Xs], axis=0), dtype=self.dtype)
        y = Tensor(xp.stack([y for y in ys], axis=0), dtype=self.dtype)
        return X, y

    def __iter__(self):
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


IMG_EXTS = (
    '.png', '.jpg', '.jpeg', '.bmp', '.gif',
    '.tif', '.tiff', '.webp', '.jfif', '.avif',
    '.heif', '.heic'
)

class ImageFolder(Dataset):
    def __init__(
        self,
        root: str,
        img_shape: tuple = None,
        img_mode: str = "RGB",
        img_normalize: bool = True,
        img_transform: callable = None,
        target_transform: callable = None,
        img_dtype=np.float32,  # Use numpy dtypes, not xp
        target_dtype=np.int64,
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

        self.images: list[str] = []
        self.targets: list[str] = []
        self._collect_paths()

        # stable class mapping
        self.target_names = sorted(set(self.targets))
        self.target_mapping = {name: i for i, name in enumerate(self.target_names)}
        self.num_classes = len(self.target_names)
        
        # Initialize parent with empty arrays (we'll load on demand)
        super().__init__([], [], dtype=float32)

    def _collect_paths(self):
        for r, _, files in os.walk(self.root):
            for f in files:
                if f.lower().endswith(IMG_EXTS):
                    p = os.path.join(r, f)
                    cls = os.path.basename(os.path.dirname(p))
                    self.images.append(p)
                    self.targets.append(cls)

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
        mode = (self.img_mode or "RGB").upper()
        if mode in ("L", "GRAY", "GREY", "GRAYSCALE"):
            flag = cv2.IMREAD_GRAYSCALE
        elif mode == "RGBA":
            flag = cv2.IMREAD_UNCHANGED
        else:
            flag = cv2.IMREAD_COLOR

        try:
            flag |= cv2.IMREAD_IGNORE_ORIENTATION
        except Exception:
            pass

        arr = cv2.imread(path, flag)
        if arr is None:
            raise ValueError(f"Failed to read image: {path}")

        if mode == "RGB" and arr.ndim == 3 and arr.shape[2] == 3:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
        elif mode == "RGBA" and arr.ndim == 3 and arr.shape[2] == 4:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGRA2RGBA)

        if self.img_shape is not None:
            h, w = self.img_shape
            arr = cv2.resize(arr, (int(w), int(h)), interpolation=cv2.INTER_LINEAR)
        if arr.ndim == 2:
            arr = arr[:, :, None]
        if self.img_transform:
            arr = self._apply_img_transform(arr)
        if self.chw:
            arr = np.transpose(arr, (2, 0, 1))
        if self.img_normalize:
            arr = arr.astype(np.float32) / 255.0
            
        # Convert to target dtype if needed
        if self.img_dtype is not None:
            arr = arr.astype(self.img_dtype)
            
        return arr

    def __getitem__(self, idx: int):
        img_path = self.images[idx]
        target_name = self.targets[idx]

        image = self._load_image(img_path)
        target = self.target_mapping[target_name]

        if self.target_transform:
            target = self.target_transform(target)
            
        # Convert target to numpy array with correct dtype
        target = np.array(target, dtype=self.target_dtype)

        # Return numpy arrays, not Tensors
        return image, target

    def shuffle(self, seed: Optional[int] = None):
        rng = random.Random(seed) if seed is not None else random.Random()
        idxs = list(range(len(self)))
        rng.shuffle(idxs)
        self.images = [self.images[i] for i in idxs]
        self.targets = [self.targets[i] for i in idxs]

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
                f"mode='{self.img_mode}', normalize={self.img_normalize}, chw={self.chw})")

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]