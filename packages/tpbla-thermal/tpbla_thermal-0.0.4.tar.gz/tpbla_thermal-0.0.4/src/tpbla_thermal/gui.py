import os
import platform
from pathlib import Path
import pandas as pd
import numpy as np
import itertools
from scipy.integrate import simpson
import threading
from sklearn.preprocessing import StandardScaler
import joblib
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
import re
import warnings
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import tkinter.ttk as ttk

warnings.filterwarnings("ignore")

# Detect operating system
IS_WINDOWS = platform.system() == "Windows"

amino_acids = 'ACDEFGHIKLMNPQRSTVWY'

def generate_variants(sequence):
    variants = [sequence]
    for i in range(len(sequence)):
        for letter in amino_acids:
            if sequence[i] != letter:
                v = list(sequence)
                v[i] = letter
                variants.append(''.join(v))
    return variants

def write_excel(variants, output_file):
    pd.DataFrame({'Sequence': variants}).to_excel(output_file, index=False)

def calculate_aac(sequence, amino_acids):
    n = len(sequence)
    counts = {aa: 0 for aa in amino_acids}
    for aa in sequence:
        counts[aa] += 1
    return {aa: counts[aa] / n for aa in amino_acids}

def calculate_dpc(sequence, amino_acids, dipeptides):
    n = len(sequence) - 1
    counts = {dp: 0 for dp in dipeptides}
    for i in range(n):
        dp = sequence[i:i+2]
        counts[dp] += 1
    return {dp: counts[dp] / n for dp in dipeptides}

def calculate_mean(window, df_reference):
    vals = [df_reference.loc[aa, 'Value'] for aa in window]
    return sum(vals) / len(vals)

def calculate_auc(window, df_reference):
    vals = [df_reference.loc[aa, 'Value'] for aa in window]
    return simpson(vals, x=list(range(len(window))))

def convert_to_1_letter_code(var_seq, orig_seq):
    if pd.isna(var_seq):
        return None
    muts = []
    for i, (o, v) in enumerate(zip(orig_seq, var_seq)):
        if o != v:
            muts.append(f"{o}{i+1}{v}")
    return ",".join(muts) if muts else None

def parse_mutation_code(code):
    if pd.isna(code) or code == "":
        return []
    out = []
    for part in code.split(','):
        m = re.match(r'^([A-Z])(\d+)([A-Z])$', part.strip())
        if m:
            out.append({'mutation': m.group(3), 'position': int(m.group(2))})
    return out

def color_labels(text):
    if 'Mean' in text: return 'black'
    if 'P' in text:    return 'orange'
    if any(c in text for c in 'QNCTS'): return 'green'
    if any(c in text for c in 'DE'):    return 'red'
    if any(c in text for c in 'HRK'):   return 'blue'
    if any(c in text for c in 'WYF'):   return 'brown'
    if any(c in text for c in 'IMLVA'): return 'grey'
    if 'G' in text: return 'purple'
    return 'black'

class ProgressWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Progress")
        self.window.geometry("400x200")
        self.window.transient(parent)
        self.window.grab_set()

        self.label1 = tk.Label(self.window, text="Calculating AAC/DPC")
        self.label1.pack(pady=10)
        self.progress1 = ttk.Progressbar(self.window, orient='horizontal', length=300, mode='determinate')
        self.progress1.pack(pady=5)

        self.label2 = tk.Label(self.window, text="Processing Features")
        self.label2.pack(pady=10)
        self.progress2 = ttk.Progressbar(self.window, orient='horizontal', length=300, mode='determinate')
        self.progress2.pack(pady=5)

        self.completed = False

    def update_progress1(self, value, maximum):
        self.progress1['maximum'], self.progress1['value'] = maximum, value

    def update_progress2(self, value, maximum):
        self.progress2['maximum'], self.progress2['value'] = maximum, value

    def update_label2(self, text):
        self.label2.config(text=text)

    def close(self):
        self.window.destroy()

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip().replace(' ', '_')[:255]

