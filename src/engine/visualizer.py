import os
import io
import time
from pathlib import Path
from typing import Optional, Tuple
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt
import seaborn as sns
from config import settings

class Visualizer:
    """
    Handles theme styling and rendering of data science charts.
    """
    def __init__(self):
        os.makedirs(settings.charts_dir, exist_ok=True)
        self.apply_theme()

    @staticmethod
    def apply_theme():
        """Apply modern, sleek styling suitable for dark and light Telegram themes."""
        sns.set_theme(style="whitegrid", palette="muted")
        plt.rcParams.update({
            "figure.figsize": (9, 5),
            "figure.dpi": 150,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.labelweight": "medium",
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "font.family": "sans-serif",
            "figure.autolayout": True,
        })

    def save_current_figure(self, chat_id: int | str) -> Optional[Tuple[str, bytes]]:
        """
        Check if any active matplotlib figure exists, save it to disk and bytes,
        and clean up the figure memory.
        """
        fig_nums = plt.get_fignums()
        if not fig_nums:
            return None

        fig = plt.gcf()
        timestamp = int(time.time() * 1000)
        filename = f"chart_{chat_id}_{timestamp}.png"
        filepath = str(settings.charts_dir / filename)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=160)
        fig.savefig(filepath, format="png", bbox_inches="tight", dpi=160)
        plt.close(fig)
        plt.close("all")

        buf.seek(0)
        return filepath, buf.getvalue()

visualizer = Visualizer()
