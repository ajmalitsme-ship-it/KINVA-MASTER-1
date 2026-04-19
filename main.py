#!/usr/bin/env python3
import sys
import os
from mx_interpreter import MXLangInterpreter

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <filename.mx>")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found!")
        sys.exit(1)
    
    # Create MX interpreter instance
    mx = MXLangInterpreter()
    
    # Execute MX file
    print(f"\n{'='*50}")
    print(f"Executing MX Language File: {filename}")
    print(f"{'='*50}\n")
    
    success, message = mx.execute_file(filename)
    
    print(f"\n{'='*50}")
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()
