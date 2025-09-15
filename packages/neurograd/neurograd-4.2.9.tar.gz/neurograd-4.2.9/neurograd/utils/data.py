import math
import random
import os
import numpy as np
from neurograd import xp, Tensor, float32, int64
from typing import Optional, List, Tuple, Union, Callable, Dict
import glob
from collections import deque
from concurrent.futures import ThreadPoolExecutor

# Try to import DALI first - this determines our capabilities
try:
    import nvidia.dali as dali
    from nvidia.dali import pipeline_def, Pipeline
    import nvidia.dali.fn as fn
    import nvidia.dali.types as types
    from nvidia.dali.plugin.pytorch import DALIGenericIterator, LastBatchPolicy
    from nvidia.dali.backend import PreallocateDeviceMemory, PreallocatePinnedMemory
    DALI_AVAILABLE = True
except ImportError:
    DALI_AVAILABLE = False
    print("INFO: NVIDIA DALI not available. Falling back to OpenCV-based implementation.")
    print("      For maximum performance, install with: pip install --extra-index-url https://developer.download.nvidia.com/compute/redist nvidia-dali-cuda120")

# Image file extensions
IMG_EXTS = (
    '.png', '.jpg', '.jpeg', '.bmp', '.gif',
    '.tif', '.tiff', '.webp', '.jfif', '.avif',
    '.heif', '.heic'
)


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
        preview_x = self.X[:1]
        preview_y = self.y[:1]
        return (f"Dataset:\n"
                f"  Total samples: {len(self)}\n"
                f"  Input preview: {preview_x}\n"
                f"  Target preview: {preview_y}")


