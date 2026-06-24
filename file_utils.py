# ----------------------------------------------------------
# Ortak dosya işlem yardımcıları / Shared file-operation utilities
# ----------------------------------------------------------
import os
from typing import List, Optional, Set


def log_operation(filename: str, message: str, success: bool = True) -> None:
    """Print a status line with a ✓ / ✗ indicator."""
    indicator = "✓" if success else "✗"
    print(f"{filename} {message} {indicator}")


def get_target_files(
    directory: str = ".",
    protected_extensions: Optional[Set[str]] = None,
) -> List[str]:
    """Return filenames in *directory* that are NOT protected by extension.

    Parameters
    ----------
    directory:
        Path to scan (default: current directory).
    protected_extensions:
        Set of extensions to keep (e.g. ``{".py"}``).  Files whose name
        ends with any of these extensions are excluded from the result.
    """
    if protected_extensions is None:
        protected_extensions = set()

    return [
        f
        for f in os.listdir(directory)
        if not any(f.endswith(ext) for ext in protected_extensions)
    ]


def safe_remove(filepath: str) -> bool:
    """Try to delete *filepath*; log the outcome and return success flag.

    Handles ``IsADirectoryError``, ``PermissionError``, and any other
    ``Exception`` so callers never need their own try/except block.
    """
    try:
        os.remove(filepath)
        log_operation(filepath, "silindi")
        return True
    except IsADirectoryError:
        log_operation(filepath, "bir klasör, atlandı", success=False)
    except PermissionError:
        log_operation(filepath, "izin hatası, atlandı", success=False)
    except Exception as e:
        log_operation(filepath, f"silinemedi: {e}", success=False)
    return False
