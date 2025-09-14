"""
Neural Network components for NeuroGrad.

This module contains layers, loss functions, activation functions,
weight initializers, and other neural network building blocks.
"""

# Import submodules lazily to avoid circular imports
# Individual components can be imported directly as needed

# Import commonly used components for convenience
from .layers import (
    Module, Sequential, Linear, MLP, Conv2D, MaxPool2D, AveragePool2D, 
    MaxPooling2D, AveragePooling2D, BatchNorm, BatchNorm2D, Dropout, Dropout2D,
    Flatten, Pad
)
from .activations import ReLU, Sigmoid, Tanh, Softmax, LeakyReLU
from .losses import MSE, CrossEntropy, BCELoss
from .metrics import Accuracy, BinaryAccuracy, TopKAccuracy
from .initializers import Normal, Xavier, He, Zeros