#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
APP_PATH="$SCRIPT_DIR/Image Sorter.app"

command -v osacompile >/dev/null 2>&1 || {
    printf '%s\n' "Building the macOS app requires macOS and osacompile." >&2
    exit 1
}

osacompile -o "$APP_PATH" "$SCRIPT_DIR/macos_launcher.applescript"

cat > "$APP_PATH/Contents/MacOS/launch" <<'EOF'
#!/bin/sh
set -eu

APP_EXECUTABLE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$APP_EXECUTABLE_DIR/../../.." && pwd)
VENV_PYTHON="$PROJECT_DIR/../venv_imagesorter/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
    /usr/bin/osascript -e 'display dialog "The Image Sorter virtual environment was not found. Create it with: python3 -m venv ../venv_imagesorter" buttons {"OK"} with icon stop'
    exit 1
fi

exec "$VENV_PYTHON" "$PROJECT_DIR/run_image_sorter.py"
EOF

chmod +x "$APP_PATH/Contents/MacOS/launch"
printf 'Built %s\n' "$APP_PATH"
