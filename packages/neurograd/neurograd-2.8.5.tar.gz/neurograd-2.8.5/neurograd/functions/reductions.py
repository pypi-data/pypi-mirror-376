from neurograd import xp
import builtins
from .base import Function
from neurograd.nn.module import Module

# Cache for backend capabilities to avoid repeated checks
_is_cupy = hasattr(xp, 'cupy') and xp.__name__ == 'cupy'
_has_efficient_tuple_reduction = not _is_cupy  # NumPy handles tuple reductions efficiently

def _reduce(arr, axis, reduction_func, keepdims=False, **kwargs):
    """Optimized reduction helper with backend-aware implementation"""
    if axis is None or isinstance(axis, int):
        return reduction_func(arr, axis=axis, keepdims=keepdims, **kwargs)
    
    # For tuple axes, use the most efficient approach based on backend
    if _has_efficient_tuple_reduction:
        # Use native tuple reduction for backends that handle it well
        return reduction_func(arr, axis=axis, keepdims=keepdims, **kwargs)
    else:
        # For problematic backends (CuPy), use reshape approach
        ndim = arr.ndim
        axes = tuple(sorted(ax if ax >= 0 else ndim + ax for ax in axis))
        
        # Group axes for more efficient reduction
        non_axes = [i for i in range(ndim) if i not in axes]
        reduced_size = builtins.prod(arr.shape[ax] for ax in axes)
        
        # Reshape and reduce in one operation
        reshaped = arr.transpose(non_axes + list(axes)).reshape(
            *[arr.shape[i] for i in non_axes], reduced_size
        )
        result = reduction_func(reshaped, axis=-1, keepdims=keepdims, **kwargs)
        
        if keepdims:
            # Restore reduced dimensions as size 1
            new_shape = []
            for i in range(ndim):
                if i in axes:
                    new_shape.append(1)
                else:
                    new_shape.append(arr.shape[i])
            result = result.reshape(new_shape)
        
        return result

class Sum(Function, Module):
    name = "Sum"
    def __init__(self, axis=None, keepdims=False):
        super().__init__()  # Combined initialization
        self.axis = axis
        self.keepdims = keepdims
        
    def forward(self, x: xp.ndarray) -> xp.ndarray:
        self._input_shape = x.shape  # Cache for backward
        return _reduce(x, self.axis, xp.sum, keepdims=self.keepdims, dtype=xp.float32)
        
    def backward(self, grad_output: xp.ndarray) -> xp.ndarray:
        if not self.parent_tensors[0].requires_grad:
            return None
            
        grad = grad_output
        if not self.keepdims and self.axis is not None:
            # Expand dimensions for proper broadcasting
            axes = (self.axis,) if isinstance(self.axis, int) else self.axis
            for ax in sorted(axes):
                ax_norm = ax if ax >= 0 else len(self._input_shape) + ax
                grad = xp.expand_dims(grad, axis=ax_norm)
                
        return xp.broadcast_to(grad, self._input_shape)

class Mean(Function, Module):
    name = "Mean"
    def __init__(self, axis=None, keepdims=False):
        super().__init__()
        self.axis = axis
        self.keepdims = keepdims
        
    def forward(self, x: xp.ndarray) -> xp.ndarray:
        self._input_shape = x.shape
        
        # Calculate reduction factor
        if self.axis is None:
            self._n = x.size
        else:
            axes = (self.axis,) if isinstance(self.axis, int) else self.axis
            self._n = builtins.prod(
                x.shape[ax if ax >= 0 else len(x.shape) + ax] for ax in axes
            )
            
        return _reduce(x, self.axis, xp.mean, keepdims=self.keepdims, dtype=xp.float32)
        
    def backward(self, grad_output: xp.ndarray) -> xp.ndarray:
        if not self.parent_tensors[0].requires_grad:
            return None
            
        # Scale gradient by inverse of reduction count
        grad = grad_output / self._n
        
        if not self.keepdims and self.axis is not None:
            axes = (self.axis,) if isinstance(self.axis, int) else self.axis
            for ax in sorted(axes):
                ax_norm = ax if ax >= 0 else len(self._input_shape) + ax
                grad = xp.expand_dims(grad, axis=ax_norm)
                
        return xp.broadcast_to(grad, self._input_shape)

