import neurograd as ng
from neurograd import xp
from .base import Function

class BatchNormalizer(Function):
    """
    Optimized batch normalization implementation
    y = var_scaler * (X - mean) / sqrt(var + eps) + mean_scaler
    """
    name = "BatchNormalizer"

    # ---- single-output fused kernels ----
    @ng.fuse
    def _fw_fused(X, mean, inv_std, var_scaler, mean_scaler):
        return var_scaler * ((X - mean) * inv_std) + mean_scaler

    @ng.fuse
    def _dX_fused(gY, inv_std, var_scaler):
        return gY * (var_scaler * inv_std)

    @ng.fuse
    def _combined_backward_terms(gY, x_centered, inv_std, inv_std3, var_scaler):
        # Compute multiple terms in a single fused operation
        dmean_term = gY * (-(var_scaler * inv_std))
        dvar_term = gY * (var_scaler * x_centered * (-0.5) * inv_std3)
        dvar_scaler_term = gY * (x_centered * inv_std)
        return dmean_term, dvar_term, dvar_scaler_term

    def __init__(self, axes, epsilon: float = 1e-5):
        super().__init__()
        self.axes = axes if isinstance(axes, tuple) else (axes,)
        self.epsilon = float(epsilon)
        self.cache = {}  # Cache for intermediate values

    def forward(self, X: xp.ndarray, mean: xp.ndarray, var: xp.ndarray,
                mean_scaler: xp.ndarray, var_scaler: xp.ndarray) -> xp.ndarray:
        # Use original dtype for computation (avoid casting if possible)
        inv_std = 1.0 / xp.sqrt(var + self.epsilon)
        
        # Cache values needed for backward pass
        self.cache.update({
            'X_shape': X.shape,
            'X_dtype': X.dtype,
            'inv_std': inv_std,
            'axes': self.axes
        })
        
        # Use fused operation
        out = BatchNormalizer._fw_fused(X, mean, inv_std, var_scaler, mean_scaler)
        return out

    def backward(self, grad_output: xp.ndarray):
        X, mean, var, mean_scaler, var_scaler = self.parent_tensors
        axes = self.cache['axes']
        inv_std = self.cache['inv_std']
        
        # Precompute frequently used values
        x_center = X.data - mean.data
        inv_std3 = inv_std * inv_std * inv_std  # More efficient than power operation
        
        # Compute gradients
        dX = (BatchNormalizer._dX_fused(grad_output, inv_std, var_scaler.data)
              if X.requires_grad else None)

        # Combined computation of multiple terms
        if any([mean.requires_grad, var.requires_grad, var_scaler.requires_grad]):
            dmean_term, dvar_term, dvar_scaler_term = BatchNormalizer._combined_backward_terms(
                grad_output, x_center, inv_std, inv_std3, var_scaler.data
            )
            
            dmean = (xp.sum(dmean_term, axis=axes, keepdims=True)
                     if mean.requires_grad else None)
            
            dvar = (xp.sum(dvar_term, axis=axes, keepdims=True)
                    if var.requires_grad else None)
            
            dvar_scaler = (xp.sum(dvar_scaler_term, axis=axes, keepdims=True)
                           if var_scaler.requires_grad else None)
        else:
            dmean = dvar = dvar_scaler = None

        dmean_scaler = (xp.sum(grad_output, axis=axes, keepdims=True)
                        if mean_scaler.requires_grad else None)

        return dX, dmean, dvar, dmean_scaler, dvar_scaler


def batch_normalize(X, mean, var, mean_scaler, var_scaler, axes, epsilon=1e-5):
    return BatchNormalizer(axes, epsilon)(X, mean, var, mean_scaler, var_scaler)