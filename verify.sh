#!/bin/sh
set -eu
cd "$(dirname "$0")"
# Sin pruebas todavía no hay nada que verificar; en cuanto existan, mandan.
if ls tests/test_*.py >/dev/null 2>&1; then
    exec python3 -B -m unittest discover -s tests -v
fi
echo "sin pruebas todavía"