class Max(Function, Module):
    name = "Max"
    def __init__(self, axis=None, keepdims=False):
        super().__init__()
        self.axis = axis
        self.keepdims = keepdims
        
    def forward(self, x: xp.ndarray) -> xp.ndarray:
        self._input_shape = x.shape
        
        # Use keepdims=True for consistent backward handling
        self.max_vals = _reduce(x, self.axis, xp.max, keepdims=True)
        
        if self.keepdims:
            return self.max_vals
        else:
            # Squeeze reduced dimensions
            axes = (self.axis,) if isinstance(self.axis, int) else self.axis
            if axes is None:
                return self.max_vals.reshape(())
            axes = tuple(ax if ax >= 0 else x.ndim + ax for ax in axes)
            return xp.squeeze(self.max_vals, axis=axes)
            
    def backward(self, grad_output: xp.ndarray) -> xp.ndarray:
        if not self.parent_tensors[0].requires_grad:
            return None
            
        # Create mask for max values with proper tie handling
        mask = (self.parent_tensors[0].data == self.max_vals).astype(xp.float32)
        
        # Normalize for ties
        if self.axis is None:
            mask /= xp.sum(mask)
        else:
            count = _reduce(mask, self.axis, xp.sum, keepdims=True)
            mask /= xp.maximum(count, 1.0)  # Avoid division by zero
            
        # Expand gradient if needed
        grad = grad_output
        if not self.keepdims and self.axis is not None:
            axes = (self.axis,) if isinstance(self.axis, int) else self.axis
            for ax in sorted(axes):
                ax_norm = ax if ax >= 0 else len(self._input_shape) + ax
                grad = xp.expand_dims(grad, axis=ax_norm)
                
        return grad * mask

class Min(Function, Module):
    name = "Min"
    def __init__(self, axis=None, keepdims=False):
        super().__init__()
        self.axis = axis
        self.keepdims = keepdims
        
    def forward(self, x: xp.ndarray) -> xp.ndarray:
        self._input_shape = x.shape
        self.min_vals = _reduce(x, self.axis, xp.min, keepdims=True)
        
        if self.keepdims:
            return self.min_vals
        else:
            axes = (self.axis,) if isinstance(self.axis, int) else self.axis
            if axes is None:
                return self.min_vals.reshape(())
            axes = tuple(ax if ax >= 0 else x.ndim + ax for ax in axes)
            return xp.squeeze(self.min_vals, axis=axes)
            
    def backward(self, grad_output: xp.ndarray) -> xp.ndarray:
        if not self.parent_tensors[0].requires_grad:
            return None
            
        mask = (self.parent_tensors[0].data == self.min_vals).astype(xp.float32)
        
        if self.axis is None:
            mask /= xp.sum(mask)
        else:
            count = _reduce(mask, self.axis, xp.sum, keepdims=True)
            mask /= xp.maximum(count, 1.0)
            
        grad = grad_output
        if not self.keepdims and self.axis is not None:
            axes = (self.axis,) if isinstance(self.axis, int) else self.axis
            for ax in sorted(axes):
                ax_norm = ax if ax >= 0 else len(self._input_shape) + ax
                grad = xp.expand_dims(grad, axis=ax_norm)
                
        return grad * mask

