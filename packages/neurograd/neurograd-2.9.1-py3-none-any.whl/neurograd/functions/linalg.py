from neurograd import xp
from .base import Function
from neurograd.nn.module import Module
from typing import TYPE_CHECKING, Union, Tuple, Sequence
from numpy.typing import ArrayLike
if TYPE_CHECKING:
    from neurograd.tensor import Tensor

def _transpose(arr):
    """Transpose that works for any ndim >= 1"""
    if arr.ndim == 1:
        return arr  # 1D arrays don't transpose
    elif arr.ndim == 2:
        return arr.T  # Use .T for 2D for efficiency
    else:
        return xp.swapaxes(arr, -2, -1)  # Swap last two axes for higher dims

# Matrix OPS classes for Functional API
# These classes implement matrix operations like matrix/tensor dot products, transpose, etc.
class MatMul(Function, Module):
    name = "MatMul"
    """Matrix multiplication A @ B with support for higher dimensions"""
    def __init__(self):
        Function.__init__(self)
        Module.__init__(self)
    def forward(self, A: xp.ndarray, B: xp.ndarray) -> xp.ndarray:
        return xp.matmul(A, B)
    def backward(self, grad_output: xp.ndarray) -> tuple[xp.ndarray, xp.ndarray]:
        A, B = self.parent_tensors
        grad_A = grad_B = None
        if A.requires_grad:
            grad_A = xp.matmul(grad_output, _transpose(B.data))
        if B.requires_grad:
            grad_B = xp.matmul(_transpose(A.data), grad_output)
        return grad_A, grad_B
    

class Linear(Function, Module):
    name = "Linear"
    """Applies a linear transformation: y = XW + b"""
    def __init__(self):
        Function.__init__(self)
        Module.__init__(self)
    def forward(self, X: xp.ndarray, W: xp.ndarray, b: xp.ndarray) -> xp.ndarray:
        out = xp.matmul(X, W)
        xp.add(out, b, out=out)
        return out
    def backward(self, grad_output: xp.ndarray) -> xp.ndarray:
        X, W, b = self.parent_tensors
        grad_X = xp.matmul(grad_output, _transpose(W.data)) if X.requires_grad else None
        grad_W = xp.matmul(_transpose(X.data), grad_output) if W.requires_grad else None
        grad_b = xp.sum(grad_output, axis=0) if b.requires_grad else None
        return grad_X, grad_W, grad_b


class TensorDot(Function, Module):
    name = "TensorDot"
    """Tensor contraction along specified axes"""
    def __init__(self, axes):
        Function.__init__(self)
        Module.__init__(self)
        self.axes = axes
        self.output_shape = None
    def forward(self, A: xp.ndarray, B: xp.ndarray) -> xp.ndarray:
        C = xp.tensordot(A, B, axes=self.axes)
        self.output_shape = C.shape
        return C    
    def backward(self, grad_output: xp.ndarray) -> xp.ndarray:
        A, B = self.parent_tensors
        # Parse axes consistently
        if isinstance(self.axes, int):
            # Contract last n axes of A with first n axes of B
            A_axes = list(range(A.ndim - self.axes, A.ndim))
            B_axes = list(range(self.axes))
        elif isinstance(self.axes, (list, tuple)) and len(self.axes) == 2:
            A_axes, B_axes = self.axes
            # Ensure they're lists for consistency
            if isinstance(A_axes, int):
                A_axes = [A_axes]
            if isinstance(B_axes, int):
                B_axes = [B_axes]
        else:
            raise ValueError(f"Invalid axes format: {self.axes}")       
        # Convert negative indices to positive
        A_axes = [(ax % A.ndim) for ax in A_axes]
        B_axes = [(ax % B.ndim) for ax in B_axes]
        # Find free (non-contracted) axes
        A_free = [i for i in range(A.ndim) if i not in A_axes]
        B_free = [i for i in range(B.ndim) if i not in B_axes]
        grad_A = grad_B = None   
        if A.requires_grad:
            grad_A = xp.tensordot(grad_output, B.data,
                                axes=[list(range(len(A_free), len(A_free) + len(B_free))), B_free])
            perm = [0] * A.ndim
            for i, ax in enumerate(A_free):
                perm[ax] = i
            for i, ax in enumerate(A_axes):
                perm[ax] = len(A_free) + i
            grad_A = xp.transpose(grad_A, perm)     
        if B.requires_grad:
            grad_B = xp.tensordot(A.data, grad_output,
                                axes=[A_free, list(range(len(A_free)))])
            perm = [0] * B.ndim
            for i, ax in enumerate(B_axes):
                perm[ax] = i
            for i, ax in enumerate(B_free):
                perm[ax] = len(B_axes) + i
            grad_B = xp.transpose(grad_B, perm) 
        return grad_A, grad_B

