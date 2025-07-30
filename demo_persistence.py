#!/usr/bin/env python3
"""Demo persistence across sessions."""

import subprocess
import time

print("🎓 Demo: SAGE Persistence")
print("=" * 50)

# First session
print("\n📝 Session 1: Alice learns about fractions")
print("-" * 30)
proc = subprocess.Popen(['sage', 'learn', '-s', 'alice', '-t', 'fractions'], 
                       stdin=subprocess.PIPE, 
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,
                       text=True)

# Send some inputs
inputs = "Hello\nI struggle with fractions\nexit\n"
stdout, stderr = proc.communicate(input=inputs)
print("Output:", stdout[:200] + "..." if len(stdout) > 200 else stdout)

# Wait a bit
time.sleep(1)

# Second session - should remember Alice
print("\n📝 Session 2: Alice returns")
print("-" * 30)
proc = subprocess.Popen(['sage', 'learn', '-s', 'alice', '-t', 'fractions'], 
                       stdin=subprocess.PIPE, 
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,
                       text=True)

inputs = "Do you remember me?\nexit\n"
stdout, stderr = proc.communicate(input=inputs)
print("Output:", stdout[:200] + "..." if len(stdout) > 200 else stdout)

# Check what was saved
print("\n💾 Checking saved data...")
import os
sage_dir = os.path.expanduser("~/.sage/data")
if os.path.exists(sage_dir):
    for root, dirs, files in os.walk(sage_dir):
        level = root.replace(sage_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files[:5]:  # Show first 5 files
            print(f'{subindent}{file}')