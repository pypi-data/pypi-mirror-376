# ===================================================================
#
#  Part 1: Data Loading Library Code (Corrected)
#
# ===================================================================

import math
import random
import os
import numpy as np
from neurograd import xp, Tensor, float32, int64
from typing import Optional, List, Tuple, Union, Callable, Dict, Any
import glob
from collections import deque
from concurrent.futures import ThreadPoolExecutor, Future
import cv2
import psutil
import shutil
import hashlib
import threading
import time

# Suppress common environment variable warnings from libraries like OpenCV
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK']='True'

# Try to import DALI first - this determines our capabilities
try:
    import nvidia.dali as dali
    from nvidia.dali import pipeline_def, Pipeline
    import nvidia.dali.fn as fn
    import nvidia.dali.types as types
    from nvidia.dali.plugin.base_iterator import LastBatchPolicy
    from nvidia.dali.backend import PreallocateDeviceMemory, PreallocatePinnedMemory
    DALI_AVAILABLE = True

    class DALIGenericIterator:
        """
        A generic DALI iterator that is not tied to any specific framework.
        It iterates over a DALI pipeline and yields batches of data.
        """
        def __init__(
            self,
            pipeline: Pipeline,
            output_map: List[str],
            last_batch_policy: LastBatchPolicy,
            auto_reset: bool = False,
            reader_name: Optional[str] = None
        ):
            self._pipeline = pipeline
            self._output_map = output_map
            self._last_batch_policy = last_batch_policy
            self._auto_reset = auto_reset
            self._reader_name = reader_name

            if not self._reader_name:
                readers = [op.name for op in self._pipeline.ops if "readers" in op.spec.name]
                if len(readers) == 1:
                    self._reader_name = readers[0]
                else:
                    raise ValueError(
                        f"Could not automatically determine the reader name. "
                        f"Found {len(readers)} readers: {readers}. Please specify 'reader_name'."
                    )

            self._size = self._pipeline.epoch_size(self._reader_name)
            self._batch_size = self._pipeline.max_batch_size

            if self._last_batch_policy == LastBatchPolicy.DROP:
                self._num_batches = self._size // self._batch_size
            else:
                self._num_batches = math.ceil(self._size / self._batch_size)

            self._counter = 0

        def __iter__(self):
            return self

        def __len__(self):
            return self._num_batches

        def __next__(self):
            if self._counter >= self._num_batches:
                if self._auto_reset:
                    self.reset()
                raise StopIteration

            try:
                outputs = self._pipeline.run()
                self._counter += 1
                batch_dict = {key: outputs[i] for i, key in enumerate(self._output_map)}
                return [batch_dict]
            except StopIteration:
                if self._auto_reset:
                    self.reset()
                raise

        def reset(self):
            self._pipeline.reset()
            self._counter = 0

except ImportError:
    DALI_AVAILABLE = False
    print("INFO: NVIDIA DALI not available. Falling back to OpenCV-based implementation.")
    print("      For maximum performance, install with: pip install --extra-index-url https://developer.download.nvidia.com/compute/redist nvidia-dali-cuda120")

IMG_EXTS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tif', '.tiff', '.webp', '.jfif', '.avif', '.heif', '.heic')

class Dataset:
    """Base dataset class for simple tensor data"""
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
        return f"Dataset:\n  Total samples: {len(self)}\n  Input preview: {self.X[:1]}\n  Target preview: {self.y[:1]}"

