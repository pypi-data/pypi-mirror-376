import neurograd as ng
from neurograd import xp
from .base import Function

class BatchNormalizer(Function):
    name = "BatchNormalizer"

    @ng.fuse
    def _fw_fused(X, mean, inv_std, var_scaler, mean_scaler):
        return var_scaler * ((X - mean) * inv_std) + mean_scaler

    @ng.fuse
    def _dX_fused(gY, inv_std, var_scaler):
        return gY * (var_scaler * inv_std)

    @ng.fuse
    def _dmean_dvar_fused(gY, x_centered, inv_std, inv_std3, var_scaler):
        dmean = gY * (-var_scaler * inv_std)
        dvar = gY * var_scaler * x_centered * (-0.5) * inv_std3
        return dmean, dvar

    def __init__(self, axes, epsilon: float = 1e-5):
        super().__init__()
        self.axes = axes if isinstance(axes, tuple) else (axes,)
        self.epsilon = float(epsilon)

    def forward(self, X: xp.ndarray, mean: xp.ndarray, var: xp.ndarray,
                mean_scaler: xp.ndarray, var_scaler: xp.ndarray) -> xp.ndarray:
        # Precompute in float32 for better performance
        inv_std = xp.asarray(1.0 / xp.sqrt(var + self.epsilon), dtype=xp.float32)
        mean32 = xp.asarray(mean, dtype=xp.float32)
        var_scaler32 = xp.asarray(var_scaler, dtype=xp.float32)
        mean_scaler32 = xp.asarray(mean_scaler, dtype=xp.float32)
        
        # Store intermediate values for backward pass
        self.inv_std = inv_std
        self.x_centered = xp.asarray(X - mean, dtype=xp.float32)
        
        out = self._fw_fused(X, mean32, inv_std, var_scaler32, mean_scaler32)
        return out.astype(X.dtype, copy=False)

    def backward(self, grad_output: xp.ndarray):
        X, mean, var, mean_scaler, var_scaler = self.parent_tensors
        axes = self.axes
        
        # Use precomputed values from forward pass
        inv_std = self.inv_std
        x_centered = self.x_centered
        inv_std3 = inv_std ** 3

        dX = (self._dX_fused(grad_output, inv_std, xp.asarray(var_scaler.data, dtype=xp.float32))
              if X.requires_grad else None)

        dmean_scaler = (xp.sum(grad_output, axis=axes, keepdims=True)
                        if mean_scaler.requires_grad else None)

        dvar_scaler = (xp.sum(grad_output * (x_centered * inv_std), 
                              axis=axes, keepdims=True)
                       if var_scaler.requires_grad else None)

        if mean.requires_grad or var.requires_grad:
            dmean_term, dvar_term = self._dmean_dvar_fused(
                grad_output, x_centered, inv_std, inv_std3, 
                xp.asarray(var_scaler.data, dtype=xp.float32)
            )
            
            dmean = (xp.sum(dmean_term, axis=axes, keepdims=True) 
                     if mean.requires_grad else None)
            dvar = (xp.sum(dvar_term, axis=axes, keepdims=True) 
                    if var.requires_grad else None)
        else:
            dmean = dvar = None

        if dX is not None:
            dX = dX.astype(X.data.dtype, copy=False)
            
        return dX, dmean, dvar, dmean_scaler, dvar_scaler

def batch_normalize(X, mean, var, mean_scaler, var_scaler, axes, epsilon=1e-5):
    return BatchNormalizer(axes, epsilon)(X, mean, var, mean_scaler, var_scaler)