class ImageFolder(Dataset):
    """
    ImageFolder dataset class that handles image loading and preprocessing.
    All data loading parameters are now handled by the DataLoader.
    """
    def __init__(
        self,
        root: str,
        img_shape: tuple = None,          # (H, W)
        img_mode: str = "RGB",            # "RGB", "L", etc.
        img_normalize: bool = True,       # /255 -> float
        img_transform: callable = None,   # DALI pipeline or callable
        one_hot_targets: bool = True,     # Convert targets to one-hot encoding
        img_dtype=xp.float32,
        target_dtype=xp.int64,
        chw: bool = True,                 # return CxHxW if True, else HxWxC
    ):
        self.root = root
        self.img_shape = img_shape
        self.img_mode = img_mode
        self.img_normalize = img_normalize
        self.img_transform = img_transform
        self.one_hot_targets = one_hot_targets
        self.img_dtype = img_dtype
        self.target_dtype = target_dtype
        self.chw = chw

        self.images: List[str] = []
        self.targets: List[str] = []
        self._collect_paths()

        # Check if we have any images
        if len(self.images) == 0:
            raise ValueError(f"No images found in {root} with supported extensions: {IMG_EXTS}")

        # Stable class mapping
        self.target_names = sorted(set(self.targets))
        self.target_mapping = {name: i for i, name in enumerate(self.target_names)}
        self.num_classes = len(self.target_names)
        
        # Create one-hot mapping
        self.one_hot_mapping: Dict[int, np.ndarray] = {}
        for class_idx in range(self.num_classes):
            one_hot = np.zeros(self.num_classes, dtype=np.float32)
            one_hot[class_idx] = 1.0
            self.one_hot_mapping[class_idx] = one_hot
        
        # Convert targets to numeric labels
        self.numeric_targets = [self.target_mapping[t] for t in self.targets]

        print(f"ImageFolder initialized: {len(self)} samples, {self.num_classes} classes")

    def get_class_name(self, class_idx: int) -> str:
        """Get class name from class index"""
        if class_idx < 0 or class_idx >= len(self.target_names):
            raise ValueError(f"Class index {class_idx} out of range [0, {len(self.target_names)-1}]")
        return self.target_names[class_idx]
    
    def get_class_index(self, class_name: str) -> int:
        """Get class index from class name"""
        if class_name not in self.target_mapping:
            raise ValueError(f"Class name '{class_name}' not found in dataset")
        return self.target_mapping[class_name]
    
    def get_one_hot(self, class_idx: int) -> np.ndarray:
        """Get one-hot encoding from class index"""
        if class_idx not in self.one_hot_mapping:
            raise ValueError(f"Class index {class_idx} not found in one-hot mapping")
        return self.one_hot_mapping[class_idx]
    
    def get_class_from_one_hot(self, one_hot: np.ndarray) -> int:
        """Get class index from one-hot encoding"""
        if one_hot.shape != (self.num_classes,):
            raise ValueError(f"One-hot encoding must have shape ({self.num_classes},), got {one_hot.shape}")
        
        class_idx = np.argmax(one_hot)
        if one_hot[class_idx] != 1.0:
            raise ValueError("One-hot encoding must have exactly one element set to 1.0")
            
        return class_idx

    def _collect_paths(self):
        """Collect image paths and their class labels"""
        if not os.path.exists(self.root) or not os.path.isdir(self.root):
            raise ValueError(f"Root directory {self.root} does not exist or is not a directory")
        
        # Method 1: Class folders (ImageNet style)
        for class_name in os.listdir(self.root):
            class_path = os.path.join(self.root, class_name)
            if not os.path.isdir(class_path):
                continue
            
            for ext in IMG_EXTS:
                pattern = os.path.join(class_path, f"*{ext}")
                for img_path in glob.glob(pattern):
                    self.images.append(img_path)
                    self.targets.append(class_name)
        
        # Method 2: If no class folders found, walk directory tree
        if not self.images:
            for r, _, files in os.walk(self.root):
                for f in files:
                    if any(f.lower().endswith(ext) for ext in IMG_EXTS):
                        p = os.path.join(r, f)
                        cls = os.path.basename(os.path.dirname(p))
                        self.images.append(p)
                        self.targets.append(cls)


    def get_dali_pipeline(self, batch_size: int, shuffle: bool = True, 
                         device: str = "cpu", num_threads: int = 4, 
                         seed: int = 42):
        """Create DALI pipeline for this dataset (only when DALI is available)"""
        if not DALI_AVAILABLE:
            return None
            
        # If user provided an entire DALI Pipeline instance, return it directly.
        if isinstance(self.img_transform, Pipeline):
            return self.img_transform

        # Device-specific configuration
        device_id = 0 if device == "gpu" else None
        prefetch_depth = 3 if device == "gpu" else 2  # More prefetch for GPU
        h, w = self.img_shape if self.img_shape is not None else (224, 224)
        
        @pipeline_def(batch_size=batch_size, num_threads=num_threads, 
                     device_id=device_id, seed=seed, prefetch_queue_depth=prefetch_depth)
        def image_pipeline():
            # Create file reader
            if shuffle:
                images, labels = fn.readers.file(
                    files=self.images,
                    labels=self.numeric_targets,
                    random_shuffle=True,
                    initial_fill=batch_size * 4,
                    name="Reader"
                )
            else:
                images, labels = fn.readers.file(
                    files=self.images,
                    labels=self.numeric_targets,
                    random_shuffle=False,
                    name="Reader"
                )

            # Device-specific processing
            if device == "gpu":
                # GPU-accelerated pipeline
                images = fn.decoders.image(images, device="mixed", output_type=types.RGB,
                                           size=[h, w])
                images = images.gpu()  # Move to GPU for subsequent operations
            else:
                # CPU-only processing
                images = fn.decoders.image(images, device="cpu", output_type=types.RGB,
                                           size=[h, w])

            # Handle grayscale conversion if needed
            if self.img_mode.upper() in ("L", "GRAY", "GREY", "GRAYSCALE"):
                images = fn.color_space_conversion(
                    images, image_type=types.RGB, output_type=types.GRAY
                )

            # Apply custom transforms if provided
            if self.img_transform and callable(self.img_transform):
                try:
                    images = self.img_transform(images)
                except Exception as e:
                    print(f"WARNING: Failed to apply DALI callable transform. Error: {e}. Skipping transform.")

            # Normalize and format
            if self.img_normalize:
                # Use crop_mirror_normalize for better performance
                images = fn.crop_mirror_normalize(
                    images,
                    dtype=types.FLOAT,
                    output_layout="CHW" if self.chw else "HWC",
                    mean=[0.485 * 255, 0.456 * 255, 0.406 * 255],  # ImageNet stats
                    std=[0.229 * 255, 0.224 * 255, 0.225 * 255]
                )
            else:
                images = fn.cast(images, dtype=types.FLOAT)
                if self.chw:
                    images = fn.transpose(images, perm=[2, 0, 1])
            
            # Apply one-hot encoding if requested
            if self.one_hot_targets:
                labels = fn.one_hot(labels, num_classes=self.num_classes)
            
            # Move labels to GPU if using GPU pipeline
            if device == "gpu":
                labels = labels.gpu()
            
            return images, labels

        return image_pipeline()

    def _apply_img_transform(self, arr: np.ndarray) -> np.ndarray:
        """Apply image transforms (OpenCV fallback path)"""
        if self.img_transform is None:
            return arr
            
        if isinstance(self.img_transform, Pipeline):
            print("WARNING: DALI Pipeline transform provided but running in fallback numpy/OpenCV mode. "
                  "Cannot apply Pipeline to ndarray; skipping transform.")
            return arr
            
        # Try Albumentations-style call
        try:
            out = self.img_transform(image=arr)
            if isinstance(out, dict) and "image" in out:
                return out["image"]
            return out
        except TypeError:
            pass

        # Fallback: plain callable expecting ndarray
        try:
            return self.img_transform(arr)
        except Exception as e:
            print(f"WARNING: img_transform callable raised an exception: {e}. Returning original image.")
            return arr

    def _load_image_opencv(self, path: str) -> np.ndarray:
        """Load image using OpenCV (fallback implementation)"""
        # OpenCV-only fast decode/resize
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

        # Convert channel order to match RGB/RGBA expectations
        if mode == "RGB" and arr.ndim == 3 and arr.shape[2] == 3:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
        elif mode == "RGBA" and arr.ndim == 3 and arr.shape[2] == 4:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGRA2RGBA)

        # Resize if requested
        if self.img_shape is not None:
            h, w = self.img_shape
            arr = cv2.resize(arr, (int(w), int(h)), interpolation=cv2.INTER_LINEAR)
        
        if arr.ndim == 2:
            arr = arr[:, :, None]
        
        # Apply transforms
        if self.img_transform:
            arr = self._apply_img_transform(arr)
        
        # Convert to CHW if requested
        if self.chw and arr.ndim == 3:
            arr = np.transpose(arr, (2, 0, 1))
        
        # Normalize
        if self.img_normalize:
            arr = arr.astype(np.float32) / 255.0
        else:
            arr = arr.astype(np.float32)
        
        return arr

    def __getitem__(self, idx: int):
        """Get single item - uses OpenCV fallback"""
        img_path = self.images[idx]
        target = self.numeric_targets[idx]
        
        # Load image using OpenCV
        image = self._load_image_opencv(img_path)
        
        # Apply one-hot encoding if requested
        if self.one_hot_targets:
            # Use our precomputed one-hot mapping
            target = self.one_hot_mapping[target]
            target_dtype = float32  # One-hot targets should be float
        else:
            target_dtype = self.target_dtype
        
        return Tensor(image, dtype=self.img_dtype), Tensor(target, dtype=target_dtype)

    def shuffle(self, seed: Optional[int] = None):
        """Shuffle the dataset"""
        rng = random.Random(seed) if seed is not None else random.Random()
        combined = list(zip(self.images, self.targets, self.numeric_targets))
        rng.shuffle(combined)
        self.images, self.targets, self.numeric_targets = zip(*combined)
        self.images = list(self.images)
        self.targets = list(self.targets)
        self.numeric_targets = list(self.numeric_targets)

    def __len__(self):
        return len(self.images)

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __str__(self):
        return (f"ImageFolder(root='{self.root}', samples={len(self)}, "
                f"classes={self.num_classes})")

    def __repr__(self):
        shape = None
        if len(self) > 0:
            try:
                image, _ = self[0]
                shape = tuple(image.shape)
            except Exception:
                shape = None
        
        return (f"ImageFolder(root='{self.root}', samples={len(self)}, "
                f"classes={self.num_classes}, "
                f"shape={shape}, img_dtype={self.img_dtype}, target_dtype={self.target_dtype}, "
                f"mode='{self.img_mode}', normalize={self.img_normalize}, chw={self.chw}, "
                f"one_hot_targets={self.one_hot_targets})")


