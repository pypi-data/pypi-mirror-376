# readgrid

**readgrid** is a Python package for **document layout analysis and content extraction**.  
It lets you upload scanned documents, automatically detect tables and images, manually adjust bounding boxes, and extract clean structured output using LLMs.

---

## ✨ Features
- **Stage 1 – Upload & Detect**
  - Upload document images.
  - Automatically detect **tables** (red boxes) and **images** (green boxes).
  - Manually edit bounding boxes with an interactive editor.

- **Stage 2 – Coordinate Testing**
  - Verify detected regions with side-by-side previews.
  - Test either existing detections or custom coordinates.

- **Stage 3 – Content Extraction**
  - Extract structured JSON output (header, text, footer).
  - Replace detected tables with clean HTML `<table>` tags.
  - Insert `[image]` placeholders with captions in reading order.
  - Supports LaTeX formatting for equations.

- **Utility Functions**
  - `pretty_print_page_with_image()` – inspect extracted results with annotated images.
  - `show_comparison_view()` – compare annotated vs. reconstructed content.
  - `cleanup_pipeline()` – reset all artifacts.

---

## 🚀 Installation
```bash
pip install readgrid
```

---

## 🛠️ Usage

### Stage 1: Upload, Detect, and Edit

```python
from readgrid import stage_1

stage_1()
```

### Stage 2: Test Coordinates

```python
from readgrid import stage_2

stage_2(
    row_id="ID_1",
    box_type="tables",
    box_index=0
)
```

### Stage 3: Extract with Gemini

```python
from readgrid import stage_3

stage_3(api_key="YOUR_API_KEY")
```

---

## 📦 Requirements

* Python 3.8+
* [OpenCV](https://pypi.org/project/opencv-python/)
* [NumPy](https://pypi.org/project/numpy/)
* [Pillow](https://pypi.org/project/Pillow/)
* google-generativeai

---

## 📄 License

MIT License.
See LICENSE for details.