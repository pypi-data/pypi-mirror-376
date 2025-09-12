#!/bin/bash

# Simple 5-Minute Stability Test
# Tests only arithmetic operations for 5 minutes

set -e

echo ""
echo "============================================================"
echo "Simple 5-Minute Stability Test"
echo "============================================================"
echo "Testing arithmetic operations continuously for 5 minutes"
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

# Create simple test script
cat > simple_stability.py << 'EOF'
#!/usr/bin/env python3
"""
Simple 5-minute stability test focusing on arithmetic operations.
"""

import asyncio
import time
import random
from calculator.services.arithmetic import ArithmeticService
from calculator.core.config.loader import ConfigLoader

async def main():
    """Main stability test function."""
    print("🚀 Starting simple 5-minute stability test...")
    
    # Initialize service
    config_loader = ConfigLoader()
    config = config_loader.load_config()
    arithmetic_service = ArithmeticService(config)
    
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
        
        try:
            # Test basic arithmetic operations
            numbers = [random.uniform(1, 100), random.uniform(1, 100)]
            
            # Addition
            result = await arithmetic_service.process("add", {"numbers": numbers})
            total_operations += 1
            
            # Multiplication  
            result = await arithmetic_service.process("multiply", {"numbers": numbers})
            total_operations += 1
            
            # Power
            result = await arithmetic_service.process("power", {"base": numbers[0], "exponent": 2})
            total_operations += 1
            
            # Square root
            result = await arithmetic_service.process("sqrt", {"number": abs(numbers[0])})
            total_operations += 1
            
        except Exception as e:
            total_errors += 1
            if total_errors <= 5:  # Only print first 5 errors
                print(f"Error in cycle {cycle}: {e}")
        
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
        
        # Small delay
        await asyncio.sleep(0.01)
    
    # Final report
    total_time = time.time() - start_time
    ops_per_sec = total_operations / total_time
    error_rate = (total_errors / total_operations * 100) if total_operations > 0 else 0
    
    print("\n" + "="*60)
    print("📊 SIMPLE STABILITY TEST RESULTS")
    print("="*60)
    print(f"⏱️  Total Duration: {total_time:.1f} seconds")
    print(f"🔄 Total Cycles: {cycle}")
    print(f"⚡ Total Operations: {total_operations}")
    print(f"❌ Total Errors: {total_errors}")
    print(f"📈 Operations/Second: {ops_per_sec:.1f}")
    print(f"📉 Error Rate: {error_rate:.2f}%")
    
    if error_rate < 5.0:
        print("✅ STABILITY TEST PASSED - Error rate acceptable")
        return 0
    else:
        print("❌ STABILITY TEST FAILED - High error rate")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
EOF

echo "📋 Running simple 5-minute stability test..."
echo "ℹ️  This will test arithmetic operations continuously for 5 minutes"
echo "ℹ️  Press Ctrl+C to stop early if needed"
echo ""

# Run the stability test
python simple_stability.py

# Cleanup
rm -f simple_stability.py

echo ""
echo "============================================================"
echo "✅ Simple stability test completed!"
echo "============================================================"