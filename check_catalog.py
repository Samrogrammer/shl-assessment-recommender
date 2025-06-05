#!/usr/bin/env python3
"""
Debug script to check catalog file location and content
"""
import os
import json

def debug_catalog():
    print("=== SHL Catalog Debug ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {os.path.abspath(__file__)}")
    
    # Check different possible locations
    possible_paths = [
        "app/data/shl_catalogue.json",
        "data/shl_catalogue.json", 
        "shl_catalogue.json",
        "./app/data/shl_catalogue.json",
        "../data/shl_catalogue.json",
    ]
    
    print("\n=== Checking possible paths ===")
    found_files = []
    
    for path in possible_paths:
        full_path = os.path.abspath(path)
        exists = os.path.exists(path)
        print(f"Path: {path}")
        print(f"  Full path: {full_path}")
        print(f"  Exists: {exists}")
        
        if exists:
            found_files.append(path)
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                print(f"  Records: {len(data)}")
                if data:
                    print(f"  First record keys: {list(data[0].keys())}")
            except Exception as e:
                print(f"  Error reading: {e}")
        print()
    
    print(f"=== Found files: {found_files} ===")
    
    # List all files in common directories
    print("\n=== Directory listings ===")
    for dir_path in [".", "app", "data", "app/data"]:
        if os.path.exists(dir_path):
            print(f"\nContents of {dir_path}:")
            try:
                files = os.listdir(dir_path)
                for file in files:
                    file_path = os.path.join(dir_path, file)
                    if os.path.isfile(file_path):
                        print(f"  FILE: {file}")
                    else:
                        print(f"  DIR:  {file}/")
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == "__main__":
    debug_catalog()