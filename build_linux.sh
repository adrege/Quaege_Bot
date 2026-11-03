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

BUILD_DIR="${ROOT_DIR}/build"
DIST_DIR="${ROOT_DIR}/dist"
SPEC_DIR="${ROOT_DIR}/.pyinstaller-specs"
rm -rf "$BUILD_DIR" "$DIST_DIR" "$SPEC_DIR"
mkdir -p "$SPEC_DIR"
trap 'rm -rf "$SPEC_DIR"' EXIT

python3 -m PyInstaller --noconfirm --clean --onedir --name Quaege_Bot \
    "${PYINSTALLER_EXCLUDES[@]}" \
    --specpath "$SPEC_DIR" \
    --add-data "${ROOT_DIR}/scripts:scripts" \
    --add-data "${ROOT_DIR}/Adrege_logo.png:." \
    --add-data "${ROOT_DIR}/Adrege_logo_lang.png:." \
    --add-data "${ROOT_DIR}/config.py:." \
    --add-data "${ROOT_DIR}/settings.json:." \
    main_gui.py

for script in scripts/*.py; do
    name="$(basename "$script" .py)"
    python3 -m PyInstaller --noconfirm --clean --onefile \
        "${PYINSTALLER_EXCLUDES[@]}" \
        --specpath "$SPEC_DIR" \
        --name "$name" --distpath "$DIST_DIR/Quaege_Bot" \
        --add-data "${ROOT_DIR}/Adrege_logo.png:." \
        --add-data "${ROOT_DIR}/Adrege_logo_lang.png:." \
        --add-data "${ROOT_DIR}/settings.json:." \
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