class EinSum(Function, Module):
    name = "EinSum"
    def __init__(self, subscripts: str, optimize=False):
        Function.__init__(self)
        Module.__init__(self)
        self.subscripts = subscripts.replace(" ", "")
        self.optimize = optimize
        self.contraction_path = None 
    def forward(self, *operands: xp.ndarray) -> xp.ndarray:
        self.operand_shapes = [op.shape for op in operands]
        self.input_operands = operands
        # Precompute contraction path if optimizing
        if self.optimize and self.contraction_path is None:
            try:
                import opt_einsum as oe
                path, _ = oe.contract_path(self.subscripts, *operands, optimize='optimal')
                self.contraction_path = path
            except ImportError:
                self.contraction_path = True  # Fallback to standard optimize
        return xp.einsum(self.subscripts, *operands, optimize=self.contraction_path if self.optimize else False)
    def backward(self, grad_output: xp.ndarray):
        grads = []
        # Parse the subscripts
        if '->' in self.subscripts:
            inputs_str, output_str = self.subscripts.split('->')
            input_specs = inputs_str.split(',')
        else:
            input_specs = self.subscripts.split(',')
            all_indices = ''.join(input_specs)
            output_str = ''.join(sorted(set(all_indices) - 
                                      set([idx for idx in all_indices 
                                           if all_indices.count(idx) > 1])))
        # Precompute common indices
        input_indices = [set(spec) for spec in input_specs]
        output_indices_set = set(output_str)
        for i, tensor in enumerate(self.parent_tensors):
            if not tensor.requires_grad:
                grads.append(None)
                continue  
            # Determine which indices need to be summed over
            current_indices = set(input_specs[i])
            sum_indices = current_indices - output_indices_set 
            # Build the gradient equation efficiently
            grad_equation = output_str + ","
            other_operands = []
            other_specs = [] 
            for j, spec in enumerate(input_specs):
                if j != i:
                    grad_equation += spec + ","
                    other_operands.append(self.parent_tensors[j].data)
                    other_specs.append(spec)
            # Remove trailing comma and add output spec
            grad_equation = grad_equation[:-1] + "->" + input_specs[i]         
            # Compute gradient
            try:
                # Use precomputed contraction path if available
                grad = xp.einsum(grad_equation, grad_output, *other_operands, 
                               optimize=self.contraction_path if self.optimize else False)
                
                # Handle broadcasting more efficiently
                grad = self._handle_broadcasting(grad, self.operand_shapes[i])
                grads.append(grad)
            except Exception as e:
                grads.append(xp.zeros_like(self.input_operands[i]))             
        return tuple(grads)
    def _handle_broadcasting(self, grad, original_shape):
        if grad.shape == original_shape:
            return grad    
        # Determine which axes need to be summed
        sum_axes = []
        for i, (g_dim, o_dim) in enumerate(zip(grad.shape, original_shape)):
            if o_dim == 1 and g_dim > 1:
                sum_axes.append(i)       
        # Sum over the necessary axes
        if sum_axes:
            grad = grad.sum(axis=tuple(sum_axes), keepdims=True)
        # Handle any remaining shape mismatches
        if grad.shape != original_shape:
            # This handles cases where dimensions were added during broadcasting
            for i in range(len(grad.shape) - len(original_shape)):
                grad = grad.sum(axis=0)         
        return grad

class Transpose(Function, Module):
    name = "Transpose"
    """Transpose of a matrix"""
    def __init__(self, axes=None):
        Function.__init__(self)
        Module.__init__(self)
        self.axes = axes # tuple of permuation
    def forward(self, A: xp.ndarray) -> xp.ndarray:
        if self.axes is None:
            self.axes = tuple(range(A.ndim - 2)) + (A.ndim - 1, A.ndim - 2)
        return xp.transpose(A, axes=self.axes)
    def backward(self, grad_output: xp.ndarray) -> xp.ndarray:
        A = self.parent_tensors[0]
        if not A.requires_grad:
            return None
        inv_axes = [0] * len(self.axes)
        for i, ax in enumerate(self.axes):
            inv_axes[ax] = i
        return xp.transpose(grad_output, axes=inv_axes) # inverse axes permuation


# Convenience function for matrix multiplication
# This function is designed to be used directly with Tensor objects.
def matmul(A, B):
    return MatMul()(A, B)
def linear(X, W, b):
    return Linear()(X, W, b)
def dot(A, B):
    return MatMul()(A, B)
def tensordot(A, B, axes):
    return TensorDot(axes)(A, B)
def einsum(subscripts: str, *operands: xp.ndarray, optimize = False) -> xp.ndarray:
    return EinSum(subscripts, optimize=optimize)(*operands)
def transpose(A, axes=None):
    return Transpose(axes)(A)