class ImageFolder(Dataset):
    """
    ImageFolder with smart caching for network storage.
    Caches raw image files to a local directory to accelerate reading.
    """
    def __init__(
        self,
        root: str,
        img_shape: tuple = None,
        img_mode: str = "RGB",
        img_normalize: bool = True,
        img_transform: callable = None,
        one_hot_targets: bool = True,
        img_dtype=xp.float32,
        target_dtype=xp.int64,
        chw: bool = True,
        cache_dir: Optional[str] = None,
        cache_size_limit: int = 20 * 1024**3,
        cache_strategy: str = "lru",
    ):
        self.root = os.path.abspath(root)
        self.img_shape = img_shape
        self.img_mode = img_mode
        self.img_normalize = img_normalize
        self.img_transform = img_transform
        self.one_hot_targets = one_hot_targets
        self.img_dtype = img_dtype
        self.target_dtype = target_dtype
        self.chw = chw
        self.cache_dir = os.path.abspath(cache_dir) if cache_dir else None
        self.cache_size_limit = cache_size_limit
        self.cache_strategy = cache_strategy

        self.cache_current_size = 0
        self.cache_lock = threading.Lock()
        self.cache_access_times: Dict[str, float] = {}
        self.cache_available = False

        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
            self.cache_available = True
            self._update_cache_size()
            print(f"File cache enabled at: {self.cache_dir}")
            print(f"Cache size: {self.cache_current_size / (1024**3):.2f}GB used of {self.cache_size_limit / (1024**3):.2f}GB limit")

        self.images: List[str] = []
        self.targets: List[str] = []
        self.dont_use_mmap = is_on_network_drive(self.root)
        self._collect_paths()

        if not self.images:
            raise ValueError(f"No images found in {root} with supported extensions: {IMG_EXTS}")

        self.cached_image_paths: List[str] = [self._get_cache_destination(p) for p in self.images] if self.cache_available else []

        self.target_names = sorted(set(self.targets))
        self.target_mapping = {name: i for i, name in enumerate(self.target_names)}
        self.num_classes = len(self.target_names)
        self.one_hot_mapping: Dict[int, np.ndarray] = {i: np.eye(self.num_classes, dtype=np.float32)[i] for i in range(self.num_classes)}
        self.numeric_targets = [self.target_mapping[t] for t in self.targets]
        print(f"ImageFolder initialized: {len(self)} samples, {self.num_classes} classes")

    def _get_cache_destination(self, original_path: str) -> str:
        relative_path = os.path.relpath(original_path, self.root)
        _, extension = os.path.splitext(original_path)
        hashed_name = hashlib.md5(relative_path.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed_name}{extension}")

    def _ensure_file_is_cached(self, original_path: str, cached_path: str) -> str:
        if not self.cache_available:
            return original_path
        
        if os.path.exists(cached_path):
            if self.cache_strategy == 'lru':
                with self.cache_lock:
                    self.cache_access_times[cached_path] = time.time()
            return cached_path
        
        with self.cache_lock:
            if os.path.exists(cached_path):
                if self.cache_strategy == 'lru':
                    self.cache_access_times[cached_path] = time.time()
                return cached_path
            
            self._add_to_cache(original_path, cached_path)
        return cached_path

    def _add_to_cache(self, original_path: str, cached_path: str):
        os.makedirs(os.path.dirname(cached_path), exist_ok=True)
        shutil.copyfile(original_path, cached_path)
        file_size = os.path.getsize(cached_path)
        
        self.cache_current_size += file_size
        self.cache_access_times[cached_path] = time.time()
        
        if self.cache_current_size > self.cache_size_limit:
            self._manage_cache_size()

    def _manage_cache_size(self):
        target_size = self.cache_size_limit * 0.9
        if self.cache_current_size <= target_size:
            return

        if self.cache_strategy == "lru":
            items_to_remove = sorted(self.cache_access_times.items(), key=lambda x: x[1])
        else:
            try:
                items_to_remove = sorted(self.cache_access_times.items(), key=lambda x: os.path.getctime(x[0]))
            except OSError:
                items_to_remove = sorted(self.cache_access_times.items(), key=lambda x: os.path.getmtime(x[0]))

        for path, _ in items_to_remove:
            if self.cache_current_size <= target_size:
                break
            
            if os.path.exists(path):
                try:
                    file_size = os.path.getsize(path)
                    os.remove(path)
                    self.cache_current_size -= file_size
                    del self.cache_access_times[path]
                except (OSError, KeyError):
                    continue

    def _update_cache_size(self):
        total_size = 0
        self.cache_access_times = {}
        if not (self.cache_dir and os.path.exists(self.cache_dir)):
            return
            
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            try:
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
                    self.cache_access_times[file_path] = os.path.getmtime(file_path)
            except OSError:
                continue
        self.cache_current_size = total_size

    def get_class_name(self, class_idx: int) -> str:
        return self.target_names[class_idx]
    
    def get_class_index(self, class_name: str) -> int:
        return self.target_mapping[class_name]
    
    def get_one_hot(self, class_idx: int) -> np.ndarray:
        return self.one_hot_mapping[class_idx]
    
    def get_class_from_one_hot(self, one_hot: np.ndarray) -> int:
        return int(np.argmax(one_hot))

    def _collect_paths(self):
        if not os.path.isdir(self.root):
            raise ValueError(f"Root directory {self.root} does not exist")
        
        for class_name in sorted(os.listdir(self.root)):
            class_path = os.path.join(self.root, class_name)
            if not os.path.isdir(class_path):
                continue
            
            for f in sorted(os.listdir(class_path)):
                if f.lower().endswith(IMG_EXTS):
                    self.images.append(os.path.join(class_path, f))
                    self.targets.append(class_name)

    def get_dali_pipeline(self, batch_size: int, shuffle: bool = True, device: str = "cpu", num_threads: int = 4, prefetch: int = 2, seed: int = 42):
        if not DALI_AVAILABLE:
            return None
        if isinstance(self.img_transform, Pipeline):
            return self.img_transform
        
        is_gpu = device == "gpu"
        h, w = self.img_shape or (224, 224)
        image_source_paths = self.cached_image_paths if self.cache_available else self.images
        
        @pipeline_def(batch_size=batch_size, num_threads=num_threads, device_id=0 if is_gpu else None, seed=seed, prefetch_queue_depth=prefetch)
        def image_pipeline():
            images, labels = fn.readers.file(files=image_source_paths, labels=self.numeric_targets, random_shuffle=shuffle, name="Reader", initial_fill=4096, read_ahead=True, dont_use_mmap=self.dont_use_mmap)
            images = fn.decoders.image(images, device="mixed" if is_gpu else "cpu", output_type=types.RGB)
            images = fn.resize(images, resize_x=w, resize_y=h, interp_type=types.INTERP_LINEAR)
            
            if self.img_transform and callable(self.img_transform):
                images = self.img_transform(images)
            
            if self.img_normalize:
                images = fn.crop_mirror_normalize(images, dtype=types.FLOAT, output_layout="CHW" if self.chw else "HWC", mean=[0.485 * 255, 0.456 * 255, 0.406 * 255], std=[0.229 * 255, 0.224 * 255, 0.225 * 255])
            elif self.chw:
                images = fn.transpose(images, perm=[2, 0, 1])
            
            if self.one_hot_targets:
                labels = fn.one_hot(labels, num_classes=self.num_classes)
            
            return images, labels
        
        return image_pipeline()

    def _apply_img_transform(self, arr: np.ndarray) -> np.ndarray:
        if self.img_transform is None:
            return arr
        if isinstance(self.img_transform, Pipeline):
            return arr
        
        try:
            out = self.img_transform(image=arr)
            return out["image"] if isinstance(out, dict) else out
        except Exception:
            try:
                return self.img_transform(arr)
            except Exception as e:
                print(f"WARNING: img_transform failed: {e}")
                return arr

    def _load_image_opencv(self, path: str) -> np.ndarray:
        flag = cv2.IMREAD_COLOR
        if self.img_mode in ("L", "GRAY", "GREY", "GRAYSCALE"):
            flag = cv2.IMREAD_GRAYSCALE
        
        arr = cv2.imread(path, flag)
        if arr is None:
            raise IOError(f"Failed to read image: {path}")

        if self.img_mode == "RGB" and arr.ndim == 3 and arr.shape[2] == 3:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
        
        if self.img_shape:
            arr = cv2.resize(arr, (self.img_shape[1], self.img_shape[0]), interpolation=cv2.INTER_LINEAR)
        
        if arr.ndim == 2:
            arr = arr[..., None]
        
        if self.img_transform:
            arr = self._apply_img_transform(arr)
        
        if self.chw and arr.ndim == 3:
            arr = np.transpose(arr, (2, 0, 1))
        
        arr = arr.astype(np.float32)
        if self.img_normalize:
            arr /= 255.0
            
        return arr

    def __getitem__(self, idx: int):
        original_path = self.images[idx]
        target_val = self.numeric_targets[idx]
        
        path_to_load = original_path
        if self.cache_available:
            cached_path = self.cached_image_paths[idx]
            path_to_load = self._ensure_file_is_cached(original_path, cached_path)
            
        image = self._load_image_opencv(path_to_load)
        
        target = self.one_hot_mapping[target_val] if self.one_hot_targets else target_val
        target_dtype = float32 if self.one_hot_targets else self.target_dtype
        
        return Tensor(image, dtype=self.img_dtype), Tensor(target, dtype=target_dtype)

    def shuffle(self, seed: Optional[int] = None):
        rng = random.Random(seed) if seed is not None else random.Random()
        
        if self.cache_available:
            combined = list(zip(self.images, self.targets, self.numeric_targets, self.cached_image_paths))
        else:
            combined = list(zip(self.images, self.targets, self.numeric_targets))

        if not combined:
            return

        rng.shuffle(combined)
        
        if self.cache_available:
            self.images, self.targets, self.numeric_targets, self.cached_image_paths = [list(t) for t in zip(*combined)]
        else:
            self.images, self.targets, self.numeric_targets = [list(t) for t in zip(*combined)]

    def __len__(self):
        return len(self.images)

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __str__(self):
        return f"ImageFolder(root='{self.root}', samples={len(self)}, classes={self.num_classes})"

    def __repr__(self):
        shape = tuple(self[0][0].shape) if len(self) > 0 else None
        return f"ImageFolder(root='{self.root}', samples={len(self)}, classes={self.num_classes}, shape={shape})"

