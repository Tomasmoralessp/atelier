# PyInstaller spec for the backend bundled inside the desktop app.
# Build: .venv/bin/pyinstaller atelier-backend.spec --noconfirm
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = [], [], []
for package in ("open_clip", "torchvision", "skimage", "lazy_loader"):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h
hiddenimports += collect_submodules("uvicorn")
hiddenimports += ["api", "database", "pipeline", "schemas", "main", "settings"]

a = Analysis(
    ["run.py"],
    pathex=["."],
    datas=datas,
    binaries=binaries,
    hiddenimports=hiddenimports,
    excludes=["matplotlib", "tkinter", "IPython", "pytest"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="atelier-backend", console=True)
coll = COLLECT(exe, a.binaries, a.datas, name="atelier-backend")