def read_fasta_file(path):
    seqs, name, lines = [], None, []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith('>'):
                if name:
                    seqs.append((name, ''.join(lines)))
                name, lines = line[1:], []
            else:
                lines.append(line)
        if name:
            seqs.append((name, ''.join(lines)))
    return seqs

def run_analysis(ref_seq, job, root, prog):
    try:
        if any(res not in amino_acids for res in ref_seq):
            messagebox.showerror("Invalid Sequence", f"{job} contains invalid residues.")
            return

        dipeps = [''.join(p) for p in itertools.product(amino_acids, repeat=2)]
        variants = generate_variants(ref_seq)

        base = Path(job)
        base.mkdir(exist_ok=True) 
        (base / "sequence_variants").mkdir(exist_ok=True)
        var_file = base / "sequence_variants" / "sequence_variants.xlsx"
        write_excel(variants, var_file)

        df = pd.read_excel(var_file)
        cols = ['Sequence'] + list(amino_acids) + dipeps
        comp = pd.DataFrame(columns=cols)
        for idx, row in df.iterrows():
            seq = row['Sequence']
            rec = {**calculate_aac(seq, amino_acids),
                   **calculate_dpc(seq, amino_acids, dipeps),
                   'Sequence': seq}
            comp = pd.concat([comp, pd.DataFrame([rec])], ignore_index=True)
            prog.window.after(0, prog.update_progress1, idx+1, len(df))

        aacdir = base / "Sequence's_AAC_DPC"
        aacdir.mkdir(exist_ok=True)
        comp.to_excel(aacdir / "Sequence's_AAC_DPC.xlsx", index=False)

        df_feat = pd.read_excel(aacdir / "Sequence's_AAC_DPC.xlsx")
        seqs = df_feat['Sequence'].tolist()
        atlases = {
            '3_B_Atlas.xlsx':  'Bulkiness',
            '3_BT_Atlas.xlsx': 'Beta Turn Propensity',
            '3_cDR_Atlas.xlsx':'Coli Propensity',
            '3_CF_Atlas.xlsx': 'Beta Sheet Propensity',
            '3_Kd_Atlas.xlsx': 'hydrophobicity',
            '3_P_Atlas.xlsx':  'Polarity',
            '3_DR_Atlas.xlsx':'Alpha helicity'
        }

        total = len(atlases) * len(seqs)
        count = 0
        for fname, feat in atlases.items():
            prog.window.after(0, prog.update_label2, f"Processing {feat}")
            refdf = pd.read_excel(Path('required_docs') / fname, index_col=0)
            records = []
            for seq in seqs:
                rec = {'Sequence': seq}
                aucs = []
                for i in range(len(seq) - 8):
                    w = seq[i:i+9]
                    rec[f'Mean_{i+1}'] = calculate_mean(w, refdf)
                    aucs.append(calculate_auc(w, refdf))
                rec['AUC'] = sum(aucs) / len(aucs) if aucs else 0
                records.append(rec)
                count += 1
                prog.window.after(0, prog.update_progress2, count, total)

            aucdf = pd.DataFrame(records)
            wt = aucdf.loc[0, 'AUC']
            df_feat[feat] = aucdf['AUC'] - wt

        featdir = base / "sequences_with_features"
        featdir.mkdir(exist_ok=True)
        df_feat.to_excel(featdir / "sequences_with_features.xlsx", index=False)

        new = (pd.read_excel(featdir / "sequences_with_features.xlsx")
               .dropna().replace([np.inf, -np.inf], np.nan).dropna())
        rf = joblib.load('required_docs/ThermAL.joblib')
        X = new[rf.feature_names_in_]
        Xs = StandardScaler().fit_transform(X)
        new['Predicted Variant Fitness'] = rf.predict(Xs)

        pred_dir = base / 'Predicted_fitness'
        pred_dir.mkdir(exist_ok=True)
        new.to_excel(pred_dir / 'predicted_fitness.xlsx', index=False)

        var_df = pd.read_excel(var_file)
        var_df['1_letter_mutation'] = var_df['Sequence'].apply(
            lambda x: convert_to_1_letter_code(x, ref_seq)
        )
        res = pd.concat([new, var_df['1_letter_mutation']], axis=1).fillna('')
        parsed = res['1_letter_mutation'].apply(parse_mutation_code)
        expanded = []
        for idx, muts in parsed.items():
            if muts:
                for m in muts:
                    r = res.loc[idx].copy()
                    r['mutation'], r['position'] = m['mutation'], m['position']
                    expanded.append(r)
            else:
                r = res.loc[idx].copy()
                r['mutation'], r['position'] = None, None
                expanded.append(r)
        res = pd.DataFrame(expanded)

        mut_dir = base / 'Predicted_fitness_with_1_letter_mutations'
        mut_dir.mkdir(exist_ok=True)
        res.to_excel(mut_dir / 'Predicted_fitness_with_1_letter_mutations.xlsx', index=False)

        df_hm = pd.read_excel(mut_dir / 'Predicted_fitness_with_1_letter_mutations.xlsx')
        df_hm = df_hm.dropna(subset=['mutation', 'position'])
        df_hm['position'] = df_hm['position'].astype(int)
        order = list("GAVLMIFYWKRHDESTCNQP")
        pivot = df_hm.pivot_table(index='mutation', columns='position',
                                  values='Predicted Variant Fitness', aggfunc='mean').reindex(order)

        hm_dir = base / 'heatmap'
        hm_dir.mkdir(exist_ok=True)
        pivot.to_excel(hm_dir / 'heatmap_simple.xlsx')

        data = pd.read_excel(hm_dir / 'heatmap_simple.xlsx', index_col=0)
        wt = ref_seq
        rename_map = {
            pos: f"{wt[pos-1]}{pos}" if isinstance(pos, int) and pos <= len(wt) else f"X{pos}"
            for pos in data.columns
        }
        data.rename(columns=rename_map, inplace=True)
        data.to_excel(hm_dir / 'heatmap_with_WT_sequence.xlsx')

        # Heatmap plot
        cmap = LinearSegmentedColormap.from_list("custom_cmap", ["lightskyblue", "white", "red"])
        cmap.set_bad('#b0b0b0')
        plt.figure(figsize=(10,10))
        ax = sns.heatmap(data, cmap=cmap, center=0, square=True,
                         linewidths=2, linecolor='white',
                         cbar_kws={'label':'Predicted Variant Fitness','shrink':0.5})
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                mut = data.index[i]
                col = data.columns[j]
                m = re.match(r'^([A-Z])(\d+)$', col)
                if m and m.group(1) == mut:
                    ax.add_patch(Rectangle((j, i), 1, 1,
                                           fill=True, edgecolor='black',
                                           facecolor='white', lw=3, zorder=10))
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_edgecolor('black')
            spine.set_linewidth(2)

        ax.set_xlabel('Position', fontsize=16)
        ax.set_ylabel('Mutation', fontsize=16)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=90, fontsize=10)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=10)
        for lbl in ax.get_xticklabels():
            lbl.set_color(color_labels(lbl.get_text()))
        for lbl in ax.get_yticklabels():
            lbl.set_color(color_labels(lbl.get_text()))

        plt.tight_layout()
        plt.savefig(hm_dir / 'heatmap.png', dpi=300)
        plt.close()

        # Sliding-window plot
        df_sw = data.copy()
        df_sw.loc['Mean'] = df_sw.select_dtypes(include=[np.number]).mean(axis=0)
        sw = df_sw.loc['Mean'].rolling(window=5, min_periods=5, center=True).mean()

        x = list(range(len(sw)))
        y = -sw.values  # invert if desired

        fig, ax1 = plt.subplots(figsize=(10,5))
        ax1.plot(x, y, marker='o', linestyle='-')
        ax1.set_xlabel('Centre of Sliding Window (n=5)', fontsize=14)
        ax1.set_ylabel('Average Predicted Fitness', fontsize=14)
        ax1.set_title('Predicted Stabilising Regions (Corrected Sliding Window)', fontsize=16)
        ax1.set_xticks(x)
        ax1.set_xticklabels(data.columns, rotation=90, fontsize=10)
        for lbl in ax1.get_xticklabels():
            lbl.set_color(color_labels(lbl.get_text()))

        plt.tight_layout()
        plt.savefig(hm_dir / 'sliding_window_with_foldx.png', dpi=300, bbox_inches='tight')
        plt.close()

        # Display
        heat_img = Image.open(hm_dir / 'heatmap.png')
        sw_img   = Image.open(hm_dir / 'sliding_window_with_foldx.png')
        for img in (heat_img, sw_img):
            img.thumbnail((800,600), Image.LANCZOS)
        heat_ph = ImageTk.PhotoImage(heat_img)
        sw_ph   = ImageTk.PhotoImage(sw_img)

        w1 = tk.Toplevel(root)
        w1.title(f"Heatmap - {job}")
        tk.Label(w1, image=heat_ph).pack()
        w1.image = heat_ph

        w2 = tk.Toplevel(root)
        w2.title(f"Sliding Window Plot - {job}")
        tk.Label(w2, image=sw_ph).pack()
        w2.image = sw_ph

    except Exception as e:
        messagebox.showerror("Error", f"{job}: {e}")
    finally:
        prog.completed = True

