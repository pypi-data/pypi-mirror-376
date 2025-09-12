# ThermAL (**Therm**odynamics of **A**myloid **L**andscapes)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI - Version](https://img.shields.io/pypi/v/tpbla-thermal)](https://pypi.org/project/tpbla-thermal/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tpbla-thermal)](https://pypi.org/project/tpbla-thermal/)

<img src="ThermAL.png" alt="ThermAL Logo" width="300"/>

---

## 🔧 Installation

Install from **PyPI**:

```bash
pip install tpbla-thermal
```

Then run:

```bash
tpbla-thermal
```

---

## 📦 Requirements

- Python 3.8+

Dependencies (exact pins where required):

```bash
pip install pandas numpy scipy==1.9.3 scikit-learn==1.2.2 seaborn matplotlib pillow joblib openpyxl
```

---

## 🧪 What is ThermAL?

ThermAL is a tool for predicting regions that stabilise amyloid fibrils.

**Note:** The feature extraction step can be time-limiting for larger sequences. These features are reusable for other ML tasks.

ThermAL takes one or more FASTA sequences as input, generates all single–residue variants, computes physicochemical features (AAC, DPC, sliding-window AUC), feeds them into a pre-trained Random Forest model, and produces the following key outputs:

- `Predicted_fitness_with_1_letter_mutations.xlsx`
- `heatmap_simple.xlsx`
- `heatmap.png`
- `sliding_window.xlsx`
- `sliding_window_with_foldx.png`

All outputs are written into per-job directories named after each input sequence.

---

## 📁 Project Structure

```
/ThermAL
│
├── required_docs/                  ← precomputed resources
│   ├── 3_B_Atlas.xlsx
│   ├── 3_BT_Atlas.xlsx
│   ├── 3_cDR_Atlas.xlsx
│   ├── 3_CF_Atlas.xlsx
│   ├── 3_Kd_Atlas.xlsx
│   ├── 3_P_Atlas.xlsx
│   ├── 3_DR_Atlas.xlsx
│   └── ThermAL.joblib
│
├── ThermAL.png                     ← logo displayed in GUI
├── src/tpbla_thermal/              ← package source
│   ├── __init__.py
│   ├── cli.py
│   └── gui.py
└── README.md
```

---

## 🚀 Usage (GUI)

1. Launch the GUI:

```bash
tpbla-thermal-gui
```

2. In the GUI:
   - Click **Select FASTA File** and choose your `.fasta` or `.fa` file.
   - Click **Run Analysis**.
   - Progress bars will update during AAC/DPC and feature processing.

When complete, you’ll find a subfolder per sequence in the working directory containing the outputs above.

---

## 📬 Contact

Any problems, feel free to reach out:  
📧 conor_mckay98@aol.com  
🔗 [LinkedIn](https://www.linkedin.com/in/conor-mckay-babba7171/)
