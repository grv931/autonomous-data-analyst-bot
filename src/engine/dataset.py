import os
import io
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
from config import settings

class DatasetManager:
    """
    Manages datasets per chat session.
    Supports CSV, Excel, JSON, TSV, Parquet.
    """
    def __init__(self):
        self._chat_datasets: Dict[int | str, pd.DataFrame] = {}
        self._chat_filenames: Dict[int | str, str] = {}
        os.makedirs(settings.data_dir, exist_ok=True)

    def load_from_bytes(self, chat_id: int | str, filename: str, content: bytes) -> Tuple[pd.DataFrame, str]:
        """Load dataframe from uploaded file bytes and cache it for the chat."""
        ext = Path(filename).suffix.lower()
        buf = io.BytesIO(content)

        if ext == ".csv":
            # Auto-detect separator if possible
            try:
                df = pd.read_csv(buf)
            except Exception:
                buf.seek(0)
                df = pd.read_csv(buf, sep=";")
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(buf)
        elif ext == ".json":
            df = pd.read_json(buf)
        elif ext == ".parquet":
            df = pd.read_parquet(buf)
        elif ext == ".tsv":
            df = pd.read_csv(buf, sep="\t")
        else:
            raise ValueError(f"Unsupported file format: {ext}. Supported: CSV, Excel (.xlsx/.xls), JSON, Parquet, TSV.")

        # Persist a copy to disk
        save_path = settings.data_dir / f"{chat_id}_{filename}"
        with open(save_path, "wb") as f:
            f.write(content)

        self._chat_datasets[chat_id] = df
        self._chat_filenames[chat_id] = filename
        return df, filename

    def set_dataset(self, chat_id: int | str, df: pd.DataFrame, name: str = "custom_dataset.csv"):
        self._chat_datasets[chat_id] = df
        self._chat_filenames[chat_id] = name

    def get_dataset(self, chat_id: int | str) -> Optional[pd.DataFrame]:
        return self._chat_datasets.get(chat_id)

    def get_filename(self, chat_id: int | str) -> Optional[str]:
        return self._chat_filenames.get(chat_id)

    def clear(self, chat_id: int | str):
        self._chat_datasets.pop(chat_id, None)
        self._chat_filenames.pop(chat_id, None)

    def get_summary_text(self, chat_id: int | str) -> str:
        """Generate a concise, LLM-ready markdown overview of the active dataset."""
        df = self.get_dataset(chat_id)
        if df is None:
            return "No dataset currently active in this session."

        fname = self.get_filename(chat_id) or "dataset"
        rows, cols = df.shape
        lines = [
            f"### Active Dataset: `{fname}`",
            f"- **Shape**: {rows:,} rows × {cols} columns",
            f"- **Memory Usage**: {df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB",
            "",
            "#### Column Information:",
        ]

        for col in df.columns[:30]:  # limit to first 30 cols
            dtype = str(df[col].dtype)
            nulls = int(df[col].isna().sum())
            null_pct = (nulls / rows) * 100 if rows > 0 else 0
            
            # Sample values / stats
            if pd.api.types.is_numeric_dtype(df[col]):
                min_val = df[col].min()
                max_val = df[col].max()
                mean_val = df[col].mean()
                stats_str = f"range=[{min_val}, {max_val}], mean={mean_val:.2f}"
            else:
                uniques = df[col].nunique()
                sample_vals = [str(x) for x in df[col].dropna().unique()[:3]]
                stats_str = f"{uniques} unique, samples={sample_vals}"

            lines.append(f"- **`{col}`** ({dtype}): {nulls} nulls ({null_pct:.1f}%), {stats_str}")

        if cols > 30:
            lines.append(f"... and {cols - 30} more columns.")

        return "\n".join(lines)

dataset_manager = DatasetManager()
