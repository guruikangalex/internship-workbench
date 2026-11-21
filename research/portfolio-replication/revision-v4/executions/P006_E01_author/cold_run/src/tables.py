"""R^2-by-theme LaTeX tables. The numbers come from pricing.r_2_table_gen[_beta];
this writes them as the paper's \\input-able .tex tables (ported from
rolling_window/plot_stuff.py::create_latex_table)."""
from src.pricing import r_2_table_gen, r_2_table_gen_beta
from src.constants import JKP_CLUSTERS

_R2_THEME_NOTE = (
    r"This table calculates the $R^{2}$ of SDF-based out-of-sample Sharpe ratio "
    r"predictions versus realized out-of-sample Sharpe ratios within each of the 13 "
    r"JKP factor themes.  $R^{2}$ represents fit versus the 45-degree line, as "
    r"described in the analysis of Figure \ref{fig:pricingacc}.")

_R2_BETA_SEC_NOTE = (
    r"Comparison of in-sample second-moment beta ($\mathbb{E}[FF'] w / w'\mathbb{E}[FF'] w$) "
    r"out-of-sample Sharpe ratio predictions versus realized out-of-sample Sharpe ratios for "
    r"test assets defined as the 153 JKP factors. $R^{2}$ represents fit versus the 45-degree "
    r"line for each JKP theme. Candidate SDFs are derived from UPSA, ridge, and LW optimal portfolios.")


def create_latex_table(r_2, path, caption, label, note, tab_col_sep="16pt", array_stretch="0.9"):
    column_format = "l" + "c" * len(r_2.columns)
    header = " & ".join(["Factor Theme"] + [str(c) for c in r_2.columns]) + r" \\"
    indices = list(r_2.index)
    lines = []
    for i, (idx, row) in enumerate(r_2.iterrows()):
        row_str = str(idx) + " & " + " & ".join(str(v) for v in row.values)
        row_str += r" \\[1.5ex]" if i == len(indices) - 2 else r" \\"
        lines.append(row_str)
    latex = (
        r"\begin{table}[!t]\begin{center}" "\n"
        r"\caption{\textbf{" + caption + r"}}\label{" + label + "}\n"
        r"\setlength{\tabcolsep}{" + tab_col_sep + "}\n"
        r"\renewcommand{\arraystretch}{" + array_stretch + "}\n"
        r"\vspace{-.4in}" "\n"
        r"\noindent\begin{minipage}[c]{1\textwidth}%" "\n"
        r"\singlespacing" "\n\\footnotesize\n" + note + "\n"
        r"\medskip\end{minipage}" "\n\\small\n"
        r"\begin{tabular}{" + column_format + "}\n\\hline\n" + header + "\n\\hline\n"
        + "\n".join(lines) + "\n\\hline\n"
        r"\end{tabular}" "\n\\end{center}\n\\end{table}")
    with open(path, "w") as f:
        f.write(latex)


def write_r2_theme_table(opt_port, factors, save_dir):
    r2 = r_2_table_gen(opt_port, factors, JKP_CLUSTERS).T.round(2)
    create_latex_table(r2, save_dir.rstrip("/") + "/r_2_theme.tex",
                        caption=r"Out-of-sample Pricing Accuracy By Factor Theme",
                        label="tab:r_2_theme", note=_R2_THEME_NOTE)


def write_r2_beta_sec_table(opt_port, betas_insample_sec, factors, save_dir):
    r2 = r_2_table_gen_beta(opt_port, betas_insample_sec, factors, JKP_CLUSTERS).T.round(2)
    create_latex_table(r2, save_dir.rstrip("/") + "/r_2_theme_beta_insample_sec.tex",
                        caption=r"Out-of-sample Pricing Accuracy By Factor Theme (In-Sample Second-Moment Beta)",
                        label="tab:r_2_theme_beta_insample_sec", note=_R2_BETA_SEC_NOTE)
