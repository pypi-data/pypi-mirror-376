import math
import random
import os
import numpy as np
from neurograd import xp, Tensor, float32, int64
from typing import Optional, List, Tuple, Union, Callable
import glob
from collections import deque



# Try to import DALI first - this determines our capabilities
try:
    import nvidia.dali as dali
    from nvidia.dali import pipeline_def, Pipeline
    import nvidia.dali.fn as fn
    import nvidia.dali.types as types
    from nvidia.dali.plugin.base_iterator import LastBatchPolicy
    DALI_AVAILABLE = True
except ImportError:
    DALI_AVAILABLE = False
    print("INFO: NVIDIA DALI not available. Falling back to OpenCV-based implementation.")
    print("      For maximum performance, install with: pip install --extra-index-url https://developer.download.nvidia.com/compute/redist nvidia-dali-cuda120")

# Always import OpenCV as fallback
try:
    import cv2
    # cv2.setNumThreads(1)  # Uncomment if needed for threading control
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("WARNING: OpenCV not available. Image loading will be limited.")

from concurrent.futures import ThreadPoolExecutor

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
    Enhanced ImageFolder that uses DALI when available, OpenCV as fallback.
    
    Automatically detects DALI availability and optimizes accordingly.
    """
    def __init__(
        self,
        root: str,
        img_shape: tuple = None,          # (H, W)
        img_mode: str = "RGB",            # "RGB", "L", etc.
        img_normalize: bool = True,       # /255 -> float
        img_transform: callable = None,   # DALI pipeline or callable
        target_transform: callable = None,
        img_dtype=xp.float32,
        target_dtype=xp.int64,
        chw: bool = True,                 # return CxHxW if True, else HxWxC
        device: str = "cpu",              # "cpu" or "gpu"/"cuda" (DALI only)
        num_threads: int = 4,             # DALI CPU threads
        prefetch_queue_depth: int = 2,    # DALI prefetch depth
        seed: int = 42
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
        self.device = "gpu" if device in ["gpu", "cuda"] else "cpu"
        self.num_threads = num_threads
        self.prefetch_queue_depth = prefetch_queue_depth
        self.seed = seed

        # Determine which backend to use
        # Use DALI whenever it is available. Do not gate DALI usage on the
        # type of img_transform — we will apply transforms inside the DALI
        # pipeline when possible (callable transforms will be invoked inside
        # the pipeline; Pipeline instances are returned directly).
        self.use_dali = DALI_AVAILABLE
        if device in ["gpu", "cuda"] and not DALI_AVAILABLE:
            print("WARNING: GPU device requested but DALI not available. Using CPU with OpenCV fallback.")
            self.device = "cpu"

        self.images: List[str] = []
        self.targets: List[str] = []
        self._collect_paths()

        # Stable class mapping
        self.target_names = sorted(set(self.targets))
        self.target_mapping = {name: i for i, name in enumerate(self.target_names)}
        self.num_classes = len(self.target_names)
        
        # Convert targets to numeric labels
        self.numeric_targets = [self.target_mapping[t] for t in self.targets]

        print(f"ImageFolder initialized: {len(self)} samples, {self.num_classes} classes")
        print(f"Backend: {'DALI' if self.use_dali else 'OpenCV'}, Device: {self.device}")

    def _collect_paths(self):
        """Collect image paths and their class labels"""
        if os.path.exists(self.root) and os.path.isdir(self.root):
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
                        if f.lower().endswith(IMG_EXTS):
                            p = os.path.join(r, f)
                            cls = os.path.basename(os.path.dirname(p))
                            self.images.append(p)
                            self.targets.append(cls)


    def get_dali_pipeline(self, batch_size: int, shuffle: bool = True):
        """Create DALI pipeline for this dataset (only when DALI is available)"""
        if not self.use_dali:
            return None
            
        # If user provided an entire DALI Pipeline instance, return it directly.
        if isinstance(self.img_transform, Pipeline):
            return self.img_transform

        @pipeline_def(batch_size=batch_size, num_threads=self.num_threads, device_id=0, seed=self.seed)
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

            # Decode and apply RandomResizedCrop - this is a standard and robust approach
            h, w = self.img_shape if self.img_shape is not None else (224, 224)
            images = fn.decoders.image_random_crop(
                images,
                device="mixed",
                output_type=types.RGB,
                random_aspect_ratio=[0.8, 1.25],
                random_area=[0.1, 1.0],
                num_attempts=100
            )
            
            # Now, resize the cropped image to the final desired shape
            images = fn.resize(
                images,
                device=self.device,
                size=[h, w],
                interp_type=types.INTERP_LINEAR
            )

            # Handle grayscale conversion if needed
            if self.img_mode.upper() in ("L", "GRAY", "GREY", "GRAYSCALE"):
                images = fn.color_space_conversion(
                    images, device=self.device, image_type=types.RGB, output_type=types.GRAY
                )

            # Apply remaining augmentations directly here
            if self.img_transform and callable(self.img_transform):
                try:
                    # The callable is expected to contain other DALI ops like color_twist, rotate, etc.
                    images = self.img_transform(images)
                except Exception as e:
                    print(f"WARNING: Failed to apply DALI callable transform. Error: {e}. Skipping transform.")

            # Normalize to [0, 1] if requested
            if self.img_normalize:
                images = fn.cast(images, dtype=types.FLOAT)
                images = images / 255.0
            else:
                # Still cast to float for consistency, even if not normalized
                images = fn.cast(images, dtype=types.FLOAT)

            # Transpose to CHW format if requested
            if self.chw:
                images = fn.transpose(images, device=self.device, perm=[2, 0, 1])
            
            return images, labels.gpu() if self.device == "gpu" else labels

        return image_pipeline()

    def _apply_img_transform(self, arr: np.ndarray) -> np.ndarray:
        """Apply image transforms (OpenCV fallback path)"""
        if self.img_transform is None:
            return arr
        # If a DALI Pipeline was provided but we are in the numpy/OpenCV path,
        # warn the user because we cannot apply a full DALI Pipeline to a single
        # numpy array. Users should provide a callable transform for fallback.
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
        except Exception:
            # If transform fails for unexpected reasons, warn and return original
            print("WARNING: img_transform callable raised an exception on ndarray input. Returning original image.")
            return arr

    def _load_image_opencv(self, path: str) -> np.ndarray:
        """Load image using OpenCV (fallback implementation)"""
        if not CV2_AVAILABLE:
            raise RuntimeError("OpenCV not available for image loading")
            
        # OpenCV-only fast decode/resize
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
        
        # Apply transforms
        if self.img_transform:
            arr = self._apply_img_transform(arr)
        
        # Convert to CHW if requested
        if self.chw and arr.ndim == 3:
            arr = np.transpose(arr, (2, 0, 1))  # C,H,W
        
        # Normalize
        if self.img_normalize:
            arr = arr.astype(np.float32) / 255.0
        else:
            arr = arr.astype(np.float32)
        
        return arr

    def __getitem__(self, idx: int):
        """Get single item - uses appropriate backend"""
        img_path = self.images[idx]
        target = self.numeric_targets[idx]
        
        # Load image using appropriate backend
        if self.use_dali:
            # For DALI datasets, single item access uses OpenCV fallback
            # DALI is optimized for batch processing
            image = self._load_image_opencv(img_path)
        else:
            # Standard OpenCV loading
            image = self._load_image_opencv(img_path)
        
        # Apply target transform
        if self.target_transform:
            target = self.target_transform(target)
        
        return Tensor(image, dtype=self.img_dtype), Tensor(target, dtype=self.target_dtype)

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
        backend = "DALI" if self.use_dali else "OpenCV"
        device = self.device
        return (f"ImageFolder(root='{self.root}', samples={len(self)}, "
                f"classes={self.num_classes}, backend={backend}, device='{device}')")

    def __repr__(self):
        backend = "DALI" if self.use_dali else "OpenCV"
        shape = None
        if len(self) > 0:
            try:
                image, _ = self[0]
                shape = tuple(image.shape)
            except Exception:
                shape = None
        
        return (f"ImageFolder(root='{self.root}', samples={len(self)}, "
                f"classes={self.num_classes}, backend={backend}, device='{self.device}', "
                f"shape={shape}, img_dtype={self.img_dtype}, target_dtype={self.target_dtype}, "
                f"mode='{self.img_mode}', normalize={self.img_normalize}, chw={self.chw})")


class DataLoader:
    """
    Enhanced DataLoader with DALI acceleration when available, OpenCV fallback otherwise.
    
    Automatically detects capabilities and optimizes accordingly.
    """
    def __init__(
        self,
        dataset: Union[ImageFolder, Dataset],
        batch_size: int = 32,
        shuffle: bool = True,
        num_threads: int = 4,
        device: str = "cpu",
        prefetch_queue_depth: int = 2,
        drop_last: bool = False,
        seed: Optional[int] = None,
        num_workers: Optional[int] = None,  # For fallback threading
        prefetch_batches: int = 2           # For fallback prefetch
    ):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.num_threads = num_threads
        self.device = "gpu" if device in ["gpu", "cuda"] else "cpu"
        self.prefetch_queue_depth = prefetch_queue_depth
        self.drop_last = drop_last
        self.seed = seed or 42
        self.prefetch_batches = max(0, int(prefetch_batches))
        
        # Determine threading for fallback mode
        if num_workers is None:
            cores = os.cpu_count() or 2
            self.num_workers = max(1, min(8, cores - 1))
        else:
            self.num_workers = int(num_workers)
        
        self._pipeline = None
        self._dali_iter = None
        self._executor: Optional[ThreadPoolExecutor] = None
        
        # Initialize DALI pipeline if available and applicable
        self.use_dali = (
            DALI_AVAILABLE and 
            isinstance(dataset, ImageFolder) and 
            dataset.use_dali
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
        
        # Update dataset's DALI settings
        self.dataset.device = self.device
        self.dataset.num_threads = self.num_threads
        self.dataset.prefetch_queue_depth = self.prefetch_queue_depth
        self.dataset.seed = self.seed
        
        # Create pipeline
        self._pipeline = self.dataset.get_dali_pipeline(
            batch_size=self.batch_size,
            shuffle=self.shuffle
        )
        
        if self._pipeline is not None:
            # Build the pipeline
            self._pipeline.build()
            print(f"DALI pipeline initialized: batch_size={self.batch_size}, device={self.device}")

    def __len__(self):
        n = len(self.dataset)
        if self.drop_last:
            return n // self.batch_size
        return (n + self.batch_size - 1) // self.batch_size

    def __iter__(self):
        """Main iteration - uses DALI when available, falls back otherwise"""
        if self.use_dali and self._pipeline is not None:
            return self._dali_iterator()
        else:
            return self._regular_iterator()

    def _dali_iterator(self):
        """DALI-based iteration - maximum performance!"""
        # Reset pipeline for new epoch
        self._pipeline.reset()
        
        # Create DALI iterator
        last_batch_policy = LastBatchPolicy.DROP if self.drop_last else LastBatchPolicy.FILL
        
        class DALIGenericIterator:
            # Pass the dataset in to get dtype info
            def __init__(self, pipeline, output_map, size, last_batch_policy, dataset):
                self.pipeline = pipeline
                self.output_map = output_map
                self.size = size
                self.last_batch_policy = last_batch_policy
                self.dataset = dataset  # Store the dataset
                self._counter = 0
            
            def __iter__(self):
                return self
            
            def __next__(self):
                if self._counter >= self.size:
                    raise StopIteration
                
                try:
                    # 1. Get the raw DALI output tensors
                    outputs = self.pipeline.run()
                    self._counter += 1
                    
                    images_dali = outputs[0]
                    labels_dali = outputs[1]
                    
                    # 2. Now, decide how to convert based on the device
                    if self.pipeline.device_id is not None:
                        # GPU PATH: Use zero-copy DLPack
                        images_arr = xp.from_dlpack(images_dali.as_tensor())
                        labels_arr = xp.from_dlpack(labels_dali.as_tensor())
                    else:
                        # CPU PATH: Convert to NumPy array
                        images_arr = images_dali.as_array()
                        labels_arr = labels_dali.as_array()

                    # 3. Create your framework's Tensors from arrays already on the correct device
                    X = Tensor(images_arr, dtype=self.dataset.img_dtype)
                    y = Tensor(labels_arr, dtype=self.dataset.target_dtype)
                    
                    return X, y
                    
                except StopIteration:
                    raise StopIteration
        
        # Create the iterator, passing the dataset instance
        iterator = DALIGenericIterator(
            pipeline=self._pipeline,
            output_map=["images", "labels"],
            size=len(self),
            last_batch_policy=last_batch_policy,
            dataset=self.dataset  # Pass the dataset here
        )
        
        for batch in iterator:
            yield batch

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
            return [(self.dataset[i], None) for i in idxs]  # (result, None) to unify interface

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
        device_str = f", device='{self.device}'" if self.use_dali else ""
        return (f"<DataLoader: {len(self)} batches, "
                f"batch_size={self.batch_size}, shuffle={self.shuffle}, "
                f"backend={backend}{device_str}, "
                f"prefetch_depth={self.prefetch_queue_depth if self.use_dali else self.prefetch_batches}>")


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
                fill_value=0
            )
        
        return images
    
    return apply_transforms


# Example usage demonstrating graceful fallback:
"""
# Basic usage - works with or without DALI
dataset = ImageFolder(
    root="/path/to/imagenet",
    img_shape=(224, 224),
    img_mode="RGB", 
    img_normalize=True,
    device="cuda" if DALI_AVAILABLE else "cpu",  # Automatically adapts
    num_threads=8,
    prefetch_queue_depth=3
)

dataloader = DataLoader(
    dataset,
    batch_size=128,
    shuffle=True,
    device="cuda" if DALI_AVAILABLE else "cpu",  # Automatically adapts
    prefetch_queue_depth=3,
    num_threads=8
)

print(f"Using backend: {'DALI' if dataloader.use_dali else 'OpenCV+Threading'}")

# Training loop - works at maximum speed regardless of backend
for epoch in range(num_epochs):
    for batch_idx, (images, targets) in enumerate(dataloader):
        # Your training code here
        # Performance automatically optimized based on available libraries
        pass
    dataloader.reset()  # Reset for next epoch
    
# Clean up when done
dataloader.close()
"""