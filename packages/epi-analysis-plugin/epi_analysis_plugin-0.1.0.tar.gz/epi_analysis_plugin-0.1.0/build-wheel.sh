#!/usr/bin/env bash
set -euo pipefail

# Configuration
PROJECT_NAME="scd-matching-plugin"
WHEEL_OUTPUT_DIR="target/wheels"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Build targets configuration
declare -A BUILD_TARGETS=(
    #["linux"]="x86_64-unknown-linux-gnu"
    ["windows"]="x86_64-pc-windows-msvc"
    #["macos"]="x86_64-apple-darwin"
    #["macos-universal"]="universal2-apple-darwin"
)

# Utility functions
log_info() { echo -e "${BLUE}$1${NC}"; }
log_success() { echo -e "${GREEN}✓ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
log_error() { echo -e "${RED}✗ $1${NC}"; }

check_command() {
    local cmd=$1
    local install_hint=$2

    if ! command -v "$cmd" &>/dev/null; then
        log_error "$cmd not found"
        log_warning "$install_hint"
        return 1
    fi
    return 0
}

check_rust_version() {
    local required_version="1.70.0"
    if command -v rustc &>/dev/null; then
        local rust_version=$(rustc --version | awk '{print $2}')
        log_info "Rust version: $rust_version"
        # Note: This is a simple check, real version comparison would be more complex
        if [[ "$rust_version" < "$required_version" ]]; then
            log_warning "Rust version $rust_version may be too old. Recommended: $required_version+"
        fi
    fi
}

setup_python_env() {
    log_info "Setting up Python environment..."

    # Unset CONDA_PREFIX to avoid conflicts (similar to Makefile)
    unset CONDA_PREFIX 2>/dev/null || true

    # Activate the local .venv if it exists
    if [[ -f ".venv/bin/activate" ]]; then
        log_info "Activating local .venv..."
        source .venv/bin/activate
        log_success "Using virtual environment: $VIRTUAL_ENV"
    elif [[ -z "${VIRTUAL_ENV:-}" ]]; then
        log_warning "No local .venv found and not in a virtual environment."
        log_warning "Consider running 'make venv' first or activate a virtual environment."
        log_info "Continuing with system Python..."
    else
        log_success "Using existing virtual environment: $VIRTUAL_ENV"
    fi

    # Install/upgrade build dependencies
    pip install --upgrade maturin pip wheel
}

build_wheel() {
    local target=$1
    local target_name=$2

    log_info "Building $target_name wheel..."

    # Add target if not already present
    rustup target add "$target" 2>/dev/null || true

    # Build wheel with maturin for current Python version only (handles cross-compilation internally)
    if maturin build --release --target "$target" --out "$WHEEL_OUTPUT_DIR" --interpreter "$(which python)"; then
        log_success "$target_name wheel built successfully"
        return 0
    else
        log_error "$target_name wheel build failed"
        return 1
    fi
}

test_wheel() {
    local wheel_path=$1
    log_info "Testing wheel: $(basename "$wheel_path")"

    # Create temporary test environment
    local test_dir=$(mktemp -d)
    local test_venv="$test_dir/test_env"

    python -m venv "$test_venv"
    source "$test_venv/bin/activate"

    # Install wheel and test import
    pip install "$wheel_path" polars

    if python -c "from matching_plugin import complete_scd_matching_workflow; print('✓ Import successful')"; then
        log_success "Wheel test passed"
        deactivate
        rm -rf "$test_dir"
        return 0
    else
        log_error "Wheel test failed"
        deactivate
        rm -rf "$test_dir"
        return 1
    fi
}

show_build_summary() {
    log_info "=== Build Summary ==="

    local wheel_count=0
    local total_size=0

    for wheel in "$WHEEL_OUTPUT_DIR"/*.whl; do
        if [[ -f "$wheel" ]]; then
            ((wheel_count++))
            local basename_wheel=$(basename "$wheel")
            local size_bytes=$(stat -f%z "$wheel" 2>/dev/null || stat -c%s "$wheel" 2>/dev/null || echo "0")
            local size_mb=$((size_bytes / 1024 / 1024))
            local platform=$(basename "$wheel" | sed 's/.*-\(.*\)\.whl/\1/')

            log_success "$basename_wheel"
            echo -e "  → Size: ${size_mb}MB, Platform: ${platform}"

            total_size=$((total_size + size_bytes))
        fi
    done

    if [[ $wheel_count -eq 0 ]]; then
        log_error "No wheels were built successfully"
        return 1
    fi

    local total_size_mb=$((total_size / 1024 / 1024))
    log_info ""
    log_info "Built $wheel_count wheel(s), total size: ${total_size_mb}MB"
    log_info ""
    log_info "PyPI deployment ready!"
    log_info "Upload with: twine upload $WHEEL_OUTPUT_DIR/*.whl"
    log_info ""
    log_info "Test locally with:"
    log_info "  pip install $WHEEL_OUTPUT_DIR/<wheel-name>.whl"
    log_info ""
    log_info "Quick test command:"
    log_info "  python -c \"from matching_plugin import complete_scd_matching_workflow; print('Import OK')\""
}

main() {
    log_info "=== Building $PROJECT_NAME Python wheels ==="

    # Check prerequisites
    check_command "maturin" "Install with: pip install maturin" || exit 1
    check_command "rustc" "Install Rust from: https://rustup.rs/" || exit 1
    check_rust_version

    # Setup environment
    setup_python_env

    # Create output directory
    mkdir -p "$WHEEL_OUTPUT_DIR"
    rm -f "$WHEEL_OUTPUT_DIR"/*.whl # Clean previous builds

    # Build for different platforms
    local failed_builds=()
    local successful_wheels=()

    # Build wheels for all defined targets
    for target_name in "${!BUILD_TARGETS[@]}"; do
        local target_triple="${BUILD_TARGETS[$target_name]}"
        local display_name=""

        # Set display names
        case "$target_name" in
        "linux") display_name="Linux" ;;
        "windows") display_name="Windows" ;;
        "macos") display_name="macOS" ;;
        "macos-universal") display_name="macOS Universal" ;;
        *) display_name="$target_name" ;;
        esac

        # Platform-specific logic
        case "$target_name" in
        "windows")
            if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "win32" ]]; then
                log_info "Cross-compiling Windows wheel..."
            fi
            ;;
        "macos" | "macos-universal")
            if [[ "$OSTYPE" != "darwin"* ]]; then
                log_warning "Skipping $display_name build (not on macOS)"
                continue
            fi
            ;;
        esac

        # Build the wheel
        if build_wheel "$target_triple" "$display_name"; then
            successful_wheels+=("$display_name")
        else
            failed_builds+=("$display_name")
        fi
    done

    # Test the first successful wheel
    if [[ ${#successful_wheels[@]} -gt 0 ]]; then
        local first_wheel=$(find "$WHEEL_OUTPUT_DIR" -name "*.whl" | head -1)
        if [[ -f "$first_wheel" ]]; then
            test_wheel "$first_wheel"
        fi
    fi

    # Report results
    if [[ ${#successful_wheels[@]} -eq 0 ]]; then
        log_error "All builds failed: ${failed_builds[*]}"
        exit 1
    fi

    if [[ ${#failed_builds[@]} -gt 0 ]]; then
        log_warning "Some builds failed: ${failed_builds[*]}"
        log_success "Successful builds: ${successful_wheels[*]}"
    else
        log_success "All wheel builds completed successfully!"
        log_success "Built wheels for: ${successful_wheels[*]}"
    fi

    show_build_summary
}

# Execute main function
main "$@"
