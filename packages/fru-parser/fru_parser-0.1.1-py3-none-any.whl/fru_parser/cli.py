
#!/usr/bin/env python3
"""
Command-line interface for the FRU Parser.

This module provides a command-line interface for parsing IPMI FRU binary files
and extracting hardware information into JSON format.
"""

import logging
import sys
import argparse
import os
from pathlib import Path
from typing import Optional

from .parser import parse_fru, FRUParseError, FRUChecksumError, FRUInvalidValueError, FRUFormatError, FRUStringDecodeError


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """
    Set up logging configuration.
    
    Args:
        verbose: Enable debug logging
        quiet: Disable all logging except errors
    """
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
        
    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def validate_input_file(file_path: str) -> None:
    """
    Validate that the input file exists and is readable.
    
    Args:
        file_path: Path to the input file
        
    Raises:
        SystemExit: If the file is invalid
    """
    if not os.path.exists(file_path):
        logging.error(f"Input file does not exist: {file_path}")
        sys.exit(1)
        
    if not os.path.isfile(file_path):
        logging.error(f"Input path is not a file: {file_path}")
        sys.exit(1)
        
    if not os.access(file_path, os.R_OK):
        logging.error(f"Input file is not readable: {file_path}")
        sys.exit(1)
        
    # Check file size
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        logging.error(f"Input file is empty: {file_path}")
        sys.exit(1)
        
    if file_size < 8:
        logging.error(f"Input file is too small to be a valid FRU file (minimum 8 bytes): {file_path}")
        sys.exit(1)


def validate_output_path(output_path: str) -> None:
    """
    Validate that the output path is writable.
    
    Args:
        output_path: Path to the output file
        
    Raises:
        SystemExit: If the output path is invalid
    """
    output_dir = os.path.dirname(output_path)
    
    # If output_dir is empty, it means output_path is just a filename in current directory
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"Created output directory: {output_dir}")
        except OSError as e:
            logging.error(f"Cannot create output directory {output_dir}: {e}")
            sys.exit(1)
    
    # Check if we can write to the output location
    if os.path.exists(output_path):
        if not os.access(output_path, os.W_OK):
            logging.error(f"Output file exists but is not writable: {output_path}")
            sys.exit(1)
    else:
        # Try to create the file to test write permissions
        try:
            with open(output_path, 'w') as f:
                pass
            os.remove(output_path)  # Remove the test file
        except OSError as e:
            logging.error(f"Cannot write to output file {output_path}: {e}")
            sys.exit(1)


def handle_parse_error(error: Exception) -> None:
    """
    Handle FRU parsing errors with appropriate logging and exit codes.
    
    Args:
        error: The exception that occurred during parsing
    """
    if isinstance(error, FRUChecksumError):
        logging.error(f"Checksum validation failed: {error}")
        sys.exit(2)
    elif isinstance(error, FRUInvalidValueError):
        logging.error(f"Invalid value in FRU data: {error}")
        sys.exit(3)
    elif isinstance(error, FRUFormatError):
        logging.error(f"Invalid FRU file format: {error}")
        sys.exit(4)
    elif isinstance(error, FRUStringDecodeError):
        logging.error(f"String decoding error: {error}")
        sys.exit(5)
    elif isinstance(error, FRUParseError):
        logging.error(f"FRU parsing error: {error}")
        sys.exit(6)
    else:
        logging.error(f"Unexpected error: {error}")
        sys.exit(7)


def main() -> None:
    """
    Main entry point for the FRU parser CLI.
    
    Parses command-line arguments, validates input/output files,
    and processes the FRU binary file.
    """
    parser = argparse.ArgumentParser(
        description="Parse IPMI FRU (Field Replaceable Unit) binary files and extract hardware information",
        epilog="""
Examples:
  %(prog)s --fru-bin system.fru --output system.json
  %(prog)s --fru-bin /path/to/fru.bin --output /path/to/output.json --verbose
  %(prog)s --fru-bin fru.bin --quiet
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--fru-bin",
        default="fru.bin",
        help="Path to the input FRU binary file (default: fru.bin)"
    )
    
    parser.add_argument(
        "--output",
        default="fru.json",
        help="Path to the output JSON file (default: fru.json)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output (debug level logging)"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress all output except errors"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(verbose=args.verbose, quiet=args.quiet)
    
    # Validate input file
    validate_input_file(args.fru_bin)
    
    # Validate output path
    validate_output_path(args.output)
    
    # Parse the FRU file
    try:
        logging.info(f"Parsing FRU file: {args.fru_bin}")
        fru_data = parse_fru(args.fru_bin, args.output)
        
        # Log summary information
        if not args.quiet:
            areas_found = []
            if "internal" in fru_data:
                areas_found.append("Internal Use")
            if "chassis" in fru_data:
                areas_found.append("Chassis Info")
            if "board" in fru_data:
                areas_found.append("Board Info")
            if "product" in fru_data:
                areas_found.append("Product Info")
            if "multirecord" in fru_data:
                areas_found.append("Multi-Record")
                
            logging.info(f"Successfully parsed FRU file with areas: {', '.join(areas_found)}")
            logging.info(f"Output saved to: {args.output}")
            
    except Exception as e:
        handle_parse_error(e)