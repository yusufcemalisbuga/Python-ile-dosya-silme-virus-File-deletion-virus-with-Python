# ----------------------------------------------------------
# UYARI: Bu virusu kisisel bilgisayarinizda calistirmayin!
# Bu virus calistirildiginda, icinde oldugu klasordeki
# .py uzantili dosyalar HARIC her seyi geri dondurulemez
# bir sekilde siler!
# ----------------------------------------------------------
# WARNING: Never run this virus on your personal computer!
# When this virus is run, it irreversibly deletes everything
# except .py files in the folder it is in!
# ----------------------------------------------------------

import os
import sys

DANGEROUS_PATHS = {
    "/", "/bin", "/boot", "/dev", "/etc", "/home", "/lib",
    "/lib64", "/opt", "/proc", "/root", "/run", "/sbin",
    "/srv", "/sys", "/tmp", "/usr", "/var",
}

DRY_RUN = "--dry-run" in sys.argv


def is_safe_directory(path):
    """Refuse to operate inside system-critical directories."""
    resolved = os.path.realpath(path)
    if resolved in DANGEROUS_PATHS:
        return False
    for dangerous in DANGEROUS_PATHS:
        if resolved == dangerous or resolved.startswith(dangerous + "/"):
            depth = resolved[len(dangerous):].count("/")
            if depth < 2:
                return False
    return True


def confirm_action(file_count):
    """Require explicit user confirmation before deletion."""
    answer = input(
        f"\n{file_count} dosya silinecek / {file_count} file(s) will be "
        f"deleted. Devam? / Continue? [y/N]: "
    )
    return answer.strip().lower() == "y"


def main():
    work_dir = os.path.dirname(os.path.abspath(__file__)) or "."

    if not is_safe_directory(work_dir):
        print(
            "HATA / ERROR: Guvenli olmayan dizinde calistirildi. Iptal edildi."
            "\nRefusing to run in a system-critical directory. Aborted."
        )
        sys.exit(1)

    files = os.listdir(work_dir)

    targets = [
        f for f in files
        if not f.endswith(".py")
        and os.path.isfile(os.path.join(work_dir, f))
    ]

    if not targets:
        print("Silinecek dosya bulunamadi / No files to delete.")
        return

    if DRY_RUN:
        print("DRY RUN - silinecek dosyalar / files that would be deleted:")
        for f in targets:
            print(f"  {f}")
        return

    if not confirm_action(len(targets)):
        print("Iptal edildi / Aborted.")
        return

    for f in targets:
        filepath = os.path.join(work_dir, f)
        try:
            os.remove(filepath)
            print(f, "silindi / deleted")
        except IsADirectoryError:
            print(f, "bir klasor, atlandi / is a directory, skipped")
        except PermissionError:
            print(f, "izin hatasi, atlandi / permission error, skipped")
        except OSError as e:
            print(f, "silinemedi / could not delete:", e)

    print("Islem tamamlandi! / Operation complete!")


if __name__ == "__main__":
    main()
