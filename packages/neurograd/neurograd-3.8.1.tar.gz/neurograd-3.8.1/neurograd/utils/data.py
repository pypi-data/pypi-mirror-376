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
- Load balancing across worker processes
- CUDA-safe spawn context for GPU training
- Reusable pinned memory pools for efficiency
"""

from neurograd import float32, xp
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
        # Import Tensor locally to avoid serialization issues
        from neurograd import Tensor
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
    # Class-level pinned memory pool for reuse across instances
    _pinned_pool = None
    
    @staticmethod
    def _worker_loop(dataset, index_queue, data_queue, worker_id, pin_memory=False):
        """Worker process function for loading data samples."""
        # Set OpenCV threading for worker process
        cv2.setNumThreads(1)
        
        try:
            while True:
                try:
                    indices = index_queue.get(timeout=1)
                    if indices is None:  # Shutdown signal
                        break
                        
                    # Process batch
                    batch_data = []
                    for idx in indices:
                        try:
                            sample = dataset[idx]
                            batch_data.append(sample)
                        except Exception as e:
                            print(f"Worker {worker_id}: Error loading sample {idx}: {e}")
                            continue
                    
                    if batch_data:
                        data_queue.put((worker_id, indices, batch_data))
                        
                except queue.Empty:
                    continue
                except (EOFError, BrokenPipeError):
                    break
                except Exception as e:
                    print(f"Worker {worker_id}: Unexpected error: {e}")
                    break
        finally:
            # Clean up any resources
            pass
    
    def _collate_batch(self, batch_data):
        """Efficiently collate batch data into tensors with optional pinned memory."""
        if not batch_data:
            return None, None
            
        # Separate samples and targets
        samples, targets = zip(*batch_data)
        
        # Convert to arrays
        sample_arrays = [s.data if hasattr(s, 'data') else s for s in samples]
        target_arrays = [t.data if hasattr(t, 'data') else t for t in targets]
        
        # Stack arrays using numpy first
        X_data = np.stack(sample_arrays, axis=0)
        y_data = np.stack(target_arrays, axis=0) if target_arrays[0].ndim > 0 else np.array(target_arrays)
        
        # Use standard pinned memory approach when GPU is available
        if self.pin_memory and not IS_CPU:
            X_data = self._pin_memory(X_data)
            y_data = self._pin_memory(y_data)
        
        # Import Tensor locally to avoid serialization issues
        from neurograd import Tensor
        # Create tensors
        X = Tensor(X_data, dtype=samples[0].dtype if hasattr(samples[0], 'dtype') else X_data.dtype)
        y = Tensor(y_data, dtype=targets[0].dtype if hasattr(targets[0], 'dtype') else y_data.dtype)
            
        return X, y
    
    def _pin_memory(self, arr):
        """Create pinned CPU memory for faster GPU transfers with reusable pool."""
        try:
            import cupy as cp
            if not cp.cuda.is_available():
                return arr
            
            # If array is already on GPU, no need to pin
            if hasattr(arr, '__array_interface__') and arr.__array_interface__.get('typestr'):
                # Check if this is already a CuPy array
                if hasattr(arr, 'device') or 'cupy' in str(type(arr)):
                    return arr  # Already on GPU, no pinning needed
            
            # Convert CuPy arrays to NumPy for pinning
            if hasattr(arr, 'get'):  # CuPy array
                arr = arr.get()  # Convert to NumPy
            elif not isinstance(arr, np.ndarray):
                arr = np.asarray(arr)  # Ensure it's a NumPy array
                
            # Initialize pool if needed
            if DataLoader._pinned_pool is None:
                DataLoader._pinned_pool = cp.get_default_pinned_memory_pool()
            
            # Create new pinned memory with exact size needed
            try:
                # Calculate the exact size needed for the array
                total_elements = arr.size
                element_size = arr.dtype.itemsize
                required_bytes = total_elements * element_size
                
                pinned_mem = DataLoader._pinned_pool.malloc(required_bytes)
                
                # Create numpy array from buffer with correct size
                pinned_array = np.frombuffer(pinned_mem, dtype=arr.dtype, count=total_elements).reshape(arr.shape)
                pinned_array[...] = arr
                
                # Store reference to prevent garbage collection
                pinned_array._pinned_mem_ref = pinned_mem
                return pinned_array
                
            except (cp.cuda.memory.OutOfMemoryError, ValueError) as e:
                # Fallback to regular array if pinning fails
                print(f"Warning: Pinned memory allocation failed ({e}), using regular memory")
                return arr
            
        except ImportError:
            pass
        return arr
    def __init__(self, dataset: Dataset, batch_size: int = 32,
                 shuffle: bool = True, seed: Optional[int] = None,
                 num_workers: Optional[int] = None,
                 prefetch_batches: int = 4,  # Increased default for better throughput
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
            prefetch_batches: Number of batches to prefetch (increased default for better throughput)
            drop_last: Whether to drop incomplete last batch
            pin_memory: Use pinned memory for faster GPU transfers (handled internally)
            persistent_workers: Keep workers alive between epochs
            timeout: Worker timeout in seconds
        """
        self.dataset = dataset
        self.batch_size = int(batch_size)
        self.shuffle = shuffle
        self.seed = seed
        self.prefetch_batches = max(2, int(prefetch_batches))  # Minimum 2 for good overlap
        self.drop_last = bool(drop_last)
        self.pin_memory = pin_memory
        self.persistent_workers = persistent_workers
        self.timeout = timeout

        # Optimize worker count for ImageNet-scale datasets
        if num_workers is None:
            cores = os.cpu_count() or 4
            # For large datasets like ImageNet, use more workers for I/O bound operations
            if len(dataset) > 100000:  # Large dataset heuristic
                self.num_workers = max(1, min(16, cores))  # Up to 16 workers for large datasets
            else:
                self.num_workers = max(1, min(8, cores - 1))
        else:
            self.num_workers = max(0, int(num_workers))

        # Multiprocessing components
        self._workers = []
        self._index_queues = []
        self._data_queue = None
        self._shutdown_event = None
        self._worker_load = []  # Track worker load for better balancing
        
        # Enhanced performance monitoring
        self._stats = {
            'batches_loaded': 0,
            'total_load_time': 0.0,
            'avg_batch_time': 0.0,
            'worker_utilization': 0.0,
            'queue_wait_time': 0.0,
            'data_loading_time': 0.0
        }

    def __len__(self):
        n = len(self.dataset)
        if self.drop_last:
            return n // self.batch_size
        return (n + self.batch_size - 1) // self.batch_size

    def get_stats(self):
        """Get performance statistics."""
        stats = self._stats.copy()
        stats['num_workers'] = self.num_workers
        stats['prefetch_batches'] = self.prefetch_batches
        stats['batch_size'] = self.batch_size
        stats['dataset_size'] = len(self.dataset)
        stats['total_batches'] = len(self)
        return stats

    def print_performance_report(self):
        """Print detailed performance analysis for debugging."""
        stats = self.get_stats()
        print(f"\n{'='*60}")
        print(f"DataLoader Performance Report")
        print(f"{'='*60}")
        print(f"Configuration:")
        print(f"  Workers: {stats['num_workers']}")
        print(f"  Prefetch batches: {stats['prefetch_batches']}")
        print(f"  Batch size: {stats['batch_size']}")
        print(f"  Dataset size: {stats['dataset_size']:,}")
        print(f"  Total batches: {stats['total_batches']:,}")
        print(f"  Pin memory: {self.pin_memory}")
        print(f"  Persistent workers: {self.persistent_workers}")
        
        if stats['batches_loaded'] > 0:
            print(f"\nPerformance:")
            print(f"  Batches loaded: {stats['batches_loaded']:,}")
            print(f"  Average batch time: {stats['avg_batch_time']:.3f}s")
            print(f"  Throughput: {stats['batches_loaded']/stats['total_load_time']:.1f} batches/s")
            print(f"  Images/sec: {(stats['batches_loaded'] * stats['batch_size'])/stats['total_load_time']:.1f}")
            
            if 'queue_wait_time' in stats:
                avg_queue_wait = stats['queue_wait_time'] / stats['batches_loaded']
                print(f"  Avg queue wait: {avg_queue_wait:.3f}s ({avg_queue_wait/stats['avg_batch_time']*100:.1f}% of batch time)")
        
        if self._workers:
            print(f"\nWorker Status:")
            print(f"  Active workers: {len(self._workers)}")
            print(f"  Worker loads: {self._worker_load}")
        else:
            print(f"\nWorkers: Not active (single-process mode)")
        print(f"{'='*60}\n")

    def reset_stats(self):
        """Reset performance statistics."""
        self._stats = {
            'batches_loaded': 0,
            'total_load_time': 0.0,
            'avg_batch_time': 0.0
        }

    def __getitem__(self, idx):
        """Get a specific batch by index with multiprocessing safety."""
        if idx < 0 or idx >= len(self):
            raise IndexError(f"Batch index {idx} out of range [0, {len(self)})")
            
        # Always use single-process loading for random access to avoid deadlocks
        # with worker processes that are designed for sequential iteration
        batches = list(self._batch_indices())
        batch_idxs = batches[idx]
        
        # Load the batch synchronously in main process
        batch_data = []
        for i in batch_idxs:
            try:
                sample = self.dataset[i]
                batch_data.append(sample)
            except Exception as e:
                print(f"Error loading sample {i} in __getitem__: {e}")
                continue
                
        if not batch_data:
            raise RuntimeError(f"No valid samples in batch {idx}")
            
        return self._collate_batch(batch_data)

    def _start_workers(self):
        """Start multiprocessing workers with optimized queue sizes for high throughput."""
        if self.num_workers == 0 or self._workers:
            return
        
        # Always use spawn to avoid CUDA context sharing issues
        # Spawn creates completely isolated processes with clean state
        try:
            ctx = mp.get_context('spawn')
        except RuntimeError:
            # Fallback to default context if spawn is not available
            ctx = mp
        
        # Optimize queue sizes for high throughput
        # Data queue should be large enough to buffer multiple batches from all workers
        data_queue_size = max(self.num_workers * 2, self.prefetch_batches * 2)
        self._data_queue = ctx.Queue(maxsize=data_queue_size)
        self._shutdown_event = ctx.Event()
        
        for worker_id in range(self.num_workers):
            # Each worker gets a larger queue to reduce blocking
            index_queue_size = max(4, self.prefetch_batches)
            index_queue = ctx.Queue(maxsize=index_queue_size)
            self._index_queues.append(index_queue)
            
            worker = ctx.Process(
                target=DataLoader._worker_loop,
                args=(self.dataset, index_queue, self._data_queue, worker_id, self.pin_memory)
            )
            worker.daemon = True
            worker.start()
            self._workers.append(worker)
            
        # Initialize worker load tracking
        self._worker_load = [0] * self.num_workers
            
        print(f"[DataLoader] Started {len(self._workers)} worker processes (queues: data={data_queue_size}, index={index_queue_size}) using spawn context (CUDA-safe)")
        
        # Warm up workers by submitting initial work
        if hasattr(self, '_warmup_workers'):
            self._warmup_workers()

    def _stop_workers(self):
        """Stop multiprocessing workers with improved safety."""
        if not self._workers:
            return
        
        print(f"[DataLoader] Stopping {len(self._workers)} workers...")
        
        # Send shutdown signals to all workers
        shutdown_success = 0
        for i, index_queue in enumerate(self._index_queues):
            try:
                # Try multiple times to ensure signal is sent
                for attempt in range(3):
                    try:
                        index_queue.put(None, timeout=0.5)
                        shutdown_success += 1
                        break
                    except queue.Full:
                        if attempt == 2:
                            print(f"Warning: Could not send shutdown signal to worker {i}")
                        continue
            except Exception as e:
                print(f"Error sending shutdown to worker {i}: {e}")
                
        # Wait for workers with increasing timeouts
        for i, worker in enumerate(self._workers):
            try:
                worker.join(timeout=3)  # Increased timeout
                if worker.is_alive():
                    print(f"Worker {i} did not terminate gracefully, forcing termination")
                    worker.terminate()
                    worker.join(timeout=1)
                    if worker.is_alive():
                        print(f"Warning: Worker {i} could not be terminated")
            except Exception as e:
                print(f"Error stopping worker {i}: {e}")
                
        # Clean up resources
        self._workers.clear()
        self._worker_load.clear()
        
        # Close queues safely
        for queue in self._index_queues:
            try:
                # Drain any remaining items
                while True:
                    try:
                        queue.get_nowait()
                    except queue.Empty:
                        break
                queue.close()
            except Exception:
                pass
        self._index_queues.clear()
        
        if self._data_queue:
            try:
                # Drain data queue
                while True:
                    try:
                        self._data_queue.get_nowait()
                    except queue.Empty:
                        break
                self._data_queue.close()
            except Exception:
                pass
            self._data_queue = None
            
        self._shutdown_event = None
        
        print(f"[DataLoader] Workers stopped (signals sent: {shutdown_success}/{len(self._index_queues)})")

    def _get_best_worker(self):
        """Get the worker with the lowest current load for better load balancing."""
        if not self._worker_load:
            return 0
        return self._worker_load.index(min(self._worker_load))

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
            # Ensure we don't have any existing workers if not using persistent workers
            if self._workers and not self.persistent_workers:
                self._stop_workers()
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
        """Multiprocessing iteration with advanced prefetching and performance monitoring."""
        batches = list(self._batch_indices())
        
        # Start workers if not persistent or not already started
        if not self.persistent_workers or not self._workers:
            self._start_workers()
            
        # Performance tracking
        iteration_start = time.time()
        queue_wait_times = []
        data_load_times = []
        
        try:
            # Submit initial batches for prefetching with load balancing
            submitted = 0
            prefetch_start = time.time()
            
            initial_prefetch = min(self.prefetch_batches * self.num_workers, len(batches))
            for i in range(initial_prefetch):
                worker_id = self._get_best_worker()
                batch_indices = batches[i]
                try:
                    self._index_queues[worker_id].put(batch_indices, timeout=self.timeout)
                    # Track load by number of samples for accurate balancing
                    self._worker_load[worker_id] += len(batch_indices)
                    submitted += 1
                except queue.Full:
                    print(f"Warning: Worker {worker_id} queue full, skipping prefetch")
                    break
            
            prefetch_time = time.time() - prefetch_start
            if submitted > 0:
                print(f"[DataLoader] Pre-submitted {submitted} batches to {self.num_workers} workers in {prefetch_time:.3f}s")
                
            # Process batches
            for batch_idx in range(len(batches)):
                batch_start_time = time.time()
                
                # Submit next batch for prefetching with load balancing
                if submitted < len(batches):
                    worker_id = self._get_best_worker()
                    try:
                        self._index_queues[worker_id].put(batches[submitted], timeout=self.timeout)
                        # Track load by number of samples for accurate balancing
                        self._worker_load[worker_id] += len(batches[submitted])
                        submitted += 1
                    except queue.Full:
                        print(f"Warning: Worker {worker_id} queue full during iteration")
                
                # Get processed batch
                queue_start = time.time()
                try:
                    worker_id, indices, batch_data = self._data_queue.get(timeout=self.timeout)
                    queue_wait_time = time.time() - queue_start
                    queue_wait_times.append(queue_wait_time)
                    
                    # Update worker load accurately - decrement by samples, not batches
                    if worker_id < len(self._worker_load) and self._worker_load[worker_id] > 0:
                        self._worker_load[worker_id] -= len(indices)
                    
                    collate_start = time.time()
                    X, y = self._collate_batch(batch_data)
                    collate_time = time.time() - collate_start
                    
                    # Update stats with detailed timing
                    total_batch_time = time.time() - batch_start_time
                    self._stats['batches_loaded'] += 1
                    self._stats['total_load_time'] += total_batch_time
                    self._stats['avg_batch_time'] = self._stats['total_load_time'] / self._stats['batches_loaded']
                    self._stats['queue_wait_time'] += queue_wait_time
                    
                    # Periodic performance reporting for debugging
                    if batch_idx > 0 and batch_idx % 50 == 0:
                        avg_queue_wait = sum(queue_wait_times[-50:]) / min(50, len(queue_wait_times))
                        current_throughput = 50 / sum([self._stats['total_load_time'] / max(1, self._stats['batches_loaded'])] * 50)
                        worker_loads = ', '.join([f"W{i}:{load}" for i, load in enumerate(self._worker_load)])
                        print(f"[DataLoader] Batch {batch_idx}: avg_queue_wait={avg_queue_wait:.3f}s, "
                              f"throughput={current_throughput:.1f}batch/s, loads=[{worker_loads}]")
                    
                    yield X, y
                    
                except queue.Empty:
                    print(f"[DataLoader] Worker timeout after {self.timeout}s at batch {batch_idx}")
                    print(f"[DataLoader] Worker loads: {self._worker_load}")
                    print(f"[DataLoader] Submitted: {submitted}/{len(batches)}")
                    raise RuntimeError(f"DataLoader worker timeout after {self.timeout}s")
                    
        finally:
            total_time = time.time() - iteration_start
            if self._stats['batches_loaded'] > 0:
                print(f"[DataLoader] Iteration complete: {self._stats['batches_loaded']} batches in {total_time:.2f}s "
                      f"({self._stats['batches_loaded']/total_time:.1f} batches/s)")
            
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
        """Optimized image loading with OpenCV and simple format handling."""
        # Use standard OpenCV loading with simpler conversion logic
        mode = self.img_mode.upper() if self.img_mode else "RGB"
        
        if mode in ("L", "GRAY", "GREY", "GRAYSCALE"):
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is not None and len(img.shape) == 2:
                img = img[:, :, np.newaxis]
        else:
            img = cv2.imread(path, cv2.IMREAD_COLOR)
            if img is not None and mode == "RGB":
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            elif img is not None and mode == "RGBA":
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
        
        if img is None:
            raise ValueError(f"Failed to load image: {path}")
        
        # Resize if needed
        if self.img_shape is not None:
            img = cv2.resize(img, (self.img_shape[1], self.img_shape[0]))
        
        # Apply transforms
        if self.img_transform:
            img = self._apply_img_transform(img)
        
        # Convert to CHW if requested
        if self.chw and img.ndim == 3:
            img = img.transpose(2, 0, 1)
        
        # Normalize
        if self.img_normalize:
            img = img.astype(np.float32) / 255.0
        
        return img

    def __getitem__(self, idx: int):
        img_path = self.images[idx]
        target_name = self.targets[idx]

        image = self._load_image(img_path)
        target = self.target_mapping[target_name]

        if self.target_transform:
            target = self.target_transform(target)

        # Import Tensor locally to avoid serialization issues in multiprocessing
        from neurograd import Tensor
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



class OneHotEncoder:
    def __init__(self, num_classes: int, label_smoothing: float = 0.0):
        self.num_classes = num_classes
        self.label_smoothing = label_smoothing
    
    def __call__(self, class_idx: int):
        # Import xp locally to avoid serialization issues in multiprocessing
        from neurograd import xp
        one_hot = xp.zeros(self.num_classes, dtype=xp.float32)
        if self.label_smoothing > 0:
            smooth_value = self.label_smoothing / self.num_classes
            one_hot.fill(smooth_value)
            one_hot[class_idx] = 1.0 - self.label_smoothing + smooth_value
        else:
            one_hot[class_idx] = 1.0
        return one_hot