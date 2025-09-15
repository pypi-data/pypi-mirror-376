from neurograd import Tensor, float32
import numpy as np
from neurograd import xp
from typing import Optional, Union, Any, Dict, List, Callable
import random
import os
from pathlib import Path
import time

try:
    import datasets
    from datasets import Dataset as HFDataset, DatasetDict, IterableDataset, load_dataset, load_from_disk, Features, Array2D, Array3D, Image as HFImage, ClassLabel
    from datasets.utils.logging import disable_progress_bar
    import multiprocessing as mp
    HF_AVAILABLE = True
    # Disable progress bars for cleaner output
    disable_progress_bar()
except ImportError:
    HF_AVAILABLE = False
    HFDataset = None
    DatasetDict = None
    IterableDataset = None
    mp = None

# Image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Memory profiling
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class Dataset:
    """NeuroGrad Dataset wrapper using HuggingFace datasets backend with multiprocessing"""
    
    def __init__(self, X, y, dtype=float32, cache_dir: Optional[str] = None, 
                 lazy_loading: bool = False, streaming: bool = False):
        assert len(X) == len(y), "Mismatched input and label lengths"
        
        self.dtype = dtype
        self._length = len(X)
        self.lazy_loading = lazy_loading
        self.streaming = streaming
        
        if HF_AVAILABLE:
            if streaming and len(X) > 10000:  # Use streaming for very large datasets
                self._create_streaming_dataset(X, y, cache_dir)
            else:
                self._create_standard_dataset(X, y, cache_dir)
        else:
            # Fallback to simple storage
            self._X = X
            self._y = y

    def _create_streaming_dataset(self, X, y, cache_dir):
        """Create streaming dataset for very large data"""
        def data_generator():
            for x, label in zip(X, y):
                yield {'features': x, 'labels': label}
        
        self._hf_dataset = IterableDataset.from_generator(
            data_generator,
            cache_dir=cache_dir
        )
        
    def _create_standard_dataset(self, X, y, cache_dir):
        """Create standard HF dataset with optional preprocessing"""
        # Convert to HF dataset for efficient storage and operations
        self._hf_dataset = HFDataset.from_dict({
            'features': X,
            'labels': y
        }, cache_dir=cache_dir)
        
        # Enable memory mapping and preprocessing for larger datasets
        if len(X) > 1000 and not self.lazy_loading:
            self._hf_dataset = self._hf_dataset.map(
                self._preprocess_batch,
                batched=True,
                batch_size=min(1000, len(X) // (mp.cpu_count() if mp else 1) + 1),
                num_proc=min(4, mp.cpu_count()) if mp else 1,
                cache_file_name=f"{cache_dir or 'cache'}/dataset_processed.arrow" if cache_dir else None,
                desc="Preprocessing data"
            )

    def _preprocess_batch(self, examples):
        """Batch preprocessing for better efficiency"""
        # Convert to numpy arrays if needed
        features = [np.array(f) if not isinstance(f, np.ndarray) else f for f in examples['features']]
        labels = [np.array(l) if not isinstance(l, np.ndarray) else l for l in examples['labels']]
        
        return {
            'features': features,
            'labels': labels
        }

    def __len__(self):
        return self._length

    def __getitem__(self, idx):
        if HF_AVAILABLE:
            if self.streaming:
                # For streaming datasets, we need to handle differently
                raise NotImplementedError("Direct indexing not supported for streaming datasets. Use DataLoader instead.")
            
            item = self._hf_dataset[idx]
            x_data = item['features']
            y_data = item['labels']
        else:
            x_data = self._X[idx]
            y_data = self._y[idx]
        
        return Tensor(x_data, dtype=self.dtype), Tensor(y_data, dtype=self.dtype)

    def __iter__(self):
        if HF_AVAILABLE and self.streaming:
            # For streaming datasets
            for item in self._hf_dataset:
                yield Tensor(item['features'], dtype=self.dtype), Tensor(item['labels'], dtype=self.dtype)
        else:
            for idx in range(len(self)):
                yield self[idx]

    def shuffle(self, seed: Optional[int] = None):
        if HF_AVAILABLE and not self.streaming:
            self._hf_dataset = self._hf_dataset.shuffle(seed=seed)
        elif not self.streaming:
            # Fallback manual shuffle
            indices = list(range(len(self)))
            rng = random.Random(seed) if seed is not None else random.Random()
            rng.shuffle(indices)
            self._X = [self._X[i] for i in indices]
            self._y = [self._y[i] for i in indices]

    def map(self, function: Callable, num_proc: Optional[int] = None, 
            batched: bool = True, batch_size: int = 1000, **kwargs):
        """Apply function to all examples using optimized batched processing"""
        if HF_AVAILABLE:
            if num_proc is None:
                num_proc = min(4, mp.cpu_count()) if mp else 1
            
            self._hf_dataset = self._hf_dataset.map(
                function, 
                num_proc=num_proc,
                batched=batched,
                batch_size=batch_size,
                **kwargs
            )
        else:
            # Simple fallback without multiprocessing
            if batched:
                # Process in batches even in fallback mode
                for i in range(0, len(self), batch_size):
                    batch_end = min(i + batch_size, len(self))
                    batch_data = {
                        'features': [self._X[j] for j in range(i, batch_end)],
                        'labels': [self._y[j] for j in range(i, batch_end)]
                    }
                    result = function(batch_data)
                    
                    # Update data
                    for j, (feat, label) in enumerate(zip(result['features'], result['labels'])):
                        self._X[i + j] = feat
                        self._y[i + j] = label
            else:
                for i in range(len(self)):
                    result = function({'features': self._X[i], 'labels': self._y[i]})
                    self._X[i] = result.get('features', self._X[i])
                    self._y[i] = result.get('labels', self._y[i])
        return self

    def filter(self, function: Callable, num_proc: Optional[int] = None, 
               batched: bool = True, batch_size: int = 1000):
        """Filter dataset using optimized batched processing"""
        if HF_AVAILABLE:
            if num_proc is None:
                num_proc = min(4, mp.cpu_count()) if mp else 1
            
            self._hf_dataset = self._hf_dataset.filter(
                function, 
                num_proc=num_proc,
                batched=batched,
                batch_size=batch_size
            )
            self._length = len(self._hf_dataset)
        return self

    def save_to_disk(self, path: str):
        """Save dataset to disk for fast loading"""
        if HF_AVAILABLE:
            self._hf_dataset.save_to_disk(path)
        else:
            # Fallback: save as numpy arrays
            import pickle
            os.makedirs(path, exist_ok=True)
            with open(os.path.join(path, 'data.pkl'), 'wb') as f:
                pickle.dump({'X': self._X, 'y': self._y, 'dtype': self.dtype}, f)

    @classmethod
    def load_from_disk(cls, path: str):
        """Load dataset from disk"""
        if HF_AVAILABLE:
            hf_dataset = load_from_disk(path)
            # Create instance and set the loaded dataset
            instance = cls.__new__(cls)
            instance._hf_dataset = hf_dataset
            instance.dtype = float32  # Default, could be stored in metadata
            instance._length = len(hf_dataset)
            instance.lazy_loading = False
            instance.streaming = False
            return instance
        else:
            # Fallback: load from pickle
            import pickle
            with open(os.path.join(path, 'data.pkl'), 'rb') as f:
                data = pickle.load(f)
            return cls(data['X'], data['y'], dtype=data['dtype'])

    def __repr__(self):
        return f"<Dataset: {len(self)} samples, dtype={self.dtype}, streaming={self.streaming}>"


class DataLoader:
    """Highly optimized DataLoader using HuggingFace datasets backend"""
    
    def __init__(self, dataset: Dataset, batch_size: int = 32,
                 shuffle: bool = True, seed: Optional[int] = None,
                 num_workers: Optional[int] = None,
                 prefetch_batches: int = 2,
                 drop_last: bool = False,
                 pin_memory: bool = False):
        self.dataset = dataset
        self.batch_size = int(batch_size)
        self.shuffle = shuffle
        self.seed = seed
        self.prefetch_batches = max(0, int(prefetch_batches))
        self.drop_last = bool(drop_last)
        self.pin_memory = pin_memory
        
        # Optimize num_workers based on dataset size and system
        if num_workers is None:
            if HF_AVAILABLE and mp:
                # Scale workers based on dataset size
                if len(dataset) > 10000:
                    self.num_workers = min(8, mp.cpu_count())
                elif len(dataset) > 1000:
                    self.num_workers = min(4, mp.cpu_count())
                else:
                    self.num_workers = min(2, mp.cpu_count())
            else:
                self.num_workers = 1
        else:
            self.num_workers = int(num_workers)

    def __len__(self):
        if self.dataset.streaming:
            # For streaming datasets, we can't know the exact length
            return float('inf')
        
        n = len(self.dataset)
        if self.drop_last:
            return n // self.batch_size
        return (n + self.batch_size - 1) // self.batch_size

    def __iter__(self):
        """Highly optimized iteration using HF datasets built-in features"""
        if HF_AVAILABLE and hasattr(self.dataset, '_hf_dataset'):
            # Use prefetching automatically for lazy loading datasets to improve performance
            if getattr(self.dataset, 'lazy_loading', False) and self.prefetch_batches > 0:
                return self.prefetch(self.prefetch_batches)
            else:
                return self._iter_hf_optimized()
        else:
            return self._iter_fallback()

    def _iter_hf_optimized(self):
        """Use HF datasets optimized iteration"""
        hf_dataset = self.dataset._hf_dataset
        
        # Apply shuffling
        if self.shuffle and not self.dataset.streaming:
            hf_dataset = hf_dataset.shuffle(seed=self.seed)
        
        # Use HF's optimized batch iteration
        if hasattr(hf_dataset, 'iter'):
            # For IterableDataset (streaming)
            dataloader = hf_dataset.iter(batch_size=self.batch_size)
        else:
            # For regular Dataset - use to_iterable_dataset for better batching
            if len(hf_dataset) > 10000:  # Use iterable for large datasets
                iterable_dataset = hf_dataset.to_iterable_dataset(num_shards=self.num_workers)
                dataloader = iterable_dataset.iter(batch_size=self.batch_size)
            else:
                # Manual batching for smaller datasets
                dataloader = self._manual_batch_iter(hf_dataset)
        
        # Convert batches to tensors
        for batch in dataloader:
            try:
                X, y = self._convert_batch_to_tensors(batch)
                if X is not None and y is not None:
                    yield X, y
            except Exception as e:
                # Skip corrupted batches
                print(f"Warning: Skipping corrupted batch: {e}")
                continue

    def _manual_batch_iter(self, hf_dataset):
        """Manual batching for regular HF datasets"""
        n = len(hf_dataset)
        indices = list(range(n))
        
        if self.drop_last:
            limit = (n // self.batch_size) * self.batch_size
            indices = indices[:limit]
        
        for i in range(0, len(indices), self.batch_size):
            batch_indices = indices[i:i + self.batch_size]
            # Use select for efficient batch loading
            batch_dataset = hf_dataset.select(batch_indices)
            
            # Convert to batch format
            batch = {}
            for key in batch_dataset.column_names:
                batch[key] = batch_dataset[key]
            
            yield batch

    def _convert_batch_to_tensors(self, batch):
        """Convert HF batch to NeuroGrad tensors efficiently"""
        try:
            # Handle different batch formats
            if 'processed_image' in batch:
                # ImageFolder with preprocessed images
                X = Tensor(np.stack(batch['processed_image']), dtype=self.dataset.img_dtype)
                y = Tensor(np.array(batch['label']), dtype=self.dataset.target_dtype)
            elif 'features' in batch and 'labels' in batch:
                # Standard Dataset format
                features = batch['features']
                labels = batch['labels']
                
                # Handle different data types efficiently
                if isinstance(features[0], (list, np.ndarray)):
                    X = Tensor(np.stack([np.array(f) for f in features]), dtype=self.dataset.dtype)
                else:
                    X = Tensor(np.array(features), dtype=self.dataset.dtype)
                
                if isinstance(labels[0], (list, np.ndarray)):
                    y = Tensor(np.stack([np.array(l) for l in labels]), dtype=self.dataset.dtype)
                else:
                    y = Tensor(np.array(labels), dtype=self.dataset.dtype)
            else:
                # Generic handling - find feature and label columns
                keys = list(batch.keys())
                if len(keys) >= 2:
                    # Assume first key is features, last is labels
                    feature_key = keys[0]
                    label_key = keys[-1] if 'label' in keys[-1] else keys[1]
                    
                    X = Tensor(np.stack([np.array(f) for f in batch[feature_key]]), 
                              dtype=getattr(self.dataset, 'dtype', float32))
                    y = Tensor(np.array(batch[label_key]), 
                              dtype=getattr(self.dataset, 'dtype', float32))
                else:
                    return None, None
            
            return X, y
            
        except Exception as e:
            print(f"Error converting batch to tensors: {e}")
            return None, None

    def _iter_fallback(self):
        """Fallback iteration for non-HF datasets"""
        n = len(self.dataset)
        indices = list(range(n))
        
        if self.shuffle:
            rng = random.Random(self.seed)
            rng.shuffle(indices)
        
        if self.drop_last:
            limit = (n // self.batch_size) * self.batch_size
            indices = indices[:limit]
        
        for i in range(0, len(indices), self.batch_size):
            batch_indices = indices[i:i + self.batch_size]
            batch_data = [self.dataset[idx] for idx in batch_indices]
            Xs, ys = zip(*batch_data)
            
            X = Tensor(xp.stack([x.data for x in Xs], axis=0), dtype=Xs[0].dtype)
            y = Tensor(xp.stack([y.data for y in ys], axis=0), dtype=ys[0].dtype)
            yield X, y

    def prefetch(self, num_batches: int = None):
        """Return a prefetching iterator for better performance"""
        if num_batches is None:
            num_batches = self.prefetch_batches
        
        if num_batches <= 0:
            return iter(self)
        
        # Simple prefetching implementation
        import threading
        from queue import Queue
        
        def producer(queue, iterator):
            try:
                for batch in iterator:
                    queue.put(batch)
                queue.put(None)  # Sentinel
            except Exception as e:
                queue.put(e)
        
        queue = Queue(maxsize=num_batches)
        iterator = iter(self)
        thread = threading.Thread(target=producer, args=(queue, iterator))
        thread.daemon = True
        thread.start()
        
        while True:
            batch = queue.get()
            if batch is None:  # Sentinel
                break
            if isinstance(batch, Exception):
                raise batch
            yield batch

    def __repr__(self):
        return (f"<DataLoader: {len(self) if not self.dataset.streaming else '∞'} batches, "
                f"batch_size={self.batch_size}, shuffle={self.shuffle}, "
                f"num_workers={self.num_workers}, streaming={self.dataset.streaming}>")


class ImageFolder(Dataset):
    """Highly optimized ImageFolder using HuggingFace datasets with advanced features"""
    
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
        chw: bool = True,
        cache_dir: Optional[str] = None,
        num_proc: Optional[int] = None,
        lazy_loading: bool = True,
        streaming: bool = False,
        prefetch_images: bool = True,
        memory_map: bool = True
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
        self.lazy_loading = lazy_loading
        self.streaming = streaming
        self.prefetch_images = prefetch_images
        self.memory_map = memory_map
        
        # Optimize num_proc based on dataset size
        if num_proc is None:
            self.num_proc = min(8, mp.cpu_count()) if HF_AVAILABLE and mp else 1
        else:
            self.num_proc = num_proc
        
        if HF_AVAILABLE:
            if streaming:
                self._create_streaming_imagefolder(cache_dir)
            else:
                self._create_standard_imagefolder(cache_dir)
        else:
            self._create_fallback_imagefolder()

    def _create_streaming_imagefolder(self, cache_dir):
        """Create streaming dataset for very large image collections"""
        def image_generator():
            for img_path in self._iter_image_paths():
                class_name = Path(img_path).parent.name
                yield {
                    'image': img_path,
                    'label': class_name
                }
        
        # Get class names first
        self.target_names = sorted(set(
            Path(img_path).parent.name 
            for img_path in self._iter_image_paths()
        ))
        self.target_mapping = {name: i for i, name in enumerate(self.target_names)}
        self.num_classes = len(self.target_names)
        
        features = Features({
            'image': HFImage(),
            'label': ClassLabel(names=self.target_names)
        })
        
        self._hf_dataset = IterableDataset.from_generator(
            image_generator,
            features=features
        )
        
        # Apply transformations
        self._hf_dataset = self._hf_dataset.map(
            self._process_image_streaming,
            batched=True,
            batch_size=100
        )

    def _create_standard_imagefolder(self, cache_dir):
        """Create standard dataset with optimized preprocessing"""
        # Collect all image paths and labels
        self.images = []
        self.targets = []
        self._collect_paths()
        
        if len(self.images) == 0:
            raise ValueError(f"No images found in {self.root}")
        
        # Create class mapping
        self.target_names = sorted(set(self.targets))
        self.target_mapping = {name: i for i, name in enumerate(self.target_names)}
        self.num_classes = len(self.target_names)
        
        numeric_targets = [self.target_mapping[t] for t in self.targets]
        
        # Create HF dataset with proper features
        features = Features({
            'image': HFImage(),
            'label': ClassLabel(names=self.target_names)
        })
        
        self._hf_dataset = HFDataset.from_dict({
            'image': self.images,
            'label': numeric_targets
        }, features=features)
        
        # Preprocessing strategy based on dataset size and memory
        if not self.lazy_loading and len(self.images) > 0:
            self._preprocess_images(cache_dir)

    def _preprocess_images(self, cache_dir):
        """Preprocess images with optimized batching"""
        cache_file = f"{cache_dir or 'cache'}/images_processed.arrow" if cache_dir else None
        
        # Determine optimal batch size based on image size and available memory
        if self.img_shape:
            pixels = self.img_shape[0] * self.img_shape[1]
            channels = 3 if self.img_mode == 'RGB' else 1
            bytes_per_image = pixels * channels * 4  # 4 bytes for float32
            
            # Target 1GB of memory per batch
            target_memory = 1024 * 1024 * 1024  # 1GB
            batch_size = min(1000, max(10, target_memory // bytes_per_image))
        else:
            batch_size = 100
        
        print(f"Preprocessing {len(self.images)} images with batch_size={batch_size}, num_proc={self.num_proc}")
        
        self._hf_dataset = self._hf_dataset.map(
            self._process_image_batch,
            batched=True,
            batch_size=batch_size,
            num_proc=self.num_proc,
            cache_file_name=cache_file,
            desc="Processing images",
            remove_columns=['image'] if not self.memory_map else [],  # Keep original if memory mapping
            fn_kwargs={
                'img_shape': self.img_shape,
                'img_mode': self.img_mode,
                'img_normalize': self.img_normalize,
                'chw': self.chw,
                'img_transform': self.img_transform
            }
        )

    def _process_image_batch(self, examples, img_shape=None, img_mode=None, 
                           img_normalize=True, chw=True, img_transform=None):
        """Optimized batch image processing"""
        processed_images = []
        
        for img in examples['image']:
            try:
                # Handle both PIL images and file paths
                if isinstance(img, str):
                    if PIL_AVAILABLE:
                        img = Image.open(img)
                    else:
                        raise ImportError("PIL required for image loading")
                
                # Convert to target mode
                if img_mode and hasattr(img, 'convert'):
                    img = img.convert(img_mode)
                
                # Resize if needed - use high-quality resampling
                if img_shape:
                    img = img.resize((img_shape[1], img_shape[0]), Image.LANCZOS)
                
                # Convert to numpy
                arr = np.array(img)
                
                # Ensure proper dimensions
                if arr.ndim == 2:
                    arr = arr[:, :, None]
                
                # Apply custom transforms
                if img_transform:
                    arr = self._apply_img_transform(arr, img_transform)
                
                # Channel ordering (HWC -> CHW)
                if chw and arr.ndim == 3:
                    arr = np.transpose(arr, (2, 0, 1))
                
                # Normalize
                if img_normalize:
                    arr = arr.astype(np.float32) / 255.0
                
                processed_images.append(arr)
                
            except Exception as e:
                print(f"Error processing image: {e}")
                # Create a dummy image with correct shape
                if img_shape and chw:
                    dummy_shape = (3 if img_mode == 'RGB' else 1, img_shape[0], img_shape[1])
                elif img_shape:
                    dummy_shape = (img_shape[0], img_shape[1], 3 if img_mode == 'RGB' else 1)
                else:
                    dummy_shape = (224, 224, 3) if not chw else (3, 224, 224)
                
                dummy_img = np.zeros(dummy_shape, dtype=np.float32)
                processed_images.append(dummy_img)
        
        return {'processed_image': processed_images}

    def _process_image_streaming(self, examples):
        """Process images for streaming datasets"""
        return self._process_image_batch(
            examples,
            self.img_shape,
            self.img_mode,
            self.img_normalize,
            self.chw,
            self.img_transform
        )

    def _collect_paths(self):
        """Efficiently collect image paths"""
        IMG_EXTS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tif', '.tiff', 
                   '.webp', '.jfif', '.avif', '.heif', '.heic')
        
        root_path = Path(self.root)
        
        # Use os.walk for better performance on large directories
        for root, dirs, files in os.walk(root_path):
            root = Path(root)
            class_name = root.name if root != root_path else 'default'
            
            for file in files:
                if file.lower().endswith(IMG_EXTS):
                    self.images.append(str(root / file))
                    self.targets.append(class_name)

    def _iter_image_paths(self):
        """Generator for streaming image paths"""
        IMG_EXTS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tif', '.tiff',
                   '.webp', '.jfif', '.avif', '.heif', '.heic')
        
        root_path = Path(self.root)
        for img_path in root_path.rglob('*'):
            if img_path.suffix.lower() in IMG_EXTS:
                yield str(img_path)

    def _apply_img_transform(self, arr: np.ndarray, transform=None) -> np.ndarray:
        """Apply image transformations efficiently"""
        if transform is None:
            return arr
        
        # Try Albumentations-style call
        try:
            out = transform(image=arr)
            if isinstance(out, dict) and "image" in out:
                return out["image"]
        except (TypeError, AttributeError):
            pass
        
        # Try torchvision-style transforms
        try:
            return transform(arr)
        except Exception:
            return arr

    def _create_fallback_imagefolder(self):
        """Fallback implementation without HF datasets"""
        self.images = []
        self.targets = []
        self._collect_paths()
        
        self.target_names = sorted(set(self.targets))
        self.target_mapping = {name: i for i, name in enumerate(self.target_names)}
        self.num_classes = len(self.target_names)
        
        # Store as simple lists
        self._images = self.images
        self._targets = [self.target_mapping[t] for t in self.targets]

    def __len__(self):
        if self.streaming:
            return float('inf')
        return len(self.images) if hasattr(self, 'images') else 0

    def __getitem__(self, idx: int):
        if self.streaming:
            raise NotImplementedError("Direct indexing not supported for streaming datasets")
        
        if HF_AVAILABLE and hasattr(self, '_hf_dataset'):
            item = self._hf_dataset[idx]
            
            # Use pre-processed image if available
            if 'processed_image' in item:
                image = item['processed_image']
            else:
                # Process on-the-fly for lazy loading
                image = self._process_single_image(item['image'])
            
            target = item['label']
        else:
            # Fallback mode
            img_path = self._images[idx]
            target = self._targets[idx]
            image = self._load_image_fallback(img_path)
        
        # Apply target transform
        if self.target_transform:
            target = self.target_transform(target)
        
        return Tensor(image, dtype=self.img_dtype), Tensor(target, dtype=self.target_dtype)

    def _process_single_image(self, img):
        """Process single image for lazy loading"""
        batch_result = self._process_image_batch(
            {'image': [img]},
            self.img_shape,
            self.img_mode,
            self.img_normalize,
            self.chw,
            self.img_transform
        )
        return batch_result['processed_image'][0]

    def _load_image_fallback(self, path: str) -> np.ndarray:
        """Fallback image loading without HF datasets"""
        if not PIL_AVAILABLE:
            raise ImportError("PIL is required for image loading")
        
        img = Image.open(path)
        if self.img_mode:
            img = img.convert(self.img_mode)
        
        if self.img_shape:
            img = img.resize((self.img_shape[1], self.img_shape[0]), Image.LANCZOS)
        
        arr = np.array(img)
        if arr.ndim == 2:
            arr = arr[:, :, None]
        
        if self.img_transform:
            arr = self._apply_img_transform(arr, self.img_transform)
        
        if self.chw and arr.ndim == 3:
            arr = np.transpose(arr, (2, 0, 1))
        
        if self.img_normalize:
            arr = arr.astype(np.float32) / 255.0
        
        return arr

    def get_class_weights(self) -> np.ndarray:
        """Calculate class weights for imbalanced datasets"""
        if self.streaming:
            raise NotImplementedError("Class weights not available for streaming datasets")
        
        if HF_AVAILABLE and hasattr(self, '_hf_dataset'):
            labels = self._hf_dataset['label']
        else:
            labels = self._targets
        
        # Calculate class frequencies
        unique, counts = np.unique(labels, return_counts=True)
        total = len(labels)
        
        # Inverse frequency weighting
        weights = total / (len(unique) * counts)
        return weights

    def get_stats(self) -> Dict[str, Any]:
        """Get dataset statistics"""
        if self.streaming:
            return {"type": "streaming", "classes": self.num_classes}
        
        stats = {
            "total_samples": len(self),
            "num_classes": self.num_classes,
            "class_names": self.target_names
        }
        
        # Add class distribution
        if HF_AVAILABLE and hasattr(self, '_hf_dataset'):
            labels = self._hf_dataset['label']
        else:
            labels = self._targets
        
        unique, counts = np.unique(labels, return_counts=True)
        stats["class_distribution"] = dict(zip([self.target_names[i] for i in unique], counts.tolist()))
        
        # Add image shape info if available
        try:
            sample_img, _ = self[0]
            stats["image_shape"] = sample_img.shape
        except Exception:
            pass
        
        return stats

    def __repr__(self):
        if self.streaming:
            return (f"ImageFolder(root='{self.root}', streaming=True, "
                   f"classes={self.num_classes}, mode='{self.img_mode}')")
        
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


# Utility functions for loading common datasets
def load_hf_dataset(dataset_name: str, split: str = "train", 
                   streaming: bool = False, cache_dir: Optional[str] = None,
                   num_proc: Optional[int] = None, **kwargs) -> Dataset:
    """Load a dataset from HuggingFace Hub with advanced options"""
    if not HF_AVAILABLE:
        raise ImportError("datasets package required. Install with: pip install datasets")
    
    hf_dataset = load_dataset(dataset_name, split=split, streaming=streaming, 
                             cache_dir=cache_dir, **kwargs)
    
    if streaming:
        # For streaming datasets, create a wrapper
        def convert_generator():
            for item in hf_dataset:
                # Extract features and labels based on dataset structure
                if 'image' in item and 'label' in item:
                    img = item['image']
                    if hasattr(img, 'convert'):
                        img = np.array(img.convert('RGB'))
                    yield {'features': img, 'labels': item['label']}
                else:
                    # Generic handling
                    feature_keys = [k for k in item.keys() if k not in ['label', 'labels']]
                    label_key = 'label' if 'label' in item else 'labels'
                    if feature_keys and label_key in item:
                        yield {'features': item[feature_keys[0]], 'labels': item[label_key]}
        
        # Create streaming dataset
        streaming_dataset = IterableDataset.from_generator(convert_generator, cache_dir=cache_dir)
        
        # Create Dataset wrapper
        dataset = Dataset.__new__(Dataset)
        dataset._hf_dataset = streaming_dataset
        dataset.dtype = float32
        dataset._length = float('inf')
        dataset.lazy_loading = False
        dataset.streaming = True
        return dataset
    
    # For regular datasets
    if 'image' in hf_dataset.features and 'label' in hf_dataset.features:
        # Image classification dataset - process efficiently
        def process_batch(examples):
            images = []
            for img in examples['image']:
                if hasattr(img, 'convert'):
                    img = np.array(img.convert('RGB'))
                else:
                    img = np.array(img)
                images.append(img)
            return {'features': images, 'labels': examples['label']}
        
        # Process in batches
        if num_proc is None:
            num_proc = min(4, mp.cpu_count()) if mp else 1
        
        processed_dataset = hf_dataset.map(
            process_batch,
            batched=True,
            batch_size=1000,
            num_proc=num_proc,
            cache_file_name=f"{cache_dir or 'cache'}/processed_hf_dataset.arrow" if cache_dir else None,
            remove_columns=['image']
        )
        
        # Create Dataset wrapper
        dataset = Dataset.__new__(Dataset)
        dataset._hf_dataset = processed_dataset
        dataset.dtype = float32
        dataset._length = len(processed_dataset)
        dataset.lazy_loading = False
        dataset.streaming = False
        return dataset
    else:
        # Generic dataset
        feature_names = list(hf_dataset.features.keys())
        if len(feature_names) >= 2:
            # Rename columns to standard format
            feature_key = feature_names[0]
            label_key = next((k for k in feature_names if 'label' in k.lower()), feature_names[1])
            
            renamed_dataset = hf_dataset.rename_columns({
                feature_key: 'features',
                label_key: 'labels'
            })
            
            # Create Dataset wrapper
            dataset = Dataset.__new__(Dataset)
            dataset._hf_dataset = renamed_dataset
            dataset.dtype = float32
            dataset._length = len(renamed_dataset)
            dataset.lazy_loading = False
            dataset.streaming = False
            return dataset
        else:
            raise ValueError(f"Dataset {dataset_name} structure not supported")


def create_dataset_from_arrays(X: Union[List, np.ndarray], y: Union[List, np.ndarray], 
                              dtype=float32, cache_dir: Optional[str] = None,
                              streaming: bool = False, num_proc: Optional[int] = None) -> Dataset:
    """Create optimized Dataset from numpy arrays or lists"""
    return Dataset(X, y, dtype=dtype, cache_dir=cache_dir, streaming=streaming)


def load_imagefolder_hf(root: str, 
                       img_shape: tuple = None,
                       img_mode: str = "RGB",
                       cache_dir: Optional[str] = None,
                       num_proc: Optional[int] = None,
                       streaming: bool = False,
                       lazy_loading: bool = False,
                       **kwargs) -> ImageFolder:
    """Create highly optimized ImageFolder using HuggingFace datasets backend"""
    return ImageFolder(
        root=root,
        img_shape=img_shape,
        img_mode=img_mode,
        cache_dir=cache_dir,
        num_proc=num_proc,
        streaming=streaming,
        lazy_loading=lazy_loading,
        **kwargs
    )


def create_vision_dataset(image_paths: List[str], 
                         labels: List[int],
                         img_shape: tuple = None,
                         cache_dir: Optional[str] = None,
                         num_proc: Optional[int] = None,
                         batch_size: int = 1000) -> Dataset:
    """Create optimized vision dataset from image paths and labels"""
    if not HF_AVAILABLE:
        raise ImportError("datasets package required. Install with: pip install datasets")
    
    if not PIL_AVAILABLE:
        raise ImportError("PIL required for image processing. Install with: pip install Pillow")
    
    def load_and_process_batch(examples):
        """Batch process images for maximum efficiency"""
        processed_images = []
        
        for img_path in examples['image_path']:
            try:
                img = Image.open(img_path)
                if img_shape:
                    img = img.resize((img_shape[1], img_shape[0]), Image.LANCZOS)
                img = img.convert('RGB')
                processed_images.append(np.array(img))
            except Exception as e:
                print(f"Error loading {img_path}: {e}")
                # Create dummy image
                dummy_shape = img_shape + (3,) if img_shape else (224, 224, 3)
                processed_images.append(np.zeros(dummy_shape, dtype=np.uint8))
        
        return {'features': processed_images, 'labels': examples['label']}
    
    # Create HF dataset
    hf_dataset = HFDataset.from_dict({
        'image_path': image_paths,
        'label': labels
    }, cache_dir=cache_dir)
    
    # Process images with optimized batching
    if num_proc is None:
        num_proc = min(4, mp.cpu_count()) if mp else 1
    
    processed_dataset = hf_dataset.map(
        load_and_process_batch,
        batched=True,
        batch_size=batch_size,
        num_proc=num_proc,
        cache_file_name=f"{cache_dir or 'cache'}/vision_dataset.arrow" if cache_dir else None,
        remove_columns=['image_path'],
        desc="Loading and processing images"
    )
    
    # Create Dataset wrapper
    dataset = Dataset.__new__(Dataset)
    dataset._hf_dataset = processed_dataset
    dataset.dtype = float32
    dataset._length = len(processed_dataset)
    dataset.lazy_loading = False
    dataset.streaming = False
    return dataset


def benchmark_dataloader_comprehensive(dataloader: DataLoader, 
                                     num_batches: int = 10,
                                     warmup_batches: int = 2,
                                     measure_memory: bool = True) -> Dict[str, Any]:
    """Comprehensive DataLoader performance benchmark"""
    if not PSUTIL_AVAILABLE:
        measure_memory = False
    
    results = {
        'warmup_times': [],
        'batch_times': [],
        'memory_usage': [],
        'batch_sizes': [],
        'throughput': 0,
        'avg_batch_time': 0,
        'std_batch_time': 0,
        'min_batch_time': 0,
        'max_batch_time': 0
    }
    
    # Memory monitoring
    if measure_memory:
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    dataloader_iter = iter(dataloader)
    
    # Warmup
    print(f"Starting warmup ({warmup_batches} batches)...")
    for i in range(warmup_batches):
        try:
            start_time = time.time()
            X, y = next(dataloader_iter)
            end_time = time.time()
            results['warmup_times'].append(end_time - start_time)
            print(f"Warmup batch {i+1}: {end_time - start_time:.4f}s, shape: {X.shape}")
        except StopIteration:
            print("Not enough batches for warmup")
            break
    
    # Actual benchmark
    print(f"Starting benchmark ({num_batches} batches)...")
    total_samples = 0
    
    for i in range(num_batches):
        try:
            if measure_memory:
                memory_before = process.memory_info().rss / 1024 / 1024
            
            start_time = time.time()
            X, y = next(dataloader_iter)
            end_time = time.time()
            
            batch_time = end_time - start_time
            batch_size = X.shape[0]
            total_samples += batch_size
            
            results['batch_times'].append(batch_time)
            results['batch_sizes'].append(batch_size)
            
            if measure_memory:
                memory_after = process.memory_info().rss / 1024 / 1024
                results['memory_usage'].append(memory_after - initial_memory)
            
            print(f"Batch {i+1}: {batch_time:.4f}s, {batch_size} samples, shape: {X.shape}")
            
        except StopIteration:
            print(f"DataLoader exhausted after {i} batches")
            break
        except Exception as e:
            print(f"Error in batch {i}: {e}")
            break
    
    # Calculate statistics
    if results['batch_times']:
        batch_times = np.array(results['batch_times'])
        results['avg_batch_time'] = float(np.mean(batch_times))
        results['std_batch_time'] = float(np.std(batch_times))
        results['min_batch_time'] = float(np.min(batch_times))
        results['max_batch_time'] = float(np.max(batch_times))
        
        total_time = np.sum(batch_times)
        results['throughput'] = total_samples / total_time if total_time > 0 else 0
        results['samples_per_second'] = results['throughput']
        
        if measure_memory and results['memory_usage']:
            results['avg_memory_usage'] = float(np.mean(results['memory_usage']))
            results['max_memory_usage'] = float(np.max(results['memory_usage']))
            results['initial_memory'] = float(initial_memory)
    
    # Print summary
    print("\n" + "="*50)
    print("BENCHMARK RESULTS")
    print("="*50)
    print(f"Total batches processed: {len(results['batch_times'])}")
    print(f"Total samples: {total_samples}")
    print(f"Average batch time: {results['avg_batch_time']:.4f}s ± {results['std_batch_time']:.4f}s")
    print(f"Throughput: {results['throughput']:.2f} samples/second")
    
    if measure_memory:
        print(f"Memory usage: {results.get('avg_memory_usage', 0):.1f} MB (avg), "
              f"{results.get('max_memory_usage', 0):.1f} MB (max)")
    
    return results


def benchmark_dataset_loading(dataset_creator: Callable, 
                             dataset_args: tuple = (),
                             dataset_kwargs: dict = None,
                             num_workers_list: List[int] = None,
                             batch_sizes: List[int] = None) -> Dict[str, Any]:
    """Benchmark different loading configurations"""
    if dataset_kwargs is None:
        dataset_kwargs = {}
    
    if num_workers_list is None:
        num_workers_list = [1, 2, 4] if mp else [1]
    
    if batch_sizes is None:
        batch_sizes = [16, 32, 64, 128]
    
    results = {}
    
    print("Creating dataset...")
    dataset = dataset_creator(*dataset_args, **dataset_kwargs)
    print(f"Dataset created with {len(dataset)} samples")
    
    for num_workers in num_workers_list:
        for batch_size in batch_sizes:
            if batch_size > len(dataset):
                continue
            
            config_name = f"workers_{num_workers}_batch_{batch_size}"
            print(f"\nTesting {config_name}...")
            
            dataloader = DataLoader(
                dataset,
                batch_size=batch_size,
                num_workers=num_workers,
                shuffle=True
            )
            
            # Quick benchmark
            benchmark_results = benchmark_dataloader_comprehensive(
                dataloader, 
                num_batches=5,
                warmup_batches=1,
                measure_memory=PSUTIL_AVAILABLE
            )
            
            results[config_name] = {
                'num_workers': num_workers,
                'batch_size': batch_size,
                'throughput': benchmark_results['throughput'],
                'avg_batch_time': benchmark_results['avg_batch_time'],
                'memory_usage': benchmark_results.get('avg_memory_usage', 0)
            }
    
    # Find best configuration
    best_config = max(results.items(), key=lambda x: x[1]['throughput'])
    
    print("\n" + "="*60)
    print("CONFIGURATION COMPARISON")
    print("="*60)
    for config, metrics in results.items():
        print(f"{config}: {metrics['throughput']:.1f} samples/s, "
              f"{metrics['avg_batch_time']:.4f}s/batch")
    
    print(f"\nBest configuration: {best_config[0]} "
          f"({best_config[1]['throughput']:.1f} samples/s)")
    
    return results


# Memory-efficient dataset splitting
def train_test_split_dataset(dataset: Dataset, 
                           test_size: float = 0.2,
                           random_state: Optional[int] = None,
                           stratify: bool = False) -> tuple:
    """Memory-efficient train/test split for datasets"""
    if dataset.streaming:
        raise NotImplementedError("Splitting not supported for streaming datasets")
    
    n = len(dataset)
    test_size_abs = int(n * test_size)
    train_size_abs = n - test_size_abs
    
    if HF_AVAILABLE and hasattr(dataset, '_hf_dataset'):
        # Use HF datasets efficient splitting
        if stratify and 'label' in dataset._hf_dataset.column_names:
            # Stratified split
            split_dataset = dataset._hf_dataset.train_test_split(
                test_size=test_size,
                seed=random_state,
                stratify_by_column='label'
            )
        else:
            # Random split
            split_dataset = dataset._hf_dataset.train_test_split(
                test_size=test_size,
                seed=random_state
            )
        
        # Create new Dataset wrappers
        train_dataset = Dataset.__new__(Dataset)
        train_dataset._hf_dataset = split_dataset['train']
        train_dataset.dtype = dataset.dtype
        train_dataset._length = len(split_dataset['train'])
        train_dataset.lazy_loading = dataset.lazy_loading
        train_dataset.streaming = False
        
        test_dataset = Dataset.__new__(Dataset)
        test_dataset._hf_dataset = split_dataset['test']
        test_dataset.dtype = dataset.dtype
        test_dataset._length = len(split_dataset['test'])
        test_dataset.lazy_loading = dataset.lazy_loading
        test_dataset.streaming = False
        
        return train_dataset, test_dataset
    else:
        # Fallback splitting
        indices = list(range(n))
        if random_state is not None:
            random.Random(random_state).shuffle(indices)
        else:
            random.shuffle(indices)
        
        train_indices = indices[:train_size_abs]
        test_indices = indices[train_size_abs:]
        
        train_X = [dataset._X[i] for i in train_indices]
        train_y = [dataset._y[i] for i in train_indices]
        test_X = [dataset._X[i] for i in test_indices]
        test_y = [dataset._y[i] for i in test_indices]
        
        return Dataset(train_X, train_y, dtype=dataset.dtype), \
               Dataset(test_X, test_y, dtype=dataset.dtype)