class DataLoader:
    """Enhanced DataLoader with optimizations for network storage via file caching."""
    def __init__(
        self,
        dataset: Union[ImageFolder, Dataset],
        batch_size: int = 32,
        shuffle: bool = True,
        device: str = "gpu",
        num_workers: int = None,
        prefetch_batches: int = 4,
        drop_last: bool = False,
        seed: Optional[int] = None,
        cache_prefetch: bool = True,
        cache_warmup_size: int = 5000,
    ):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.device = "gpu" if device in ["gpu", "cuda"] else "cpu"
        
        if num_workers is None:
            default_workers = os.cpu_count() or 1
            if hasattr(dataset, 'dont_use_mmap') and dataset.dont_use_mmap:
                self.num_workers = min(16, default_workers * 2)
            else:
                self.num_workers = default_workers
        else:
            self.num_workers = max(0, int(num_workers))
            
        self.prefetch_batches = max(2, int(prefetch_batches))
        self.drop_last = drop_last
        self.seed = seed
        self.cache_prefetch = cache_prefetch and isinstance(dataset, ImageFolder) and dataset.cache_available
        
        self.prefetch_executor: Optional[ThreadPoolExecutor] = None
        self._pipeline: Optional[Pipeline] = None
        self._dali_iter: Optional[DALIGenericIterator] = None
        self._executor: Optional[ThreadPoolExecutor] = None
        
        if DALI_AVAILABLE:
            try:
                if self.device == "gpu":
                    PreallocateDeviceMemory(int(0.5 * 1024**3), 0)
                PreallocatePinnedMemory(int(0.25 * 1024**3))
            except Exception as e:
                print(f"WARNING: DALI memory preallocation failed: {e}")
        
        self.use_dali = DALI_AVAILABLE and isinstance(dataset, ImageFolder)
        if self.use_dali:
            self._init_dali_pipeline()
        
        if self.device == "gpu" and not self.use_dali:
            print("WARNING: GPU device requested but DALI not available. Using CPU fallback.")
            self.device = "cpu"
            
        if self.use_dali and self.cache_prefetch:
            self._warmup_cache(cache_warmup_size)
        
        if self.cache_prefetch:
            self._start_background_prefetching()

    def _warmup_cache(self, num_files_to_warmup: int):
        """
        Synchronously pre-caches a random sample of files to prevent a race
        condition with DALI's random reader.
        """
        print(f"Starting cache warm-up for {num_files_to_warmup} random files...")
        ds = self.dataset
        
        num_to_sample = min(num_files_to_warmup, len(ds.images))
        if num_to_sample == 0:
            print("No files to warm up.")
            return

        warmup_indices = random.sample(range(len(ds.images)), num_to_sample)
        
        with ThreadPoolExecutor(max_workers=self.num_workers, thread_name_prefix='CacheWarmer') as executor:
            futures = [
                executor.submit(ds._ensure_file_is_cached, ds.images[i], ds.cached_image_paths[i])
                for i in warmup_indices
            ]
            for future in futures:
                future.result()

        print("Cache warm-up complete.")

    def _start_background_prefetching(self):
        """Starts background threads to cache subsequent batches sequentially."""
        if not self.cache_prefetch:
            return
            
        self.prefetch_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='CachePrefetcher')
        batches = list(self._batch_indices())
        
        for i, batch_indices in enumerate(batches[:self.prefetch_batches]):
            self.prefetch_executor.submit(self._precache_batch, batch_indices)
    
    def _precache_batch(self, indices: List[int]):
        """Target function for background prefetching threads."""
        ds = self.dataset
        if not (isinstance(ds, ImageFolder) and ds.cache_available):
            return
            
        for idx in indices:
            try:
                ds._ensure_file_is_cached(ds.images[idx], ds.cached_image_paths[idx])
            except Exception:
                continue

    def _init_dali_pipeline(self):
        if not self.use_dali:
            return
            
        self._pipeline = self.dataset.get_dali_pipeline(
            batch_size=self.batch_size, shuffle=self.shuffle, device=self.device,
            num_threads=self.num_workers, prefetch=self.prefetch_batches, seed=self.seed)
            
        if self._pipeline:
            policy = LastBatchPolicy.DROP if self.drop_last else LastBatchPolicy.PARTIAL
            self._dali_iter = DALIGenericIterator(self._pipeline, ["images", "labels"], policy, reader_name="Reader")
            print(f"DALI pipeline initialized: batch_size={self.batch_size}, device={self.device}, num_threads={self.num_workers}")

    def __len__(self):
        n = len(self.dataset)
        return n // self.batch_size if self.drop_last else math.ceil(n / self.batch_size)

    def __iter__(self):
        if self.shuffle and not self.use_dali:
            self.dataset.shuffle(seed=self.seed)
        
        if self.use_dali and self._dali_iter:
            self._dali_iter.reset()
            return self._dali_iterator()
        else:
            return self._regular_iterator()

    def reset(self):
        if self.use_dali and self._dali_iter:
            self._dali_iter.reset()

    def _dali_iterator(self):
        for data in self._dali_iter:
            images_tensor = data[0]["images"]
            labels_tensor = data[0]["labels"]
            
            if self.device == 'gpu':
                try:
                    import cupy as cp
                    images_array = cp.asarray(images_tensor.as_tensor())
                    labels_array = cp.asarray(labels_tensor.as_tensor())
                except ImportError:
                    raise ImportError("Cupy is required for GPU tensors. Install with 'pip install cupy-cudaXXX'")
            else:
                images_array = images_tensor.as_array()
                labels_array = labels_tensor.as_array()
    
            X = Tensor(images_array, dtype=self.dataset.img_dtype)
            y_dtype = float32 if self.dataset.one_hot_targets else self.dataset.target_dtype
            y = Tensor(labels_array, dtype=y_dtype)
            yield X, y
            
    def _regular_iterator(self):
        batches = list(self._batch_indices())
        if self.cache_prefetch and self.prefetch_executor:
            for i, batch_indices in enumerate(batches):
                self.prefetch_executor.submit(self._precache_batch, batch_indices)
        
        if self.num_workers > 0:
            self._ensure_executor()
            for batch_indices in batches:
                futures = [self._executor.submit(self.dataset.__getitem__, i) for i in batch_indices]
                yield self._gather_batch(futures)
        else:
            for batch_indices in batches:
                yield self._gather_batch([self.dataset[i] for i in batch_indices])

    def _batch_indices(self):
        n = len(self.dataset)
        order = list(range(n))
        limit = (n // self.batch_size) * self.batch_size if self.drop_last else n
        for start in range(0, limit, self.batch_size):
            yield order[start:min(start + self.batch_size, n)]

    def _ensure_executor(self):
        if self.num_workers > 0 and (self._executor is None or self._executor._shutdown):
            self._executor = ThreadPoolExecutor(max_workers=self.num_workers, thread_name_prefix='DataLoaderWorker')

    def _gather_batch(self, futures_or_results: Union[List[Future], List[Any]]):
        if self.num_workers > 0 and futures_or_results and isinstance(futures_or_results[0], Future):
            batch = [f.result() for f in futures_or_results]
        else:
            batch = futures_or_results
        
        Xs, ys = zip(*batch)
        return Tensor(xp.stack([x.data for x in Xs])), Tensor(xp.stack([y.data for y in ys]))

    def close(self):
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
        if self.prefetch_executor:
            self.prefetch_executor.shutdown(wait=False)
            self.prefetch_executor = None
    
    def __del__(self):
        self.close()

def create_dali_transforms(device: str = "cpu", **kwargs):
    if not DALI_AVAILABLE:
        print("WARNING: DALI not available. Transform creation skipped.")
        return None
        
    def apply_transforms(images):
        # This is a simplified placeholder. The full implementation would use kwargs.
        images = fn.color_twist(images, device=device, brightness=fn.random.uniform(range=[-0.4, 0.4]))
        images = fn.flip(images, device=device, horizontal=fn.random.coin_flip(probability=0.5))
        return images
    
    return apply_transforms

def is_on_network_drive(path_to_check: str) -> bool:
    if not os.path.exists(path_to_check):
        return False
        
    NETWORK_FS_TYPES = {"nfs", "nfs4", "nfsd", "cifs", "smbfs", "smb", "sshfs", "gcsfuse", "s3fs"}
    path_to_check = os.path.abspath(path_to_check)
    best_mount, best_partition = "", None
    
    for p in psutil.disk_partitions(all=True):
        if path_to_check.startswith(p.mountpoint) and len(p.mountpoint) > len(best_mount):
            best_mount, best_partition = p.mountpoint, p
            
    if best_partition:
        return best_partition.fstype.lower().split('.')[0] in NETWORK_FS_TYPES
        
    return False