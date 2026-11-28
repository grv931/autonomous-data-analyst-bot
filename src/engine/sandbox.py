import sys
import io
import traceback
from dataclasses import dataclass
from typing import Any, Optional, Dict, Tuple
import pandas as pd
import numpy as np
import scipy
import matplotlib.pyplot as plt
import seaborn as sns
from config import settings
from src.engine.visualizer import visualizer

ALLOWED_MODULES = {
    "math", "numpy", "np", "pandas", "pd", "scipy", "matplotlib", "matplotlib.pyplot", "plt",
    "seaborn", "sns", "datetime", "re", "collections", "itertools", "statistics"
}

def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    root_pkg = name.split(".")[0]
    if root_pkg in ALLOWED_MODULES or name in ALLOWED_MODULES:
        return __import__(name, globals, locals, fromlist, level)
    raise ImportError(f"Import of module '{name}' is restricted in the execution sandbox.")

@dataclass
class ExecutionResult:
    success: bool
    stdout: str
    output_value: Any
    chart_path: Optional[str] = None
    chart_bytes: Optional[bytes] = None
    error: Optional[str] = None

class CodeSandbox:
    """
    Executes Python data analysis code in a controlled environment.
    Captures stdout, returned expressions, and generated Matplotlib/Seaborn plots.
    """
    def __init__(self, timeout: int = settings.code_exec_timeout):
        self.timeout = timeout

    def execute(self, code: str, chat_id: int | str, df: Optional[pd.DataFrame] = None) -> ExecutionResult:
        # Pre-clean matplotlib
        plt.close("all")
        visualizer.apply_theme()

        # Build clean execution scope
        stdout_buf = io.StringIO()
        old_stdout = sys.stdout

        local_scope: Dict[str, Any] = {
            "pd": pd,
            "np": np,
            "scipy": scipy,
            "plt": plt,
            "sns": sns,
            "df": df.copy() if df is not None else None,
            "result": None,
        }

        # Safe builtins
        safe_builtins = {
            "__import__": safe_import,
            "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
            "enumerate": enumerate, "filter": filter, "float": float, "format": format,
            "int": int, "isinstance": isinstance, "issubclass": issubclass, "iter": iter,
            "len": len, "list": list, "map": map, "max": max, "min": min, "next": next,
            "print": print, "range": range, "reversed": reversed, "round": round,
            "set": set, "slice": slice, "sorted": sorted, "str": str, "sum": sum,
            "tuple": tuple, "type": type, "zip": zip, "True": True, "False": False, "None": None,
        }
        global_scope = {"__builtins__": safe_builtins}

        try:
            sys.stdout = stdout_buf
            # Execute script
            exec(code, global_scope, local_scope)
            sys.stdout = old_stdout
            stdout_str = stdout_buf.getvalue()

            # Retrieve result variable if assigned
            output_val = local_scope.get("result")

            # Check if a chart was rendered
            chart_info = visualizer.save_current_figure(chat_id)
            chart_path = chart_info[0] if chart_info else None
            chart_bytes = chart_info[1] if chart_info else None

            return ExecutionResult(
                success=True,
                stdout=stdout_str,
                output_value=output_val,
                chart_path=chart_path,
                chart_bytes=chart_bytes,
                error=None,
            )

        except Exception as e:
            sys.stdout = old_stdout
            err_msg = traceback.format_exc()
            return ExecutionResult(
                success=False,
                stdout=stdout_buf.getvalue(),
                output_value=None,
                chart_path=None,
                chart_bytes=None,
                error=f"{type(e).__name__}: {str(e)}",
            )
        finally:
            sys.stdout = old_stdout

sandbox = CodeSandbox()