class DataLoader:
    """
    DataLoader that handles all data loading parameters including device, threading, and prefetching.
    Automatically uses DALI when available and appropriate, with OpenCV fallback.
    """
    def __init__(
        self,
        dataset: Union[ImageFolder, Dataset],
        batch_size: int = 32,
        shuffle: bool = True,
        device: str = "cpu",
        num_workers: int = 4,
        prefetch_batches: int = 2,
        drop_last: bool = False,
        seed: Optional[int] = None,
    ):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.device = "gpu" if device in ["gpu", "cuda"] else "cpu"
        self.num_workers = max(0, int(num_workers))
        self.prefetch_batches = max(0, int(prefetch_batches))
        self.drop_last = drop_last
        self.seed = seed or 42
        
        self._pipeline = None
        self._dali_iter = None
        self._executor: Optional[ThreadPoolExecutor] = None
        
        # Preallocate memory for better performance
        if DALI_AVAILABLE:
            try:
                if self.device == "gpu":
                    PreallocateDeviceMemory(int(0.5 * 1024**3))  # 0.5GB GPU memory
                PreallocatePinnedMemory(int(0.25 * 1024**3))  # 0.25GB pinned memory
            except Exception as e:
                print(f"WARNING: Memory preallocation failed: {e}")
        
        # Determine if we should use DALI
        self.use_dali = (
            DALI_AVAILABLE and 
            isinstance(dataset, ImageFolder)
        )
        
        if self.use_dali:
            self._init_dali_pipeline()
        
        # Warn if GPU requested but not available
        if device in ["gpu", "cuda"] and not self.use_dali:
            print("WARNING: GPU device requested but DALI not available. Using CPU fallback.")
            self.device = "cpu"

    def _init_dali_pipeline(self):
        """Initialize the DALI pipeline"""
        if not self.use_dali or not isinstance(self.dataset, ImageFolder):
            return
        
        # Device-specific thread optimization
        if self.device == "gpu":
            num_threads = min(4, self.num_workers)  # Fewer threads for GPU
        else:
            num_threads = self.num_workers
        
        # Create pipeline
        self._pipeline = self.dataset.get_dali_pipeline(
            batch_size=self.batch_size,
            shuffle=self.shuffle,
            device=self.device,
            num_threads=num_threads,
            seed=self.seed
        )
        
        if self._pipeline is not None:
            # Build the pipeline
            self._pipeline.build()
            
            # Set appropriate last batch policy (FIXED: use enum instead of string)
            last_batch_policy = LastBatchPolicy.DROP if self.drop_last else LastBatchPolicy.PARTIAL
            
            # Create DALI iterator
            self._dali_iter = DALIGenericIterator(
                self._pipeline, 
                output_map=["images", "labels"],
                last_batch_policy=last_batch_policy,
                auto_reset=False,
                reader_name="Reader",
                prepare_first_batch=True  # Preload first batch
            )
            print(f"DALI pipeline initialized: batch_size={self.batch_size}, device={self.device}, "
                  f"num_threads={num_threads}")

    def __len__(self):
        n = len(self.dataset)
        if self.drop_last:
            return n // self.batch_size
        return (n + self.batch_size - 1) // self.batch_size

    def __iter__(self):
        """Main iteration - uses DALI when available, falls back otherwise"""
        if self.use_dali and self._dali_iter is not None:
            return self._dali_iterator()
        else:
            return self._regular_iterator()

    def _dali_iterator(self):
        """DALI-based iteration - maximum performance!"""
        for data in self._dali_iter:
            # Extract data from DALI output
            images = data[0]["images"]
            labels = data[0]["labels"]
            
            # Convert to neurograd tensors
            if self.device == "gpu":
                # Use DLPack for zero-copy conversion
                X = Tensor(xp.from_dlpack(images), dtype=self.dataset.img_dtype)
                y = Tensor(xp.from_dlpack(labels), dtype=self.dataset.target_dtype)
            else:
                # Convert to numpy arrays
                X = Tensor(images.numpy(), dtype=self.dataset.img_dtype)
                y = Tensor(labels.numpy(), dtype=self.dataset.target_dtype)
            
            yield X, y

    def _regular_iterator(self):
        """Regular iteration for non-DALI datasets with threading and prefetch"""
        batches = list(self._batch_indices())
        window = deque()
        next_to_submit = 0
        total = len(batches)

        # Prime the prefetch window
        pre = self.prefetch_batches if self.prefetch_batches > 0 else 0
        for _ in range(min(pre, total)):
            futs = self._schedule_batch(batches[next_to_submit])
            window.append(futs)
            next_to_submit += 1

        # Iterate in order; keep the window full
        for b in range(total):
            # If window is empty (prefetch=0) or drained, schedule current batch now
            if not window:
                futs = self._schedule_batch(batches[next_to_submit])
                window.append(futs)
                next_to_submit += 1

            futs = window.popleft()

            # Immediately schedule the next batch to keep the window full
            if next_to_submit < total and len(window) < self.prefetch_batches:
                next_futs = self._schedule_batch(batches[next_to_submit])
                window.append(next_futs)
                next_to_submit += 1

            # This blocks only if this batch isn't finished yet
            X, y = self._gather_batch(futs)
            yield X, y

    def _batch_indices(self):
        """Generate batch indices with optional shuffling"""
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

    def _ensure_executor(self):
        """Ensure thread executor is ready for fallback mode"""
        if self.num_workers > 0 and self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=self.num_workers)

    def _schedule_batch(self, idxs):
        """Schedule all sample loads in this batch and return the list of futures"""
        if self.num_workers > 0:
            self._ensure_executor()
            return [self._executor.submit(self.dataset.__getitem__, i) for i in idxs]
        else:
            # synchronous path for num_workers=0
            return [(self.dataset[i], None) for i in idxs]

    def _gather_batch(self, futures_or_results):
        """Block until the batch is ready, then stack into (X, y) Tensors"""
        if self.num_workers > 0:
            batch = [f.result() for f in futures_or_results]
        else:
            batch = [r for (r, _) in futures_or_results]

        Xs, ys = zip(*batch)
        X = Tensor(xp.stack([x.data for x in Xs], axis=0), dtype=Xs[0].dtype)
        y = Tensor(xp.stack([y.data for y in ys], axis=0), dtype=ys[0].dtype)
        return X, y

    def __getitem__(self, idx):
        """Get specific batch by index"""
        if idx < 0 or idx >= len(self):
            raise IndexError(f"Batch index {idx} out of range [0, {len(self)})")
        
        # Get all batch indices for consistent ordering
        batches = list(self._batch_indices())
        batch_idxs = batches[idx]
        
        # Load the batch synchronously
        batch_data = [self.dataset[i] for i in batch_idxs]
        Xs, ys = zip(*batch_data)
        
        # Stack into tensors
        X = Tensor(xp.stack([x.data for x in Xs], axis=0), dtype=Xs[0].dtype)
        y = Tensor(xp.stack([y.data for y in ys], axis=0), dtype=ys[0].dtype)
        return X, y

    def reset(self):
        """Reset the iterator - useful for multi-epoch training"""
        if self._pipeline is not None:
            self._pipeline.reset()

    def close(self):
        """Clean up resources"""
        if self._executor is not None:
            self._executor.shutdown(wait=True)
            self._executor = None

    def __repr__(self):
        backend = "DALI" if self.use_dali else "OpenCV+Threading"
        return (f"<DataLoader: {len(self)} batches, "
                f"batch_size={self.batch_size}, shuffle={self.shuffle}, "
                f"backend={backend}, device='{self.device}', "
                f"num_workers={self.num_workers}, prefetch_batches={self.prefetch_batches}>")


