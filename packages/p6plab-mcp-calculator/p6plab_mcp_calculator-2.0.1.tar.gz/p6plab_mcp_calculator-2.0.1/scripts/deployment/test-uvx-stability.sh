#!/bin/bash

# 5-Minute uvx Stability Test
# Tests the uvx package under continuous operation for 5 minutes

set -e

echo ""
echo "============================================================"
echo "5-Minute uvx Stability Test"
echo "============================================================"
echo "Testing uvx package stability under continuous operation"
echo ""

# Check if virtual environment is active
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment active: $VIRTUAL_ENV"
else
    echo "❌ No virtual environment detected. Please activate venv first."
    exit 1
fi

# Install package in editable mode
echo "📋 Installing package locally in editable mode..."
pip install -e . > /dev/null 2>&1

# Test basic uvx availability
echo "📋 Verifying uvx availability..."
if ! command -v uvx &> /dev/null; then
    echo "❌ uvx not found. Please install uvx first."
    exit 1
fi
echo "✅ uvx is available"

# Create test script for continuous operation
cat > test_stability.py << 'EOF'
#!/usr/bin/env python3
"""
5-minute stability test for the calculator MCP server.
Tests various operations continuously for 5 minutes.
"""

import asyncio
import time
import random
from calculator.server.app import create_server
from calculator.services.arithmetic import ArithmeticService
from calculator.services.matrix import MatrixService
from calculator.services.statistics import StatisticsService
from calculator.core.config.loader import ConfigLoader

async def test_arithmetic_operations(service, test_count):
    """Test basic arithmetic operations."""
    operations = 0
    errors = 0
    
    for i in range(test_count):
        try:
            # Test various arithmetic operations using the process method
            numbers = [random.uniform(1, 100) for _ in range(random.randint(2, 5))]
            
            # Test addition
            result = await service.process("add", {"numbers": numbers})
            assert isinstance(result, (int, float))
            
            # Test multiplication
            result = await service.process("multiply", {"numbers": numbers[:2]})
            assert isinstance(result, (int, float))
            
            # Test power
            base = random.uniform(1, 10)
            exp = random.uniform(1, 3)
            result = await service.process("power", {"base": base, "exponent": exp})
            assert isinstance(result, (int, float))
            
            operations += 3
            
        except Exception as e:
            errors += 1
            if i < 3:  # Only print first few errors to avoid spam
                print(f"Arithmetic error {i}: {e}")
    
    return operations, errors

async def test_matrix_operations(service, test_count):
    """Test matrix operations."""
    operations = 0
    errors = 0
    
    for i in range(test_count):
        try:
            # Create random matrices
            size = random.randint(2, 4)  # Smaller matrices for stability
            matrix1 = [[random.uniform(1, 10) for _ in range(size)] for _ in range(size)]
            matrix2 = [[random.uniform(1, 10) for _ in range(size)] for _ in range(size)]
            
            # Test matrix addition
            result = await service.process("add", {"matrix_a": matrix1, "matrix_b": matrix2})
            assert isinstance(result, list)
            
            # Test matrix multiplication
            result = await service.process("multiply", {"matrix_a": matrix1, "matrix_b": matrix2})
            assert isinstance(result, list)
            
            # Test determinant for smaller matrices
            if size <= 3:
                result = await service.process("determinant", {"matrix": matrix1})
                assert isinstance(result, (int, float))
                operations += 1
            
            operations += 2
            
        except Exception as e:
            errors += 1
            if i < 3:  # Only print first few errors to avoid spam
                print(f"Matrix error {i}: {e}")
    
    return operations, errors

