"""
Optimized data loading utilities for NeuroGrad with multiprocessing support.
Major performance improvements over the original data.py implementation.

Key Features:
- Multiprocessing with configurable worker count
- Advanced prefetching for overlapped I/O
- Proper pinned memory handling for GPU transfers (CPU -> GPU optimization)
- Memory-efficient batch collation
- Cross-platform compatibility (Windows/Linux)
- Performance monitoring and statistics
"""

from neurograd import Tensor, float32, xp
import math
import random
import os
import cv2
cv2.setNumThreads(1)  # Prevent OpenCV threading conflicts
import numpy as np
from typing import Optional, Union, Callable, Any
try:
    import multiprocess as mp  # Use multiprocess (cloudpickle-enabled) instead of multiprocessing
except ImportError:
    import multiprocessing as mp  # Fallback to standard multiprocessing
    print("Warning: multiprocess not available, falling back to multiprocessing. Some functions may not be picklable.")
import queue
import time
import threading
from collections import deque
import pickle

# Check if we're using NumPy (CPU) or CuPy (GPU)
try:
    import numpy as real_np
    IS_CPU = xp is real_np
except ImportError:
    IS_CPU = True


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

    @staticmethod
    def _worker_loop(dataset, index_queue, data_queue, worker_id, pin_memory=False):
        """Worker process function for loading data samples."""
        # Set OpenCV threading for worker process
        cv2.setNumThreads(1)
        
        # Force workers to use CPU-only mode to avoid CUDA context issues
        # This prevents cudaErrorInitializationError in multiprocessing workers
        import os
        os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Hide CUDA from workers
        
        # Re-import neurograd to ensure CPU mode in worker
        import sys
        if 'neurograd' in sys.modules:
            # Clear neurograd modules to force CPU re-initialization
            modules_to_clear = [name for name in sys.modules.keys() if name.startswith('neurograd')]
            for mod in modules_to_clear:
                del sys.modules[mod]
        
        # Import neurograd in CPU mode
        from neurograd import Tensor, xp
        
        while True:
            try:
                indices = index_queue.get(timeout=1)
                if indices is None:  # Shutdown signal
                    break
                    
                # Load batch data (will be CPU-only in workers)
                batch_data = []
                for idx in indices:
                    try:
                        sample = dataset[idx]
                        batch_data.append(sample)
                    except Exception as e:
                        # Handle corrupted data gracefully
                        print(f"Worker {worker_id}: Error loading sample {idx}: {e}")
                        continue
                
                if batch_data:
                    data_queue.put((indices, batch_data))
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker {worker_id}: Unexpected error: {e}")
                break
    
    def _collate_batch(self, batch_data):
        """Efficiently collate batch data into tensors with optional pinned memory."""
        if not batch_data:
            return None, None
            
        # Separate samples and targets
        samples, targets = zip(*batch_data)
        
        # Convert to numpy arrays first (more efficient than stacking individual tensors)
        if hasattr(samples[0], 'data'):
            # If samples are already Tensors, extract data (will be CPU from workers)
            sample_arrays = [s.data for s in samples]
            target_arrays = [t.data for t in targets]
        else:
            # If samples are numpy arrays
            sample_arrays = list(samples)
            target_arrays = list(targets)
        
        # Pin memory optimization: allocate pinned memory if requested
        if self.pin_memory and IS_CPU:  # Only on CPU with GPU available
            try:
                import cupy as cp
                if cp.cuda.is_available():
                    # Use pinned memory for efficient GPU transfers
                    X_data = self._create_pinned_batch(sample_arrays)
                    y_data = self._create_pinned_batch(target_arrays)
                else:
                    # Fallback to regular stacking
                    X_data = xp.stack(sample_arrays, axis=0)
                    y_data = xp.stack(target_arrays, axis=0) if len(target_arrays[0].shape) > 0 else xp.array(target_arrays)
            except ImportError:
                # CuPy not available, fallback to regular stacking
                X_data = xp.stack(sample_arrays, axis=0)
                y_data = xp.stack(target_arrays, axis=0) if len(target_arrays[0].shape) > 0 else xp.array(target_arrays)
        else:
            # Regular stacking without pinned memory
            X_data = xp.stack(sample_arrays, axis=0)
            y_data = xp.stack(target_arrays, axis=0) if len(target_arrays[0].shape) > 0 else xp.array(target_arrays)
        
        # Create tensors (will automatically be on correct device based on current xp)
        X = Tensor(X_data, dtype=samples[0].dtype if hasattr(samples[0], 'dtype') else X_data.dtype)
        y = Tensor(y_data, dtype=targets[0].dtype if hasattr(targets[0], 'dtype') else y_data.dtype)
        
        # If main process is using GPU, transfer tensors to GPU
        if not IS_CPU:  # Main process is on GPU
            try:
                import cupy as cp
                if hasattr(X.data, 'get'):  # Already CuPy array
                    pass  # Already on GPU
                else:  # NumPy array from CPU workers
                    X.data = cp.asarray(X.data)  # Transfer to GPU
                    y.data = cp.asarray(y.data)  # Transfer to GPU
            except ImportError:
                pass  # No CuPy available
            
        return X, y
    
    def _create_pinned_batch(self, arrays):
        """Create a batch tensor using pinned memory for faster GPU transfers."""
        try:
            import cupy as cp
            import numpy as np
            
            # Calculate total size needed
            if len(arrays) == 0:
                return xp.array([])
            
            # Determine batch shape
            batch_shape = (len(arrays),) + arrays[0].shape
            total_bytes = np.prod(batch_shape) * arrays[0].dtype.itemsize
            
            # Allocate pinned memory
            pinned_pool = cp.get_default_pinned_memory_pool()
            pinned_mem = pinned_pool.malloc(total_bytes)
            
            # Create numpy array view of pinned memory
            pinned_array = np.frombuffer(
                pinned_mem, dtype=arrays[0].dtype, count=np.prod(batch_shape)
            ).reshape(batch_shape)
            
            # Copy data into pinned memory
            for i, arr in enumerate(arrays):
                pinned_array[i] = arr
            
            # Store reference to prevent garbage collection
            pinned_array._pinned_mem_ref = pinned_mem
            
            return pinned_array
            
        except Exception:
            # Fallback to regular stacking if pinned memory allocation fails
            return xp.stack(arrays, axis=0) if len(arrays[0].shape) > 0 else xp.array(arrays)
    def __init__(self, dataset: Dataset, batch_size: int = 32,
                 shuffle: bool = True, seed: Optional[int] = None,
                 num_workers: Optional[int] = None,
                 prefetch_batches: int = 2,
                 drop_last: bool = False,
                 pin_memory: bool = True,
                 persistent_workers: bool = True,
                 timeout: float = 10.0):
        """
        Initialize DataLoader with optimized pinned memory handling.
        
        Args:
            dataset: Dataset to load from
            batch_size: Number of samples per batch
            shuffle: Whether to shuffle data
            seed: Random seed for shuffling
            num_workers: Number of worker processes (auto-detected if None)
            prefetch_batches: Number of batches to prefetch
            drop_last: Whether to drop incomplete last batch
            pin_memory: Use pinned memory for faster GPU transfers (handled internally)
            persistent_workers: Keep workers alive between epochs
            timeout: Worker timeout in seconds
        """
        self.dataset = dataset
        self.batch_size = int(batch_size)
        self.shuffle = shuffle
        self.seed = seed
        self.prefetch_batches = max(0, int(prefetch_batches))
        self.drop_last = bool(drop_last)
        self.pin_memory = pin_memory
        self.persistent_workers = persistent_workers
        self.timeout = timeout

        if num_workers is None:
            cores = os.cpu_count() or 2
            self.num_workers = max(1, min(8, cores - 1))
        else:
            self.num_workers = max(0, int(num_workers))

        # Multiprocessing components
        self._workers = []
        self._index_queues = []
        self._data_queue = None
        self._shutdown_event = None
        
        # Performance monitoring
        self._stats = {
            'batches_loaded': 0,
            'total_load_time': 0.0,
            'avg_batch_time': 0.0
        }

    def __len__(self):
        n = len(self.dataset)
        if self.drop_last:
            return n // self.batch_size
        return (n + self.batch_size - 1) // self.batch_size

    def get_stats(self):
        """Get performance statistics."""
        return self._stats.copy()

    def reset_stats(self):
        """Reset performance statistics."""
        self._stats = {
            'batches_loaded': 0,
            'total_load_time': 0.0,
            'avg_batch_time': 0.0
        }

    def __getitem__(self, idx):
        """Get a specific batch by index. Enables random.choice(dataloader)."""
        if idx < 0 or idx >= len(self):
            raise IndexError(f"Batch index {idx} out of range [0, {len(self)})")
        # Get all batch indices for consistent ordering
        batches = list(self._batch_indices())
        batch_idxs = batches[idx]
        # Load the batch synchronously
        batch_data = [self.dataset[i] for i in batch_idxs]
        return self._collate_batch(batch_data)

    def _start_workers(self):
        """Start multiprocessing workers."""
        if self.num_workers == 0 or self._workers:
            return
        
        # Choose context based on platform: fork on Unix-like systems, spawn on Windows
        import platform
        if platform.system() in ('Linux', 'Darwin'):  # Unix-like systems
            try:
                ctx = mp.get_context('fork')  # Faster on Unix
            except RuntimeError:
                ctx = mp  # Fallback to default
        else:  # Windows and others
            try:
                ctx = mp.get_context('spawn')  # Required for Windows
            except RuntimeError:
                ctx = mp  # Fallback to default
        
        self._data_queue = ctx.Queue(maxsize=self.prefetch_batches * 2)
        self._shutdown_event = ctx.Event()
        
        for worker_id in range(self.num_workers):
            index_queue = ctx.Queue(maxsize=self.prefetch_batches)
            self._index_queues.append(index_queue)
            
            worker = ctx.Process(
                target=DataLoader._worker_loop,
                args=(self.dataset, index_queue, self._data_queue, worker_id, self.pin_memory)
            )
            worker.daemon = True
            worker.start()
            self._workers.append(worker)
            
        print(f"[DataLoader] Started {len(self._workers)} worker processes using {ctx._name if hasattr(ctx, '_name') else 'default'} context")

    def _stop_workers(self):
        """Stop multiprocessing workers."""
        if not self._workers:
            return
            
        # Send shutdown signals
        for index_queue in self._index_queues:
            try:
                index_queue.put(None, timeout=1)
            except:
                pass
                
        # Wait for workers to finish
        for worker in self._workers:
            worker.join(timeout=2)
            if worker.is_alive():
                worker.terminate()
                worker.join()
                
        # Clean up
        self._workers.clear()
        self._index_queues.clear()
        if self._data_queue:
            self._data_queue.close()
            self._data_queue = None
        self._shutdown_event = None
        
        print("[DataLoader] Stopped all worker processes")

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
        """Optimized iteration with multiprocessing support."""
        if self.num_workers == 0:
            return self._single_process_iter()
        else:
            return self._multi_process_iter()
            
    def _single_process_iter(self):
        """Single process iteration (fallback)."""
        batches = list(self._batch_indices())
        
        for batch_idxs in batches:
            start_time = time.time()
            batch_data = [self.dataset[i] for i in batch_idxs]
            X, y = self._collate_batch(batch_data)
            
            # Update stats
            load_time = time.time() - start_time
            self._stats['batches_loaded'] += 1
            self._stats['total_load_time'] += load_time
            self._stats['avg_batch_time'] = self._stats['total_load_time'] / self._stats['batches_loaded']
            
            yield X, y
            
    def _multi_process_iter(self):
        """Multiprocessing iteration with advanced prefetching."""
        batches = list(self._batch_indices())
        
        # Start workers if not persistent or not already started
        if not self.persistent_workers or not self._workers:
            self._start_workers()
            
        try:
            # Submit initial batches for prefetching
            submitted = 0
            for i in range(min(self.prefetch_batches, len(batches))):
                self._index_queues[i % self.num_workers].put(batches[i], timeout=self.timeout)
                submitted += 1
                
            # Process batches
            for batch_idx in range(len(batches)):
                start_time = time.time()
                
                # Submit next batch for prefetching
                if submitted < len(batches):
                    worker_id = submitted % self.num_workers
                    self._index_queues[worker_id].put(batches[submitted], timeout=self.timeout)
                    submitted += 1
                
                # Get processed batch
                try:
                    indices, batch_data = self._data_queue.get(timeout=self.timeout)
                    X, y = self._collate_batch(batch_data)
                    
                    # Update stats
                    load_time = time.time() - start_time
                    self._stats['batches_loaded'] += 1
                    self._stats['total_load_time'] += load_time
                    self._stats['avg_batch_time'] = self._stats['total_load_time'] / self._stats['batches_loaded']
                    
                    yield X, y
                    
                except queue.Empty:
                    raise RuntimeError(f"DataLoader worker timeout after {self.timeout}s")
                    
        finally:
            if not self.persistent_workers:
                self._stop_workers()

    def __repr__(self):
        return (f"<DataLoader: {len(self)} batches, "
                f"batch_size={self.batch_size}, "
                f"shuffle={self.shuffle}, seed={self.seed}, "
                f"num_workers={self.num_workers}, "
                f"prefetch_batches={self.prefetch_batches}, "
                f"pin_memory={self.pin_memory}, "
                f"persistent_workers={self.persistent_workers}>")

    def close(self):
        """Clean up resources."""
        self._stop_workers()


