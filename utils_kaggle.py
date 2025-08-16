import os, json, stat, subprocess, sys
from pathlib import Path

def ensure_pkg(pkg: str):
    """Ensure that ``pkg`` is importable.

    If the package cannot be imported, an :class:`ImportError` is raised with
    a message instructing the user to install the dependency manually. This
    avoids implicitly installing packages at runtime and gives clearer feedback
    to the caller.
    """

    try:
        __import__(pkg)
    except ImportError as e:
        raise ImportError(
            f"Required package '{pkg}' is not installed. Please install it manually"
            f" (e.g., 'pip install {pkg}')."
        ) from e

def ensure_kaggle_token() -> None:
    home = Path.home()
    default = home / ".kaggle" / "kaggle.json"
    local   = Path("kaggle.json")

    if default.exists():
        print(f"✅ Kaggle token: {default}")
        return

    if local.exists():
        default.parent.mkdir(parents=True, exist_ok=True)
        default.write_bytes(local.read_bytes())
        os.chmod(default, stat.S_IRUSR | stat.S_IWUSR)
        print(f"✅ Installed local kaggle.json → {default}")
        return

    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        default.parent.mkdir(parents=True, exist_ok=True)
        data = {"username": os.environ["KAGGLE_USERNAME"], "key": os.environ["KAGGLE_KEY"]}
        default.write_text(json.dumps(data))
        os.chmod(default, stat.S_IRUSR | stat.S_IWUSR)
        print("✅ Created kaggle.json from env vars.")
        return

    raise FileNotFoundError("لم يتم العثور على kaggle.json (ضعه في ~/.kaggle/ أو بجذر المشروع أو كمتغيرات بيئة).")

def folder_has_content(path: str, min_files: int = 5) -> bool:
    p = Path(path)
    if not p.exists():
        return False
    count = 0
    for _, _, fns in os.walk(path):
        count += len(fns)
        if count >= min_files:
            return True
    return False

def kaggle_download(slug: str, dest: str, skip_if_exists: bool = True) -> None:
    from shutil import which
    if which("kaggle") is None:
        ensure_pkg("kaggle")

    dest_p = Path(dest)
    dest_p.mkdir(parents=True, exist_ok=True)
    if skip_if_exists and folder_has_content(dest, 5):
        print(f"⏭️ Skip existing: {slug}")
        return

    print(f"⏬ Downloading: {slug}")
    cmd = ["kaggle", "datasets", "download", "-d", slug, "-p", str(dest_p), "--unzip"]
    out = subprocess.run(cmd, capture_output=True, text=True)
    print(out.stdout)
    if out.returncode != 0:
        print(out.stderr)
        raise RuntimeError(f"فشل تنزيل: {slug}")
