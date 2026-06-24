# Python ile Dosya Silme / File Deletion Script with Python

> **UYARI / WARNING**
>
> Bu script calistirildiginda, bulundugu klasordeki `.py` uzantili dosyalar
> haric tum dosyalari **geri dondurulemez** olarak siler.
> Kisisel bilgisayarinizda calistirmadan once ne yaptiginizi bildiginizden
> emin olun.
>
> When run, this script **irreversibly deletes** every non-`.py` file in its
> directory. Make sure you understand what it does before running it on your
> personal computer.

## Safety Features

- **Confirmation prompt** -- asks `[y/N]` before deleting anything.
- **System-directory guard** -- refuses to run inside `/`, `/home`, `/etc`,
  and other critical paths.
- **Dry-run mode** -- pass `--dry-run` to preview which files would be deleted
  without actually removing them.
- **`__main__` guard** -- the script only executes when run directly, not when
  imported.

## Usage

```bash
# Preview what would be deleted
python virus.py --dry-run

# Run for real (requires confirmation)
python virus.py
```
