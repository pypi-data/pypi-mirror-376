import neurograd as ng
from neurograd import xp
from .base import Function

class BatchNormalizer(Function):
    """
    y = var_scaler * (X - mean) / sqrt(var + eps) + mean_scaler
    mean, var, mean_scaler, var_scaler are broadcastable to X and were
    computed with keepdims=True along `axes`.
    """
    name = "BatchNormalizer"

    # ---- single-output fused kernels ----
    @ng.fuse
    def _fw_fused(X, mean, inv_std, var_scaler, mean_scaler):
        return var_scaler * ((X - mean) * inv_std) + mean_scaler  # gamma * x_hat + beta

    @ng.fuse
    def _dX_fused(gY, inv_std, var_scaler):
        return gY * (var_scaler * inv_std)  # dX

    @ng.fuse
    def _dvar_term_fused(gY, x_centered, inv_std3, var_scaler):
        # gY * gamma * x_centered * (-1/2) * (var+eps)^(-3/2)
        return gY * (var_scaler * x_centered * (-0.5) * inv_std3)

    # ---- optimized multi-output fused kernels for backward pass ----
    @ng.fuse
    def _backward_combined_fused(gY, x_centered, inv_std, inv_std3, var_scaler):
        """Combined computation for multiple gradients to reduce memory allocations"""
        vs_f32 = xp.asarray(var_scaler, dtype=xp.float32)
        dX_term = gY * (vs_f32 * inv_std)  # for dX
        dvar_scaler_term = gY * (x_centered * inv_std)  # for dvar_scaler  
        dvar_term = gY * (vs_f32 * x_centered * (-0.5) * inv_std3)  # for dvar
        dmean_term = gY * (-(vs_f32 * inv_std))  # for dmean
        return dX_term, dvar_scaler_term, dvar_term, dmean_term

    def __init__(self, axes, epsilon: float = 1e-5):
        super().__init__()
        self.axes = axes if isinstance(axes, tuple) else (axes,)
        self.epsilon = float(epsilon)

    def forward(self, X: xp.ndarray, mean: xp.ndarray, var: xp.ndarray,
                mean_scaler: xp.ndarray, var_scaler: xp.ndarray) -> xp.ndarray:
        # Minimize type conversions by working in X's dtype when possible
        if X.dtype == xp.float32:
            # Work directly in float32 - no casting needed
            inv_std = 1.0 / xp.sqrt(var + self.epsilon)
            out = BatchNormalizer._fw_fused(X, mean, inv_std, var_scaler, mean_scaler)
            return out
        else:
            # Only cast to float32 for computation, then cast back
            inv_std = xp.asarray(1.0 / xp.sqrt(var + self.epsilon), dtype=xp.float32)
            mean32 = xp.asarray(mean, dtype=xp.float32)
            var_scaler32 = xp.asarray(var_scaler, dtype=xp.float32)
            mean_scaler32 = xp.asarray(mean_scaler, dtype=xp.float32)
            out = BatchNormalizer._fw_fused(X, mean32, inv_std, var_scaler32, mean_scaler32)
            return out.astype(X.dtype, copy=False)

    def backward(self, grad_output: xp.ndarray):
        X, mean, var, mean_scaler, var_scaler = self.parent_tensors
        axes = self.axes

        # Pre-compute common terms once
        inv_std = 1.0 / xp.sqrt(var.data + self.epsilon)
        x_center = X.data - mean.data
        inv_std3 = inv_std ** 3

        # Use combined fused kernel to compute all gradient terms at once
        dX_term, dvar_scaler_term, dvar_term, dmean_term = BatchNormalizer._backward_combined_fused(
            grad_output, x_center, inv_std, inv_std3, var_scaler.data
        )

        # Now do the reductions (only where gradients are needed)
        dX = dX_term if X.requires_grad else None
        
        dmean_scaler = (xp.sum(grad_output, axis=axes, keepdims=True)
                        if mean_scaler.requires_grad else None)

        dvar_scaler = (xp.sum(dvar_scaler_term, axis=axes, keepdims=True)
                       if var_scaler.requires_grad else None)

        dmean = (xp.sum(dmean_term, axis=axes, keepdims=True)
                 if mean.requires_grad else None)

        dvar = (xp.sum(dvar_term, axis=axes, keepdims=True)
                if var.requires_grad else None)
                
        # Cast dX back to input dtype if needed
        if dX is not None and dX.dtype != X.data.dtype:
            dX = dX.astype(X.data.dtype, copy=False)
            
        return dX, dmean, dvar, dmean_scaler, dvar_scaler


def batch_normalize(X, mean, var, mean_scaler, var_scaler, axes, epsilon=1e-5):
    return BatchNormalizer(axes, epsilon)(X, mean, var, mean_scaler, var_scaler)