# DALI transform creation helper (only available when DALI is installed)
def create_dali_transforms(
    device: str = "cpu",
    brightness: float = 0.0,
    contrast: float = 0.0,
    saturation: float = 0.0,
    hue: float = 0.0,
    horizontal_flip_prob: float = 0.0,
    vertical_flip_prob: float = 0.0,
    rotation_angle: float = 0.0
):
    """
    Create common DALI augmentation transforms.
    Returns None if DALI is not available.
    """
    if not DALI_AVAILABLE:
        print("WARNING: DALI not available. Transform creation skipped.")
        return None
        
    def apply_transforms(images):
        # Color jitter
        if brightness != 0.0 or contrast != 0.0 or saturation != 0.0 or hue != 0.0:
            images = fn.color_twist(
                images,
                device=device,
                brightness=fn.random.uniform(range=[-brightness, brightness]) if brightness > 0 else None,
                contrast=fn.random.uniform(range=[1-contrast, 1+contrast]) if contrast > 0 else None,
                saturation=fn.random.uniform(range=[1-saturation, 1+saturation]) if saturation > 0 else None,
                hue=fn.random.uniform(range=[-hue, hue]) if hue > 0 else None,
            )
        
        # Flips
        if horizontal_flip_prob > 0.0:
            images = fn.flip(images, device=device, horizontal=fn.random.coin_flip(probability=horizontal_flip_prob))
        if vertical_flip_prob > 0.0:
            images = fn.flip(images, device=device, vertical=fn.random.coin_flip(probability=vertical_flip_prob))
        
        # Rotation
        if rotation_angle != 0.0:
            images = fn.rotate(
                images,
                device=device,
                angle=fn.random.uniform(range=[-rotation_angle, rotation_angle]),
                keep_size=True,
                fill_value=0
            )
        
        return images
    
    return apply_transforms