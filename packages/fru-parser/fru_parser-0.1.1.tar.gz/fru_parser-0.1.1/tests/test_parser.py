#!/usr/bin/env python3
"""
Test suite for the FRU Parser.

This module contains comprehensive tests for the FRU parser functionality,
including unit tests for individual functions and integration tests for
complete FRU file parsing.
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, mock_open
from io import BytesIO

from src.fru_parser.parser import (
    parse_fru, validate_area_checksum, parse_chassis_info_area,
    parse_board_info_area, parse_product_info_area, parse_multi_record_area,
    decode_fru_string, decode_bcd_plus, decode_6bit_ascii, bcd_plus_digit_to_char,
    format_uuid, CHASSIS_TYPES, MULTIRECORD_TYPES,
    FRUParseError, FRUChecksumError, FRUInvalidValueError, FRUFormatError, FRUStringDecodeError
)


class TestFRUStringDecoding(unittest.TestCase):
    """Test cases for FRU string decoding functions."""
    
    def test_bcd_plus_digit_to_char(self):
        """Test BCD+ digit to character conversion."""
        self.assertEqual(bcd_plus_digit_to_char(0), '0')
        self.assertEqual(bcd_plus_digit_to_char(9), '9')
        self.assertEqual(bcd_plus_digit_to_char(0xA), ' ')
        self.assertEqual(bcd_plus_digit_to_char(0xB), '-')
        self.assertEqual(bcd_plus_digit_to_char(0xC), '.')
        self.assertEqual(bcd_plus_digit_to_char(0xD), '?')
        self.assertEqual(bcd_plus_digit_to_char(0xF), '?')
    
    def test_decode_bcd_plus(self):
        """Test BCD+ string decoding."""
        # Test normal digits
        self.assertEqual(decode_bcd_plus(b'\x12\x34'), '1234')
        # Test with spaces and special characters
        self.assertEqual(decode_bcd_plus(b'\x1A\x2B\x3C'), '1 -2.3')
        # Test empty string
        self.assertEqual(decode_bcd_plus(b''), '')
        # Test reserved values
        self.assertEqual(decode_bcd_plus(b'\x1D\x2E'), '1?2?')
    
    def test_decode_6bit_ascii(self):
        """Test 6-bit ASCII string decoding."""
        # Test basic characters
        self.assertEqual(decode_6bit_ascii(b'\x20\x20'), '  ')
        # Test numbers
        self.assertEqual(decode_6bit_ascii(b'\x30\x31'), '01')
        # Test uppercase letters
        self.assertEqual(decode_6bit_ascii(b'\x41\x42'), 'AB')
        # Test empty string
        self.assertEqual(decode_6bit_ascii(b''), '')
    
    def test_decode_fru_string(self):
        """Test FRU string decoding with different encodings."""
        # Test end marker
        f = BytesIO(b'\xC1')
        result = decode_fru_string(f)
        self.assertIsNone(result)
        
        # Test empty string
        f = BytesIO(b'\x00')
        result = decode_fru_string(f)
        self.assertEqual(result, {"type": "empty", "data": ""})
        
        # Test text encoding
        f = BytesIO(b'\x03Hello')
        result = decode_fru_string(f)
        self.assertEqual(result, {"type": "text", "data": "Hello"})
        
        # Test binary encoding
        f = BytesIO(b'\x02\xAB\xCD')
        result = decode_fru_string(f)
        self.assertEqual(result, {"type": "binary", "data": "ABCD"})
        
        # Test BCD+ encoding
        f = BytesIO(b'\x02\x12\x34')
        result = decode_fru_string(f)
        self.assertEqual(result, {"type": "bcdplus", "data": "1234"})


class TestFRUValidation(unittest.TestCase):
    """Test cases for FRU validation functions."""
    
    def test_validate_area_checksum_valid(self):
        """Test checksum validation with valid data."""
        # Create valid area data: format_version=1, length=1, data=0x00, checksum=0xFF
        area_data = b'\x01\x01\x00\xFF'
        f = BytesIO(area_data)
        # This should not raise an exception
        validate_area_checksum(f, 0)
    
    def test_validate_area_checksum_invalid(self):
        """Test checksum validation with invalid data."""
        # Create invalid area data with wrong checksum
        area_data = b'\x01\x01\x00\x00'  # Wrong checksum
        f = BytesIO(area_data)
        with self.assertRaises(FRUChecksumError):
            validate_area_checksum(f, 0)
    
    def test_validate_area_checksum_short_data(self):
        """Test checksum validation with insufficient data."""
        area_data = b'\x01'  # Too short
        f = BytesIO(area_data)
        with self.assertRaises(FRUFormatError):
            validate_area_checksum(f, 0)


class TestFRUAreaParsing(unittest.TestCase):
    """Test cases for FRU area parsing functions."""
    
    def test_parse_chassis_info_area(self):
        """Test chassis info area parsing."""
        # Create valid chassis area data
        chassis_data = b'\x01\x02\x0A'  # format_version=1, length=2, type=10 (Notebook)
        chassis_data += b'\x03ABC'  # Part number: text "ABC"
        chassis_data += b'\x03XYZ'  # Serial number: text "XYZ"
        chassis_data += b'\xC1'  # End marker
        
        f = BytesIO(chassis_data)
        result = parse_chassis_info_area(f)
        
        self.assertEqual(result["type"], 10)
        self.assertEqual(result["type_name"], "Notebook")
        self.assertEqual(result["pn"]["data"], "ABC")
        self.assertEqual(result["serial"]["data"], "XYZ")
        self.assertEqual(len(result["custom"]), 0)
    
    def test_parse_board_info_area(self):
        """Test board info area parsing."""
        # Create valid board area data
        board_data = b'\x01\x04\x01'  # format_version=1, length=4, lang_code=1
        board_data += b'\x00\x00\x00'  # Manufacturing date: 0 (unspecified)
        board_data += b'\x05Intel'  # Manufacturer: text "Intel"
        board_data += b'\x08Mainboard'  # Product name: text "Mainboard"
        board_data += b'\x03SN123'  # Serial number: text "SN123"
        board_data += b'\x03PN456'  # Part number: text "PN456"
        board_data += b'\x03FILE'  # File ID: text "FILE"
        board_data += b'\xC1'  # End marker
        
        f = BytesIO(board_data)
        result = parse_board_info_area(f)
        
        self.assertEqual(result["date"], "Unspecified")
        self.assertEqual(result["lang"], 1)
        self.assertEqual(result["mfg"]["data"], "Intel")
        self.assertEqual(result["pname"]["data"], "Mainboard")
        self.assertEqual(result["serial"]["data"], "SN123")
        self.assertEqual(result["pn"]["data"], "PN456")
        self.assertEqual(result["file"]["data"], "FILE")
    
    def test_parse_product_info_area(self):
        """Test product info area parsing."""
        # Create valid product area data
        product_data = b'\x01\x03\x01'  # format_version=1, length=3, lang_code=1
        product_data += b'\x05Dell'  # Manufacturer: text "Dell"
        product_data += b'\x08OptiPlex'  # Product name: text "OptiPlex"
        product_data += b'\x03PN789'  # Part number: text "PN789"
        product_data += b'\x03v1.0'  # Version: text "v1.0"
        product_data += b'\x03SN999'  # Serial number: text "SN999"
        product_data += b'\x05Asset1'  # Asset tag: text "Asset1"
        product_data += b'\x03FILE'  # File ID: text "FILE"
        product_data += b'\xC1'  # End marker
        
        f = BytesIO(product_data)
        result = parse_product_info_area(f)
        
        self.assertEqual(result["lang"], 1)
        self.assertEqual(result["mfg"]["data"], "Dell")
        self.assertEqual(result["pname"]["data"], "OptiPlex")
        self.assertEqual(result["pn"]["data"], "PN789")
        self.assertEqual(result["ver"]["data"], "v1.0")
        self.assertEqual(result["serial"]["data"], "SN999")
        self.assertEqual(result["atag"]["data"], "Asset1")
        self.assertEqual(result["file"]["data"], "FILE")


class TestMultiRecordParsing(unittest.TestCase):
    """Test cases for multi-record area parsing."""
    
    def test_format_uuid(self):
        """Test UUID formatting."""
        # Test valid UUID bytes
        uuid_bytes = bytes.fromhex('9bd70799ccf04915a7f97ce7d64385cf')
        result = format_uuid(uuid_bytes)
        self.assertEqual(result, '9BD70799-CCF0-4915-A7F9-7CE7D64385CF')
        
        # Test invalid length
        result = format_uuid(b'\x01\x02')
        self.assertEqual(result, '0102')
    
    def test_parse_management_access_record(self):
        """Test management access record parsing."""
        from src.fru_parser.parser import parse_management_access_record
        
        # Test with UUID data
        uuid_data = bytes.fromhex('9bd70799ccf04915a7f97ce7d64385cf')
        result = parse_management_access_record(uuid_data)
        
        self.assertEqual(result["subtype"], "uuid")
        self.assertEqual(result["uuid"], "9BD70799-CCF0-4915-A7F9-7CE7D64385CF")
    
    def test_parse_multi_record_area(self):
        """Test multi-record area parsing."""
        # Create valid multi-record area data
        # Record header: type=4, end_of_list=0, length=16, record_checksum, header_checksum
        record_header = b'\x04\x10'  # type=4, length=16
        record_header += b'\x00'  # record_checksum (will be calculated)
        record_header += b'\x00'  # header_checksum (will be calculated)
        
        # Record data: UUID
        record_data = bytes.fromhex('9bd70799ccf04915a7f97ce7d64385cf')
        
        # Calculate checksums
        record_checksum = 0x100 - (sum(record_data) % 0x100)
        header_checksum = 0x100 - (sum(record_header[:2]) % 0x100)
        
        # Create complete multi-record area
        multi_record_data = record_header[:2] + bytes([record_checksum, header_checksum]) + record_data
        multi_record_data += b'\x00\x00\x00\x00\x00'  # End of list record
        
        f = BytesIO(multi_record_data)
        result = parse_multi_record_area(f)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], 4)
        self.assertEqual(result[0]["type_name"], "Management Access Record")
        self.assertEqual(result[0]["subtype"], "uuid")


class TestFRUIntegration(unittest.TestCase):
    """Integration tests for complete FRU file parsing."""
    
    def create_test_fru_file(self):
        """Create a minimal valid FRU file for testing."""
        # Common header (8 bytes)
        common_header = b'\x01'  # Format version
        common_header += b'\x02'  # Internal use offset (2 * 8 = 16)
        common_header += b'\x03'  # Chassis offset (3 * 8 = 24)
        common_header += b'\x04'  # Board offset (4 * 8 = 32)
        common_header += b'\x05'  # Product offset (5 * 8 = 40)
        common_header += b'\x00'  # Multi-record offset (0 = not present)
        common_header += b'\x00'  # Pad
        common_header += b'\x00'  # Checksum (will be calculated)
        
        # Calculate common header checksum
        checksum = 0x100 - (sum(common_header[:-1]) % 0x100)
        common_header = common_header[:-1] + bytes([checksum])
        
        # Internal use area (at offset 16)
        internal_data = b'\x01\x01\x00\xFF'  # format_version=1, length=1, data=0x00, checksum=0xFF
        
        # Chassis area (at offset 24)
        chassis_data = b'\x01\x02\x0A'  # format_version=1, length=2, type=10
        chassis_data += b'\x03ABC'  # Part number
        chassis_data += b'\x03XYZ'  # Serial number
        chassis_data += b'\xC1'  # End marker
        chassis_data += b'\x00'  # Padding to make length multiple of 8
        chassis_data += b'\x00'  # Checksum (will be calculated)
        
        # Calculate chassis checksum
        chassis_checksum = 0x100 - (sum(chassis_data[:-1]) % 0x100)
        chassis_data = chassis_data[:-1] + bytes([chassis_checksum])
        
        # Board area (at offset 32)
        board_data = b'\x01\x03\x01'  # format_version=1, length=3, lang_code=1
        board_data += b'\x00\x00\x00'  # Manufacturing date
        board_data += b'\x05Intel'  # Manufacturer
        board_data += b'\x08Mainboard'  # Product name
        board_data += b'\x03SN123'  # Serial number
        board_data += b'\x03PN456'  # Part number
        board_data += b'\x03FILE'  # File ID
        board_data += b'\xC1'  # End marker
        board_data += b'\x00'  # Checksum (will be calculated)
        
        # Calculate board checksum
        board_checksum = 0x100 - (sum(board_data[:-1]) % 0x100)
        board_data = board_data[:-1] + bytes([board_checksum])
        
        # Product area (at offset 40)
        product_data = b'\x01\x03\x01'  # format_version=1, length=3, lang_code=1
        product_data += b'\x05Dell'  # Manufacturer
        product_data += b'\x08OptiPlex'  # Product name
        product_data += b'\x03PN789'  # Part number
        product_data += b'\x03v1.0'  # Version
        product_data += b'\x03SN999'  # Serial number
        product_data += b'\x05Asset1'  # Asset tag
        product_data += b'\x03FILE'  # File ID
        product_data += b'\xC1'  # End marker
        product_data += b'\x00'  # Checksum (will be calculated)
        
        # Calculate product checksum
        product_checksum = 0x100 - (sum(product_data[:-1]) % 0x100)
        product_data = product_data[:-1] + bytes([product_checksum])
        
        # Combine all data
        fru_data = common_header
        fru_data += b'\x00' * (16 - len(fru_data))  # Pad to internal use area
        fru_data += internal_data
        fru_data += b'\x00' * (24 - len(fru_data))  # Pad to chassis area
        fru_data += chassis_data
        fru_data += b'\x00' * (32 - len(fru_data))  # Pad to board area
        fru_data += board_data
        fru_data += b'\x00' * (40 - len(fru_data))  # Pad to product area
        fru_data += product_data
        
        return fru_data
    
    def test_parse_fru_complete(self):
        """Test complete FRU file parsing."""
        fru_data = self.create_test_fru_file()
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(fru_data)
            temp_file.flush()
            
            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as json_file:
                    json_path = json_file.name
                
                # Parse the FRU file
                result = parse_fru(temp_file.name, json_path)
                
                # Verify the result
                self.assertIn("internal", result)
                self.assertIn("chassis", result)
                self.assertIn("board", result)
                self.assertIn("product", result)
                
                # Verify chassis info
                self.assertEqual(result["chassis"]["type"], 10)
                self.assertEqual(result["chassis"]["type_name"], "Notebook")
                self.assertEqual(result["chassis"]["pn"]["data"], "ABC")
                self.assertEqual(result["chassis"]["serial"]["data"], "XYZ")
                
                # Verify board info
                self.assertEqual(result["board"]["date"], "Unspecified")
                self.assertEqual(result["board"]["mfg"]["data"], "Intel")
                self.assertEqual(result["board"]["pname"]["data"], "Mainboard")
                
                # Verify product info
                self.assertEqual(result["product"]["mfg"]["data"], "Dell")
                self.assertEqual(result["product"]["pname"]["data"], "OptiPlex")
                
                # Verify JSON file was created
                self.assertTrue(os.path.exists(json_path))
                
                # Verify JSON content
                with open(json_path, 'r') as f:
                    json_data = json.load(f)
                    self.assertEqual(json_data, result)
                
            finally:
                # Clean up temporary files
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                if os.path.exists(json_path):
                    os.unlink(json_path)


class TestFRUErrorHandling(unittest.TestCase):
    """Test cases for FRU error handling."""
    
    def test_invalid_format_version(self):
        """Test handling of invalid format version."""
        with self.assertRaises(FRUInvalidValueError):
            f = BytesIO(b'\x02')  # Invalid format version
            decode_fru_string(f)
    
    def test_checksum_error(self):
        """Test checksum error handling."""
        with self.assertRaises(FRUChecksumError):
            area_data = b'\x01\x01\x00\x00'  # Wrong checksum
            f = BytesIO(area_data)
            validate_area_checksum(f, 0)
    
    def test_format_error(self):
        """Test format error handling."""
        with self.assertRaises(FRUFormatError):
            area_data = b'\x01'  # Too short
            f = BytesIO(area_data)
            validate_area_checksum(f, 0)


if __name__ == '__main__':
    unittest.main()