def process_sequences():
    try:
        seqs = read_fasta_file(fasta_file_path)
        prog = ProgressWindow(root)
        prog.label1.config(text="Processing sequences")
        for idx, (name, seq) in enumerate(seqs):
            prog.window.after(0, prog.update_label2, f"Processing {idx+1}/{len(seqs)}: {name}")
            run_analysis(seq, sanitize_filename(name), root, prog)
            prog.update_progress1(0, 1)
            prog.update_progress2(0, 1)
        prog.close()
        messagebox.showinfo("Done", "Results are saved.")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        run_button.config(state='normal')

def create_gui():
    global root, run_button, fasta_file_path
    root = tk.Tk()
    root.title("ThermAL")
    root.configure(bg='white')

    w, h = 700, 600
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    try:
        logo = Image.open('ThermAL.png')
        logo.thumbnail((220,150), Image.LANCZOS)
        ph = ImageTk.PhotoImage(logo)
        tk.Label(root, image=ph, bg='white').pack(pady=10)
        root.logo_ph = ph
    except:
        pass

    tk.Label(root, text="Welcome to ThermAL! Please upload your FASTA file:",
             font=("Helvetica",16,"bold"), bg='white').pack(pady=10)

    fasta_file_path = None

    def select_fasta_file():
        global fasta_file_path
        fasta_file_path = filedialog.askopenfilename(
            title="Select FASTA File",
            filetypes=[("FASTA files", ("*.fasta","*.fa")), ("All files","*.*")]
        )
        fasta_file_label.config(text=f"Selected: {fasta_file_path}")

    fasta_file_label = tk.Label(root, text="No file selected",
                                font=("Helvetica",12), bg='white')
    fasta_file_label.pack(pady=5)

    tk.Button(root, text="Select FASTA File", command=select_fasta_file,
              font=("Helvetica",14,"bold"), bg='white', activebackground='#DA5B2D').pack(pady=10)

    def on_run():
        if not fasta_file_path:
            messagebox.showerror("Input Error", "Please select a FASTA file.")
            return
        run_button.config(state='disabled')
        threading.Thread(target=process_sequences).start()

    run_button = tk.Button(root, text="Run Analysis", command=on_run,
                           font=("Helvetica",14,"bold"), bg='white')
    run_button.pack(pady=20)

    tk.Label(root, text="Note: Only standard amino acid residues (ACDEFGHIKLMNPQRSTVWY) are accepted.",
             font=("Helvetica",12), fg='red', bg='white').pack(pady=5)

    root.mainloop()
 

def main():
    # tiny launcher so we can wire this to a console script
    create_gui()