# Image loading constants
IMG_EXTS = (
    '.png', '.jpg', '.jpeg', '.bmp', '.gif',
    '.tif', '.tiff', '.webp', '.jfif', '.avif',
    '.heif', '.heic'
)


class ImageFolder(Dataset):
    def __init__(
        self,
        root: str,
        img_shape: tuple = None,          # (H, W)
        img_mode: str = "RGB",            # "RGB", "L", etc.
        img_normalize: bool = True,       # /255 -> float
        img_transform: callable = None,   # after numpy conversion
        target_transform: callable = None,
        img_dtype=xp.float32,            # handled by Tensor(...)
        target_dtype=xp.int64,           # handled by Tensor(...)
        chw: bool = True                 # return CxHxW if True, else HxWxC
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
        # Try Albumentations-style call
        try:
            out = self.img_transform(image=arr)
            if isinstance(out, dict) and "image" in out:
                return out["image"]
        except TypeError:
            pass
        # Fallback: plain callable expecting ndarray
        return self.img_transform(arr)

    def _load_image(self, path: str) -> np.ndarray:
        """Optimized image loading with OpenCV."""
        mode = (self.img_mode or "RGB").upper()
        if mode in ("L", "GRAY", "GREY", "GRAYSCALE"):
            flag = cv2.IMREAD_GRAYSCALE
        elif mode == "RGBA":
            flag = cv2.IMREAD_UNCHANGED  # preserve alpha if present
        else:
            flag = cv2.IMREAD_COLOR  # BGR
        
        # Avoid EXIF orientation work
        try:
            flag |= cv2.IMREAD_IGNORE_ORIENTATION
        except Exception:
            pass

        arr = cv2.imread(path, flag)
        if arr is None:
            raise ValueError(f"Failed to read image: {path}")

        # Convert channel order to match RGB/RGBA expectations
        if mode == "RGB" and arr.ndim == 3 and arr.shape[2] == 3:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
        elif mode == "RGBA" and arr.ndim == 3 and arr.shape[2] == 4:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGRA2RGBA)

        # Resize if requested (cv2 expects (W,H))
        if self.img_shape is not None:
            h, w = self.img_shape
            arr = cv2.resize(arr, (int(w), int(h)), interpolation=cv2.INTER_LINEAR)
        
        if arr.ndim == 2:
            arr = arr[:, :, None]
        
        if self.img_transform:
            arr = self._apply_img_transform(arr)
        
        if self.chw:
            arr = np.transpose(arr, (2, 0, 1))  # C,H,W
        
        if self.img_normalize:
            arr = arr.astype(np.float32) / 255.0
        
        return arr

    def __getitem__(self, idx: int):
        img_path = self.images[idx]
        target_name = self.targets[idx]

        image = self._load_image(img_path)
        target = self.target_mapping[target_name]

        if self.target_transform:
            target = self.target_transform(target)

        # Convert to Tensor with dtype specified in init
        return Tensor(image, dtype=self.img_dtype), Tensor(target, dtype=self.target_dtype)

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