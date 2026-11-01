#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

command -v rpmbuild >/dev/null || {
    echo "rpmbuild is required (Fedora: sudo dnf install rpm-build)." >&2
    exit 1
}

PYINSTALLER_EXCLUDES=(
    --exclude-module PyQt5
    --exclude-module PyQt6
    --exclude-module PySide2
    --exclude-module PySide6
)

python3 -m PyInstaller --noconfirm --clean --onedir --name Quaege_Bot \
    "${PYINSTALLER_EXCLUDES[@]}" \
    --add-data "scripts:scripts" \
    --add-data "Adrege_logo.png:." \
    --add-data "config.py:." \
    --add-data "settings.json:." \
    main_gui.py

for script in scripts/*.py; do
    name="$(basename "$script" .py)"
    python3 -m PyInstaller --noconfirm --clean --onefile \
        "${PYINSTALLER_EXCLUDES[@]}" \
        --name "$name" --distpath dist/Quaege_Bot \
        --add-data "Adrege_logo.png:." \
        --add-data "settings.json:." \
        "$script"
done

RPM_ROOT="${ROOT_DIR}/.rpmbuild"
rm -rf "$RPM_ROOT"
mkdir -p "$RPM_ROOT"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
rpmbuild -bb packaging/quaege-bot.spec \
    --define "_topdir ${RPM_ROOT}" \
    --define "_sourcedir ${ROOT_DIR}" \
    --define "_rpmdir ${ROOT_DIR}/dist/rpm"

echo "RPM package created in dist/rpm/"