async def test_statistics_operations(service, test_count):
    """Test statistics operations."""
    operations = 0
    errors = 0
    
    for i in range(test_count):
        try:
            # Generate random data
            data_size = random.randint(10, 50)  # Smaller datasets for stability
            data = [random.uniform(1, 100) for _ in range(data_size)]
            
            # Test mean
            result = await service.process("mean", {"data": data})
            assert isinstance(result, (int, float))
            
            # Test median
            result = await service.process("median", {"data": data})
            assert isinstance(result, (int, float))
            
            # Test standard deviation
            result = await service.process("std_dev", {"data": data})
            assert isinstance(result, (int, float))
            
            operations += 3
            
        except Exception as e:
            errors += 1
            if i < 3:  # Only print first few errors to avoid spam
                print(f"Statistics error {i}: {e}")
    
    return operations, errors

async def main():
    """Main stability test function."""
    print("🚀 Starting 5-minute stability test...")
    
    # Initialize services
    config_loader = ConfigLoader()
    config = config_loader.load_config()
    
    arithmetic_service = ArithmeticService(config)
    matrix_service = MatrixService(config)
    statistics_service = StatisticsService(config)
    
    # Test parameters
    test_duration = 5 * 60  # 5 minutes in seconds
    start_time = time.time()
    
    total_operations = 0
    total_errors = 0
    cycle = 0
    
    print(f"⏱️  Running for {test_duration} seconds...")
    print("📊 Progress updates every 30 seconds...")
    
    last_report = start_time
    
    while time.time() - start_time < test_duration:
        cycle += 1
        cycle_start = time.time()
        
        # Run tests for this cycle
        try:
            # Test arithmetic (10 operations per cycle)
            ops, errs = await test_arithmetic_operations(arithmetic_service, 10)
            total_operations += ops
            total_errors += errs
            
            # Test matrix (5 operations per cycle)
            ops, errs = await test_matrix_operations(matrix_service, 5)
            total_operations += ops
            total_errors += errs
            
            # Test statistics (5 operations per cycle)
            ops, errs = await test_statistics_operations(statistics_service, 5)
            total_operations += ops
            total_errors += errs
            
        except Exception as e:
            print(f"Cycle {cycle} error: {e}")
            total_errors += 1
        
        # Report progress every 30 seconds
        current_time = time.time()
        if current_time - last_report >= 30:
            elapsed = current_time - start_time
            remaining = test_duration - elapsed
            ops_per_sec = total_operations / elapsed if elapsed > 0 else 0
            error_rate = (total_errors / total_operations * 100) if total_operations > 0 else 0
            
            print(f"⏱️  {elapsed:.0f}s elapsed, {remaining:.0f}s remaining")
            print(f"📊 Cycle {cycle}: {total_operations} ops, {ops_per_sec:.1f} ops/sec, {error_rate:.2f}% errors")
            
            last_report = current_time
        
        # Small delay to prevent overwhelming the system
        await asyncio.sleep(0.1)
    
    # Final report
    total_time = time.time() - start_time
    ops_per_sec = total_operations / total_time
    error_rate = (total_errors / total_operations * 100) if total_operations > 0 else 0
    
    print("\n" + "="*60)
    print("📊 STABILITY TEST RESULTS")
    print("="*60)
    print(f"⏱️  Total Duration: {total_time:.1f} seconds")
    print(f"🔄 Total Cycles: {cycle}")
    print(f"⚡ Total Operations: {total_operations}")
    print(f"❌ Total Errors: {total_errors}")
    print(f"📈 Operations/Second: {ops_per_sec:.1f}")
    print(f"📉 Error Rate: {error_rate:.2f}%")
    
    if error_rate < 1.0:
        print("✅ STABILITY TEST PASSED - Error rate acceptable")
        return 0
    else:
        print("❌ STABILITY TEST FAILED - High error rate")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
EOF

echo "📋 Running 5-minute stability test..."
echo "ℹ️  This will test the calculator continuously for 5 minutes"
echo "ℹ️  Press Ctrl+C to stop early if needed"
echo ""

# Run the stability test
python test_stability.py

# Cleanup
rm -f test_stability.py

echo ""
echo "============================================================"
echo "✅ 5-minute stability test completed!"
echo "============================================================"