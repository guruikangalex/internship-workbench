"""Shared plotting style: fixed colorblind-friendly method colors and a save
helper. Ported from helpers/plot_functions.py."""
import matplotlib.pyplot as plt

METHOD_COLORS = {
    "UPSA": "#006BA4",
    "Ridge": "#C85200",
    "LW": "#5FA55A",
    "PCA": "#D4A017",
    "FF5": "#8B6DAF",
    "CAPM": "#CC7B7B",
    "KNS": "#8B4513",
    "PCA SR": "#D4A017",
    "EW": "#5F9ED1",
    "Best z": "#C85200",
    "Ridge Economic": "#C85200",
    "Ridge Statistical": "#5FA55A",
}


def get_method_color(method):
    return METHOD_COLORS.get(method, "black")


def save(save_folder):
    if save_folder is None:
        plt.show()
    else:
        plt.savefig(save_folder, dpi=300, bbox_inches="tight")
        plt.close()
