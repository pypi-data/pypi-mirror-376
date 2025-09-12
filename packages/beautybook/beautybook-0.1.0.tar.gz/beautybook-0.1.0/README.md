# BeautyBook

**BeautyBook** is a lightweight Python class for dynamic, real-time visualization of tabular data in Jupyter and Google Colab notebooks. Designed for iterative workflows like machine learning training loops, it renders a beautifully styled HTML table that updates in-place—no need for manual DataFrame reconstruction or external file writes.

---

## Features

- **Real-time Updates**: Clean, in-place table rendering using `IPython.display`, without cluttering notebook output.
- **Automatic Indexing**: Each entry is auto-numbered for easy tracking.
- **Responsive Styling**: Column widths adapt to content length using `ch` units for optimal readability.
- **Standalone Class**: Fully self-contained—just copy and paste into your notebook.

---

## Installation

BeautyBook is distributed as a single Python class. To use it, simply copy the class definition into a notebook cell:

```python
import uuid
from IPython.display import display, HTML

class BeautyBook:
    """
    A class to dynamically display data in a beautifully styled HTML table
    in a Jupyter/Colab environment.
    ... [rest of the code here]
    """