class Std(Function, Module):
    name = "Std"
    def __init__(self, axis=None, keepdims=False, eps=1e-8):
        super().__init__()
        self.axis = axis
        self.keepdims = keepdims
        self.eps = eps
        
    def forward(self, x: xp.ndarray) -> xp.ndarray:
        self._input_shape = x.shape
        
        # Calculate reduction parameters
        if self.axis is None:
            self._n = x.size
        else:
            axes = (self.axis,) if isinstance(self.axis, int) else self.axis
            self._n = builtins.prod(
                x.shape[ax if ax >= 0 else len(x.shape) + ax] for ax in axes
            )
            
        # Compute mean and variance efficiently
        self.mean = _reduce(x, self.axis, xp.mean, keepdims=True, dtype=xp.float32)
        self.var = _reduce((x - self.mean)**2, self.axis, xp.mean, keepdims=True, dtype=xp.float32)
        
        std_vals = xp.sqrt(self.var + self.eps)
        
        if self.keepdims:
            return std_vals
        else:
            axes = (self.axis,) if isinstance(self.axis, int) else self.axis
            if axes is None:
                return std_vals.reshape(())
            axes = tuple(ax if ax >= 0 else x.ndim + ax for ax in axes)
            return xp.squeeze(std_vals, axis=axes)
            
    def backward(self, grad_output: xp.ndarray) -> xp.ndarray:
        if not self.parent_tensors[0].requires_grad:
            return None
            
        # Precompute common terms
        x_data = self.parent_tensors[0].data
        std_safe = xp.maximum(self.var + self.eps, self.eps)  # Avoid division by zero
        
        # Compute gradient efficiently
        base_grad = (x_data - self.mean) / (self._n * xp.sqrt(std_safe))
        
        # Expand gradient if needed
        grad = grad_output
        if not self.keepdims and self.axis is not None:
            axes = (self.axis,) if isinstance(self.axis, int) else self.axis
            for ax in sorted(axes):
                ax_norm = ax if ax >= 0 else len(self._input_shape) + ax
                grad = xp.expand_dims(grad, axis=ax_norm)
                
        return base_grad * grad

class Var(Function, Module):
    name = "Var"
    def __init__(self, axis=None, keepdims=False, ddof=0, eps=1e-8):
        super().__init__()
        self.axis = axis
        self.keepdims = keepdims
        self.ddof = ddof
        self.eps = eps
        
    def forward(self, x: xp.ndarray) -> xp.ndarray:
        self._input_shape = x.shape
        
        # Calculate reduction parameters
        if self.axis is None:
            self._n = x.size
        else:
            axes = (self.axis,) if isinstance(self.axis, int) else self.axis
            self._n = builtins.prod(
                x.shape[ax if ax >= 0 else len(x.shape) + ax] for ax in axes
            )
            
        # Compute mean and variance
        self.mean = _reduce(x, self.axis, xp.mean, keepdims=True, dtype=xp.float32)
        var_vals = _reduce((x - self.mean)**2, self.axis, xp.mean, keepdims=self.keepdims, dtype=xp.float32)
        
        # Apply Bessel's correction
        if self.ddof > 0:
            var_vals = var_vals * self._n / (self._n - self.ddof)
            
        return var_vals
        
    def backward(self, grad_output: xp.ndarray) -> xp.ndarray:
        if not self.parent_tensors[0].requires_grad:
            return None
            
        # Compute denominator with safety check
        denom = builtins.max(self._n - self.ddof, self.eps)
        
        # Compute gradient efficiently
        base_grad = 2.0 * (self.parent_tensors[0].data - self.mean) / denom
        
        # Expand gradient if needed
        grad = grad_output
        if not self.keepdims and self.axis is not None:
            axes = (self.axis,) if isinstance(self.axis, int) else self.axis
            for ax in sorted(axes):
                ax_norm = ax if ax >= 0 else len(self._input_shape) + ax
                grad = xp.expand_dims(grad, axis=ax_norm)
                
        return base_grad * grad

# Function shortcuts (unchanged)
def sum(x, axis=None, keepdims=False):
    return Sum(axis=axis, keepdims=keepdims)(x)

def mean(x, axis=None, keepdims=False):
    return Mean(axis=axis, keepdims=keepdims)(x)

def max(x, axis=None, keepdims=False):
    return Max(axis=axis, keepdims=keepdims)(x)

def min(x, axis=None, keepdims=False):
    return Min(axis=axis, keepdims=keepdims)(x)

def std(x, axis=None, keepdims=False):
    return Std(axis=axis, keepdims=keepdims)(x)

def var(x, axis=None, keepdims=False):
    return Var(axis=axis, keepdims=keepdims)(x)