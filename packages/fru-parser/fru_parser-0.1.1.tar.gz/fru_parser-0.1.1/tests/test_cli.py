#!/usr/bin/env python3
"""
Test suite for the FRU Parser CLI.

This module contains tests for the command-line interface functionality.
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import patch, mock_open
from io import StringIO

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fru_parser.cli import (
    setup_logging, validate_input_file, validate_output_path,
    handle_parse_error, main
)
from fru_parser.parser import (
    FRUParseError, FRUChecksumError, FRUInvalidValueError, 
    FRUFormatError, FRUStringDecodeError
)


class TestCLILogging(unittest.TestCase):
    """Test cases for CLI logging functionality."""
    
    def test_setup_logging_verbose(self):
        """Test verbose logging setup."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(verbose=True, quiet=False)
            mock_basic_config.assert_called_once()
            # Check that DEBUG level was used
            call_args = mock_basic_config.call_args
            self.assertEqual(call_args[1]['level'], 10)  # DEBUG level
    
    def test_setup_logging_quiet(self):
        """Test quiet logging setup."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(verbose=False, quiet=True)
            mock_basic_config.assert_called_once()
            # Check that ERROR level was used
            call_args = mock_basic_config.call_args
            self.assertEqual(call_args[1]['level'], 40)  # ERROR level
    
    def test_setup_logging_normal(self):
        """Test normal logging setup."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(verbose=False, quiet=False)
            mock_basic_config.assert_called_once()
            # Check that INFO level was used
            call_args = mock_basic_config.call_args
            self.assertEqual(call_args[1]['level'], 20)  # INFO level


class TestCLIValidation(unittest.TestCase):
    """Test cases for CLI validation functions."""
    
    def test_validate_input_file_exists(self):
        """Test input file validation with existing file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b'test data')
            temp_file.flush()
            
            try:
                # This should not raise an exception
                validate_input_file(temp_file.name)
            finally:
                os.unlink(temp_file.name)
    
    def test_validate_input_file_not_exists(self):
        """Test input file validation with non-existent file."""
        with self.assertRaises(SystemExit) as cm:
            validate_input_file('/nonexistent/file')
        self.assertEqual(cm.exception.code, 1)
    
    def test_validate_input_file_empty(self):
        """Test input file validation with empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Empty file
            temp_file.flush()
            
            try:
                with self.assertRaises(SystemExit) as cm:
                    validate_input_file(temp_file.name)
                self.assertEqual(cm.exception.code, 1)
            finally:
                os.unlink(temp_file.name)
    
    def test_validate_input_file_too_small(self):
        """Test input file validation with file too small."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b'123')  # Only 3 bytes, less than minimum 8
            temp_file.flush()
            
            try:
                with self.assertRaises(SystemExit) as cm:
                    validate_input_file(temp_file.name)
                self.assertEqual(cm.exception.code, 1)
            finally:
                os.unlink(temp_file.name)
    
    def test_validate_output_path(self):
        """Test output path validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'output.json')
            # This should not raise an exception
            validate_output_path(output_path)
    
    def test_validate_output_path_create_dir(self):
        """Test output path validation with directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'subdir', 'output.json')
            # This should create the subdirectory and not raise an exception
            validate_output_path(output_path)
            self.assertTrue(os.path.exists(os.path.dirname(output_path)))


class TestCLIErrorHandling(unittest.TestCase):
    """Test cases for CLI error handling."""
    
    def test_handle_checksum_error(self):
        """Test handling of checksum errors."""
        with self.assertRaises(SystemExit) as cm:
            handle_parse_error(FRUChecksumError(0x00, 0xFF))
        self.assertEqual(cm.exception.code, 2)
    
    def test_handle_invalid_value_error(self):
        """Test handling of invalid value errors."""
        with self.assertRaises(SystemExit) as cm:
            handle_parse_error(FRUInvalidValueError("test", 0x00, 0x01))
        self.assertEqual(cm.exception.code, 3)
    
    def test_handle_format_error(self):
        """Test handling of format errors."""
        with self.assertRaises(SystemExit) as cm:
            handle_parse_error(FRUFormatError("test error"))
        self.assertEqual(cm.exception.code, 4)
    
    def test_handle_string_decode_error(self):
        """Test handling of string decode errors."""
        with self.assertRaises(SystemExit) as cm:
            handle_parse_error(FRUStringDecodeError("test", b"data"))
        self.assertEqual(cm.exception.code, 5)
    
    def test_handle_generic_parse_error(self):
        """Test handling of generic parse errors."""
        with self.assertRaises(SystemExit) as cm:
            handle_parse_error(FRUParseError("test error"))
        self.assertEqual(cm.exception.code, 6)
    
    def test_handle_unexpected_error(self):
        """Test handling of unexpected errors."""
        with self.assertRaises(SystemExit) as cm:
            handle_parse_error(ValueError("unexpected error"))
        self.assertEqual(cm.exception.code, 7)


class TestCLIMain(unittest.TestCase):
    """Test cases for CLI main function."""
    
    def test_main_help(self):
        """Test CLI help output."""
        with patch('sys.argv', ['fru-parser', '--help']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
    
    def test_main_version(self):
        """Test CLI version output."""
        with patch('sys.argv', ['fru-parser', '--version']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
    
    def test_main_invalid_file(self):
        """Test CLI with invalid input file."""
        with patch('sys.argv', ['fru-parser', '--fru-bin', '/nonexistent/file']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 1)
    
    def test_main_success(self):
        """Test CLI with successful parsing."""
        # Create a minimal valid FRU file
        fru_data = b'\x01\x00\x00\x00\x00\x00\x00\x00'  # Minimal common header
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(fru_data)
            temp_file.flush()
            
            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as json_file:
                    json_path = json_file.name
                
                with patch('sys.argv', ['fru-parser', '--fru-bin', temp_file.name, '--output', json_path]):
                    with patch('fru_parser.cli.parse_fru') as mock_parse:
                        mock_parse.return_value = {"test": "data"}
                        main()
                        mock_parse.assert_called_once_with(temp_file.name, json_path)
                
            finally:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                if os.path.exists(json_path):
                    os.unlink(json_path)


if __name__ == '__main__':
    unittest.main()
