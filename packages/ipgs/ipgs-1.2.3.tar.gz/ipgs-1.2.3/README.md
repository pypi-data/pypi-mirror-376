# iPgs – Interactive Animated Progress Bar for Jupyter

**iPgs** provides an interactive and animated progress bar designed for Jupyter Notebook and Google Colab environments. It enables clear visualization of training or processing progress, including nested loops such as epochs and batches, with automatic computation of estimated completion time (ETA).

This package is **framework-agnostic** and **dependency-free**, making it lightweight and easy to integrate into any Python workflow.

---

## Key Highlights

- **Interactive and Animated**: Real-time visual feedback enhances comprehension of long-running tasks, making iterative processes like model training more intuitive.  
- **Nested Progress Tracking**: Simultaneously displays epoch-level (outer) and batch-level (inner) progress, providing a granular view of the workflow.  
- **Automatic ETA Calculation**: Continuously estimates remaining time for both epochs and batches, improving planning and monitoring.  
- **Framework-Agnostic**: Fully compatible with PyTorch, TensorFlow, Keras, NumPy arrays, Python lists, or any iterable—no modifications required.  
- **Dependency-Free**: Relies only on built-in Python libraries and IPython display functionality, ensuring easy installation and minimal overhead.  
- **Flexible Usage**: Works seamlessly with both DataLoader-style iterables and standard Python loops, supporting diverse workflows.  

---

## Installation

```bash
pip install ipgs
```

## Usage Example
```
from ipgs import iPgs

for epoch_idx, batch_idx, batch in iPgs(loader, num_epochs=5, desc="Training"):
    bx, by = batch
    # training step
```