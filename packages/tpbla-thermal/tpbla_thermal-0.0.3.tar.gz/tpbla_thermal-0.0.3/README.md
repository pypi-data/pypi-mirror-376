[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) ![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

![ThermAL Logo](ThermAL.png)

**TPBLA_ThermAL** is a desktop GUI tool for predicting regions that stabilise amyloid fibrils.  
It takes one or more FASTA sequences as input, generates single–residue variants, extracts physicochemical features, and predicts fitness landscapes using a pre-trained Random Forest model.

---

## 🚀 Quick install (development)

```bash
# Clone the repository
git clone https://github.com/conor-mckay98/ThermAL
cd ThermAL

# Install in editable mode
python -m pip install -e .

# Run the GUI
tpbla-thermal

📦 Requirements

    Python 3.8+

    scikit-learn==1.2.2

    scipy==1.9.3

    pandas

    numpy

    joblib

    seaborn

    matplotlib

    openpyxl

    pillow

    tk (comes with most Python distributions, but may require sudo apt-get install python3-tk on Linux)

All dependencies are declared in pyproject.toml and will be installed automatically with pip.
🧠 How it works

ThermAL generates and evaluates variants of input sequences:

    Input: FASTA file(s) with protein sequence(s).

    Variant generation: Creates all single–residue variants.

    Feature extraction:

        Amino Acid Composition (AAC)

        Dipeptide Composition (DPC)

        Sliding window AUC of physicochemical properties (Bulkiness, Polarity, Hydrophobicity, etc.).

    Prediction: Pre-trained Random Forest model scores variant fitness.

    Output: Excel tables and plots, saved per-sequence.

📁 Project Structure

ThermAL/
│
├── src/tpbla_thermal/        ← Python package
│   ├── cli.py                ← CLI entrypoint
│   └── gui.py                ← GUI implementation
│
├── required_docs/            ← model + reference atlases (not tracked in GitHub)
│   ├── 3_B_Atlas.xlsx
│   ├── 3_BT_Atlas.xlsx
│   ├── … (other atlas files)
│   └── ThermAL.joblib
│
├── ThermAL.png               ← logo displayed in GUI
├── ThermAL.ipynb             ← development notebook
├── pyproject.toml             ← build config (dependencies, entrypoints)
├── LICENSE
└── README.md                  ← this file

🎛️ Usage

    Ensure the required_docs/ folder (with all .xlsx atlases and the model file ThermAL.joblib) is present.

    Run:

tpbla-thermal

    In the GUI:

        Select FASTA File → choose your .fasta or .fa.

        Run Analysis → progress bars update as AAC/DPC and feature extraction run.

        Results are written into a folder named after each sequence header.

🔍 Outputs

Inside each job folder (named after the FASTA header), you’ll find:

    Predicted_fitness_with_1_letter_mutations.xlsx
    Full table of variants, predictions, and mutation codes.

    heatmap_simple.xlsx
    Pivot table of mean predicted fitness per mutation/position.

    heatmap.png
    Visual heatmap (blue→white→red), wild-type cells bordered in black.

    sliding_window.xlsx
    5-residue sliding window average of predicted fitness.

    sliding_window_with_foldx.png
    Plot highlighting stabilising regions.

📖 Citation

If you use this tool, please cite:

> McKay et al., 2025
> *"TPBLA_ThermAL: Machine learning for amyloid thermodynamic landscape prediction"*
"TPBLA_ThermAL: Machine learning for amyloid thermodynamic landscape prediction"

(CITATION.cff coming soon for GitHub citation support.)
🤝 Contact

Any problems or questions?
📧 conor_mckay98@aol.com

🔗 [LinkedIn](https://www.linkedin.com/in/conor-mckay-babba7171/)

PhD Student @ University of Leeds
