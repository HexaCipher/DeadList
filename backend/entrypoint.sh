#!/bin/bash
set -e

SYMBOLS_DIR="/opt/volatility3/volatility3/symbols"
SYMBOLS_MARKER="$SYMBOLS_DIR/.symbols_installed"
SYMBOLS_URL="https://downloads.volatilityfoundation.org/volatility3/symbols/windows.zip"

# ── Download Windows symbol tables on first run ───────────────
if [ ! -f "$SYMBOLS_MARKER" ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║  DeadList — First Run Setup                             ║"
    echo "║  Downloading Windows symbol tables (~800 MB)...         ║"
    echo "║  This only happens ONCE. Please wait.                   ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""

    if curl -L --retry 3 --retry-delay 10 --progress-bar \
        -o /tmp/windows_symbols.zip "$SYMBOLS_URL"; then

        echo "Extracting symbols..."
        python -c "
import zipfile, sys
try:
    with zipfile.ZipFile('/tmp/windows_symbols.zip', 'r') as z:
        z.extractall('$SYMBOLS_DIR')
    print('Symbol tables installed successfully!')
except Exception as e:
    print(f'Extraction failed: {e}', file=sys.stderr)
    sys.exit(1)
"
        rm -f /tmp/windows_symbols.zip
        touch "$SYMBOLS_MARKER"
        echo ""
        echo "✅ Symbol tables ready. DeadList can now analyze Windows memory dumps."
        echo ""
    else
        echo ""
        echo "⚠️  Symbol download failed. DeadList will start but real analysis"
        echo "   may not work. You can manually download symbols later from:"
        echo "   $SYMBOLS_URL"
        echo "   Place them in: $SYMBOLS_DIR"
        echo ""
    fi
else
    echo "✅ Symbol tables already installed."
fi

# ── Start the application ─────────────────────────────────────
echo "☠ Starting DeadList..."
exec "$@"
