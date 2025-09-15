#!/usr/bin/env bash
set -euo pipefail

echo "=== Building scd-matching-plugin Python wheel ==="

# Rust version check
echo "Rust version: $(rustc --version)"

# Activate local venv
echo "Setting up Python environment..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✓ Using virtual environment: $(pwd)/.venv"
else
    echo "No .venv found. Please create one with: python3.13 -m venv .venv"
    exit 1
fi

# Ensure maturin is installed
pip install --upgrade maturin wheel

# Cross-compile Windows wheel
echo "Cross-compiling Windows wheel..."
export PYTHON_SYS_EXECUTABLE="$(which python3.13)" # Point to your Python 3.13 executable
TARGET_TRIPLE="x86_64-pc-windows-msvc"

# Build the wheel for current Python version only
maturin build --release --target $TARGET_TRIPLE

echo "✅ Wheel build complete. Check the 'target/wheels' directory."
