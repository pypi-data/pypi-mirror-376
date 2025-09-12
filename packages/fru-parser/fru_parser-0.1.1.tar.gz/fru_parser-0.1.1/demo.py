#!/usr/bin/env python3
"""
Demonstration script for the FRU Parser.

This script demonstrates the functionality of the FRU parser by parsing
the test FRU file and displaying the results in a readable format.
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fru_parser.parser import parse_fru, CHASSIS_TYPES


def format_datetime(date_str):
    """Format date string for display."""
    if date_str == "Unspecified":
        return "Unspecified"
    try:
        # Parse the date string and reformat it
        parts = date_str.split()
        if len(parts) >= 2:
            date_part = parts[0]
            time_part = parts[1]
            return f"{date_part} at {time_part}"
    except:
        pass
    return date_str


def display_fru_info(fru_data):
    """Display FRU information in a readable format."""
    print("=" * 60)
    print("FRU (Field Replaceable Unit) Information")
    print("=" * 60)
    
    # Internal Use Area
    if "internal" in fru_data:
        print(f"\nInternal Use Area:")
        print(f"  Data: {fru_data['internal']}")
    
    # Chassis Information
    if "chassis" in fru_data:
        chassis = fru_data["chassis"]
        print(f"\nChassis Information:")
        print(f"  Type: {chassis.get('type', 'Unknown')} ({chassis.get('type_name', 'Unknown')})")
        
        if "pn" in chassis and chassis["pn"]:
            pn_data = chassis["pn"]
            if isinstance(pn_data, dict):
                print(f"  Part Number: {pn_data.get('data', 'N/A')} ({pn_data.get('type', 'unknown')} encoding)")
            else:
                print(f"  Part Number: {pn_data}")
        
        if "serial" in chassis and chassis["serial"]:
            serial_data = chassis["serial"]
            if isinstance(serial_data, dict):
                print(f"  Serial Number: {serial_data.get('data', 'N/A')} ({serial_data.get('type', 'unknown')} encoding)")
            else:
                print(f"  Serial Number: {serial_data}")
        
        if "custom" in chassis and chassis["custom"]:
            print(f"  Custom Fields: {len(chassis['custom'])}")
            for i, custom in enumerate(chassis["custom"]):
                if isinstance(custom, dict):
                    print(f"    {i+1}. {custom.get('data', 'N/A')} ({custom.get('type', 'unknown')} encoding)")
                else:
                    print(f"    {i+1}. {custom}")
    
    # Board Information
    if "board" in fru_data:
        board = fru_data["board"]
        print(f"\nBoard Information:")
        
        if "date" in board:
            print(f"  Manufacturing Date: {format_datetime(board['date'])}")
        
        if "lang" in board:
            print(f"  Language Code: {board['lang']}")
        
        if "mfg" in board and board["mfg"]:
            mfg_data = board["mfg"]
            if isinstance(mfg_data, dict):
                print(f"  Manufacturer: {mfg_data.get('data', 'N/A')} ({mfg_data.get('type', 'unknown')} encoding)")
            else:
                print(f"  Manufacturer: {mfg_data}")
        
        if "pname" in board and board["pname"]:
            pname_data = board["pname"]
            if isinstance(pname_data, dict):
                print(f"  Product Name: {pname_data.get('data', 'N/A')} ({pname_data.get('type', 'unknown')} encoding)")
            else:
                print(f"  Product Name: {pname_data}")
        
        if "serial" in board and board["serial"]:
            serial_data = board["serial"]
            if isinstance(serial_data, dict):
                print(f"  Serial Number: {serial_data.get('data', 'N/A')} ({serial_data.get('type', 'unknown')} encoding)")
            else:
                print(f"  Serial Number: {serial_data}")
        
        if "pn" in board and board["pn"]:
            pn_data = board["pn"]
            if isinstance(pn_data, dict):
                print(f"  Part Number: {pn_data.get('data', 'N/A')} ({pn_data.get('type', 'unknown')} encoding)")
            else:
                print(f"  Part Number: {pn_data}")
        
        if "file" in board and board["file"]:
            file_data = board["file"]
            if isinstance(file_data, dict):
                print(f"  File ID: {file_data.get('data', 'N/A')} ({file_data.get('type', 'unknown')} encoding)")
            else:
                print(f"  File ID: {file_data}")
        
        if "custom" in board and board["custom"]:
            print(f"  Custom Fields: {len(board['custom'])}")
            for i, custom in enumerate(board["custom"]):
                if isinstance(custom, dict):
                    print(f"    {i+1}. {custom.get('data', 'N/A')} ({custom.get('type', 'unknown')} encoding)")
                else:
                    print(f"    {i+1}. {custom}")
    
    # Product Information
    if "product" in fru_data:
        product = fru_data["product"]
        print(f"\nProduct Information:")
        
        if "lang" in product:
            print(f"  Language Code: {product['lang']}")
        
        if "mfg" in product and product["mfg"]:
            mfg_data = product["mfg"]
            if isinstance(mfg_data, dict):
                print(f"  Manufacturer: {mfg_data.get('data', 'N/A')} ({mfg_data.get('type', 'unknown')} encoding)")
            else:
                print(f"  Manufacturer: {mfg_data}")
        
        if "pname" in product and product["pname"]:
            pname_data = product["pname"]
            if isinstance(pname_data, dict):
                print(f"  Product Name: {pname_data.get('data', 'N/A')} ({pname_data.get('type', 'unknown')} encoding)")
            else:
                print(f"  Product Name: {pname_data}")
        
        if "pn" in product and product["pn"]:
            pn_data = product["pn"]
            if isinstance(pn_data, dict):
                print(f"  Part Number: {pn_data.get('data', 'N/A')} ({pn_data.get('type', 'unknown')} encoding)")
            else:
                print(f"  Part Number: {pn_data}")
        
        if "ver" in product and product["ver"]:
            ver_data = product["ver"]
            if isinstance(ver_data, dict):
                print(f"  Version: {ver_data.get('data', 'N/A')} ({ver_data.get('type', 'unknown')} encoding)")
            else:
                print(f"  Version: {ver_data}")
        
        if "serial" in product and product["serial"]:
            serial_data = product["serial"]
            if isinstance(serial_data, dict):
                print(f"  Serial Number: {serial_data.get('data', 'N/A')} ({serial_data.get('type', 'unknown')} encoding)")
            else:
                print(f"  Serial Number: {serial_data}")
        
        if "atag" in product and product["atag"]:
            atag_data = product["atag"]
            if isinstance(atag_data, dict):
                print(f"  Asset Tag: {atag_data.get('data', 'N/A')} ({atag_data.get('type', 'unknown')} encoding)")
            else:
                print(f"  Asset Tag: {atag_data}")
        
        if "file" in product and product["file"]:
            file_data = product["file"]
            if isinstance(file_data, dict):
                print(f"  File ID: {file_data.get('data', 'N/A')} ({file_data.get('type', 'unknown')} encoding)")
            else:
                print(f"  File ID: {file_data}")
        
        if "custom" in product and product["custom"]:
            print(f"  Custom Fields: {len(product['custom'])}")
            for i, custom in enumerate(product["custom"]):
                if isinstance(custom, dict):
                    print(f"    {i+1}. {custom.get('data', 'N/A')} ({custom.get('type', 'unknown')} encoding)")
                else:
                    print(f"    {i+1}. {custom}")
    
    # Multi-Record Information
    if "multirecord" in fru_data and fru_data["multirecord"]:
        print(f"\nMulti-Record Information:")
        for i, record in enumerate(fru_data["multirecord"]):
            print(f"  Record {i+1}:")
            print(f"    Type: {record.get('type', 'Unknown')} ({record.get('type_name', 'Unknown')})")
            
            if "subtype" in record:
                print(f"    Subtype: {record['subtype']}")
            
            if "uuid" in record:
                print(f"    UUID: {record['uuid']}")
            
            if "data" in record:
                print(f"    Data: {record['data']}")
    
    print("\n" + "=" * 60)
    print("End of FRU Information")
    print("=" * 60)


def main():
    """Main demonstration function."""
    print("FRU Parser Demonstration")
    print("=" * 40)
    
    # Check if test file exists
    test_file = "tests/fru.bin"
    if not os.path.exists(test_file):
        print(f"Error: Test file '{test_file}' not found!")
        print("Please ensure the test FRU file exists.")
        return 1
    
    try:
        # Parse the FRU file
        print(f"Parsing FRU file: {test_file}")
        fru_data = parse_fru(test_file, "demo_output.json")
        
        # Display the information
        display_fru_info(fru_data)
        
        # Show JSON output info
        print(f"\nJSON output saved to: demo_output.json")
        print(f"JSON file size: {os.path.getsize('demo_output.json')} bytes")
        
        return 0
        
    except Exception as e:
        print(f"Error parsing FRU file: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
