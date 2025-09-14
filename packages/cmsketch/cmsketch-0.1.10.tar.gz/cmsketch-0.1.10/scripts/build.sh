#!/bin/bash

# Build script for Count-Min Sketch project

set -e

echo "Building Count-Min Sketch project..."

# Create build directory
mkdir -p build
cd build

# Configure with CMake
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_TESTS=ON \
    -DBUILD_PYTHON_BINDINGS=ON

# Build the project
make -j"$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)"

echo "Build completed successfully!"

# Run tests if available
if [ -f "cmsketch_tests" ]; then
    echo "Running tests..."
    ./cmsketch_tests
fi

# Run example if available
if [ -f "cmsketch_example" ]; then
    echo "Running example..."
    ./cmsketch_example
fi

echo "All done!"
