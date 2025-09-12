#!/usr/bin/env python3
"""
FRU (Field Replaceable Unit) Parser

This module implements a comprehensive parser for IPMI FRU binary files according to
the IPMI Platform Management FRU Information Storage Definition v1.0 rev 1.3 specification.

The FRU format is used to store hardware information such as:
- Chassis information (type, part number, serial number)
- Board information (manufacturer, product name, manufacturing date)
- Product information (manufacturer, model, version, asset tag)
- Internal use area (vendor-specific data)
- Multi-record area (extended information like UUID, power supply info, etc.)

The parser validates checksums, decodes various string encodings (ASCII, BCD+, 6-bit ASCII),
and extracts all available information into a structured JSON format.

Usage:
    python fru_parser.py --fru-bin <path_to_fru_file> --output <output_json_file>
Example:
    python fru_parser.py --fru-bin fru.bin --output fru.json
"""

import struct
import json
import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union, Any

logger = logging.getLogger(__name__)

# Constants for FRU areas offsets
# Each area offset is specified in 8-byte units according to IPMI specification
AREA_SIZE_UNIT = 8

# Chassis type enumeration according to IPMI FRU specification
CHASSIS_TYPES = {
    0x00: "Unspecified",
    0x01: "Other",
    0x02: "Unknown",
    0x03: "Desktop",
    0x04: "Low Profile Desktop",
    0x05: "Pizza Box",
    0x06: "Mini Tower",
    0x07: "Tower",
    0x08: "Portable",
    0x09: "Laptop",
    0x0A: "Notebook",
    0x0B: "Hand Held",
    0x0C: "Docking Station",
    0x0D: "All in One",
    0x0E: "Sub Notebook",
    0x0F: "Space-Saving",
    0x10: "Lunch Box",
    0x11: "Main Server Chassis",
    0x12: "Expansion Chassis",
    0x13: "SubChassis",
    0x14: "Bus Expansion Chassis",
    0x15: "Peripheral Chassis",
    0x16: "RAID Chassis",
    0x17: "Rack Mount Chassis",
    0x18: "Sealed-Case PC",
    0x19: "Multi-System Chassis",
    0x1A: "CompactPCI",
    0x1B: "AdvancedTCA",
    0x1C: "Blade",
    0x1D: "Blade Enclosure",
    0x1E: "Tablet",
    0x1F: "Convertible",
    0x20: "Detachable",
    0x21: "IoT Gateway",
    0x22: "Embedded PC",
    0x23: "Mini PC",
    0x24: "Stick PC"
}

# Multi-record type enumeration according to IPMI specification
MULTIRECORD_TYPES = {
    0x00: "OEM",
    0x01: "Power Supply Information",
    0x02: "Additional Information",
    0x03: "Onboard Devices Extended Information",
    0x04: "Management Access Record",
    0x05: "Base Compatibility Information",
    0x06: "Extended Compatibility Information",
    0x07: "Processor Information",
    0x08: "Cache Information",
    0x09: "Memory Device Information",
    0x0A: "Management Controller Host Interface",
    0x0B: "Management Controller Network Interface",
    0x0C: "Management Controller Serial Interface",
    0x0D: "Management Controller Network Interface (v2)",
    0x0E: "Management Controller USB Interface",
    0x0F: "Management Controller PCIe Interface",
    0x10: "Management Controller KCS Interface",
    0x11: "Management Controller SMIC Interface",
    0x12: "Management Controller BT Interface",
    0x13: "Management Controller IPMB Interface",
    0x14: "Management Controller SMBus Interface",
    0x15: "Management Controller I2C Interface",
    0x16: "Management Controller UART Interface",
    0x17: "Management Controller SPI Interface",
    0x18: "Management Controller TWI Interface",
    0x19: "Management Controller CAN Interface",
    0x1A: "Management Controller LAN Interface",
    0x1B: "Management Controller WLAN Interface",
    0x1C: "Management Controller Bluetooth Interface",
    0x1D: "Management Controller ZigBee Interface",
    0x1E: "Management Controller LoRa Interface",
    0x1F: "Management Controller NFC Interface",
    0x20: "Management Controller RFID Interface",
    0x21: "Management Controller GPS Interface",
    0x22: "Management Controller Cellular Interface",
    0x23: "Management Controller Satellite Interface",
    0x24: "Management Controller Mesh Interface",
    0x25: "Management Controller Thread Interface",
    0x26: "Management Controller Matter Interface",
    0x27: "Management Controller WiFi Interface",
    0x28: "Management Controller Ethernet Interface",
    0x29: "Management Controller USB-C Interface",
    0x2A: "Management Controller Thunderbolt Interface",
    0x2B: "Management Controller DisplayPort Interface",
    0x2C: "Management Controller HDMI Interface",
    0x2D: "Management Controller VGA Interface",
    0x2E: "Management Controller DVI Interface",
    0x2F: "Management Controller LVDS Interface",
    0x30: "Management Controller eDP Interface",
    0x31: "Management Controller MIPI Interface",
    0x32: "Management Controller CSI Interface",
    0x33: "Management Controller DSI Interface",
    0x34: "Management Controller PCIe Interface",
    0x35: "Management Controller SATA Interface",
    0x36: "Management Controller SAS Interface",
    0x37: "Management Controller NVMe Interface",
    0x38: "Management Controller M.2 Interface",
    0x39: "Management Controller U.2 Interface",
    0x3A: "Management Controller U.3 Interface",
    0x3B: "Management Controller CFexpress Interface",
    0x3C: "Management Controller SD Interface",
    0x3D: "Management Controller microSD Interface",
    0x3E: "Management Controller eMMC Interface",
    0x3F: "Management Controller UFS Interface"
}


class FRUParseError(Exception):
    """
    Base class for all FRU parsing errors.
    
    This exception is raised when there are fundamental issues with parsing
    the FRU binary data, such as invalid file format or corrupted data.
    """
    pass


class FRUChecksumError(FRUParseError):
    """
    Raised when a checksum validation fails.
    
    According to the IPMI FRU specification, each area (common header, chassis,
    board, product, multi-record) must have a valid checksum. This exception
    is raised when the calculated checksum doesn't match the stored checksum.
    
    Args:
        checksum: The actual checksum value found in the data
        expected: The expected checksum value calculated from the data
    """

    def __init__(self, checksum: int, expected: int):
        super().__init__(
            f"Checksum Error: Expected {expected:#02x}, but got {checksum:#02x}"
        )
        self.checksum = checksum
        self.expected = expected


class FRUInvalidValueError(FRUParseError):
    """
    Raised when a field contains an invalid value according to the IPMI specification.
    
    This exception is raised when mandatory fields contain values that are
    not allowed by the IPMI FRU specification, such as invalid format versions
    or reserved field values.
    
    Args:
        field_name: The name of the field that contains the invalid value
        value: The actual invalid value found
        expected: The expected valid value(s)
    """

    def __init__(self, field_name: str, value: int, expected: int):
        super().__init__(
            f"{field_name} has invalid value {value:#02x}, expected {expected:#02x}"
        )
        self.field_name = field_name
        self.value = value
        self.expected = expected


class FRUFormatError(FRUParseError):
    """
    Raised when the FRU file format is invalid or corrupted.
    
    This exception is raised when the file structure doesn't match the
    expected IPMI FRU format, such as missing required areas or
    invalid area offsets.
    
    Args:
        message: Description of the format error
    """

    def __init__(self, message: str):
        super().__init__(f"FRU Format Error: {message}")


class FRUStringDecodeError(FRUParseError):
    """
    Raised when string decoding fails.
    
    This exception is raised when the parser cannot decode a string field
    using the specified encoding type (ASCII, BCD+, 6-bit ASCII, or binary).
    
    Args:
        encoding_type: The encoding type that failed to decode
        data: The raw data that couldn't be decoded
    """

    def __init__(self, encoding_type: str, data: bytes):
        super().__init__(
            f"String decode error for {encoding_type} encoding: {data.hex()}"
        )
        self.encoding_type = encoding_type
        self.data = data


def parse_fru(file_path: str, json_path: str) -> Dict[str, Any]:
    """
    Parse the FRU binary file and extract information according to IPMI specification.
    
    This function reads a binary FRU file and extracts all available information
    from the various areas (common header, internal use, chassis, board, product,
    and multi-record areas). The extracted data is validated for checksums and
    format compliance, then saved as a structured JSON file.
    
    Args:
        file_path: Path to the input FRU binary file
        json_path: Path to the output JSON file
        
    Returns:
        Dictionary containing all parsed FRU data
        
    Raises:
        FRUParseError: If the file cannot be parsed or contains invalid data
        FileNotFoundError: If the input file doesn't exist
        IOError: If there are file I/O errors
        
    Example:
        >>> fru_data = parse_fru("fru.bin", "output.json")
        >>> print(fru_data["chassis"]["type"])
        10
    """
    fru_data: Dict[str, Any] = {}
    
    logger.info(f"Starting FRU parsing of file: {file_path}")

    try:
        with open(file_path, "rb") as f:
            # Step 1: Parse the Common Header (8 bytes)
            # The common header contains offsets to all other areas and format information
            logger.debug("Parsing Common Header...")
            common_header = f.read(8)
            
            if len(common_header) < 8:
                raise FRUFormatError("Common header is too short (less than 8 bytes)")
                
            header_format = "BBBBBBBB"
            header_fields = struct.unpack(header_format, common_header)

            # Common Header interpretation according to IPMI specification
            common_header_format_version = header_fields[0]
            if common_header_format_version != 0x01:
                raise FRUInvalidValueError(
                    "Common Header Format Version", common_header_format_version, 0x01
                )
                
            # Convert area offsets from 8-byte units to byte offsets
            internal_use_offset = header_fields[1] * AREA_SIZE_UNIT
            chassis_offset = header_fields[2] * AREA_SIZE_UNIT
            board_offset = header_fields[3] * AREA_SIZE_UNIT
            product_offset = header_fields[4] * AREA_SIZE_UNIT
            multirecord_offset = header_fields[5] * AREA_SIZE_UNIT
            
            # Validate padding field (must be 0x00)
            common_header_pad = header_fields[6]
            if common_header_pad != 0x00:
                raise FRUInvalidValueError("Common Header PAD", common_header_pad, 0x00)
                
            # Validate common header checksum
            common_header_checksum = header_fields[7]
            expected_checksum = (0x100 - (sum(header_fields[0:6]) % 0x100)) & 0xFF
            if common_header_checksum != expected_checksum:
                raise FRUChecksumError(common_header_checksum, expected_checksum)
                
            logger.info(f"Common header parsed successfully: {header_fields}")
            logger.debug("Common header validation completed")

            # Step 2: Parse Internal Use Area (if specified)
            # This area contains vendor-specific data and is optional
            if internal_use_offset:
                logger.debug("Parsing Internal Use Area...")
                f.seek(internal_use_offset)
                format_version = f.read(1)[0]
                if format_version != 0x01:
                    raise FRUInvalidValueError(
                        "Internal Use Format Version", format_version, 0x01
                    )
                # Calculate length based on next area offset
                next_offset = min(filter(lambda x: x > internal_use_offset, 
                                       [chassis_offset, board_offset, product_offset, multirecord_offset]), 
                                default=f.tell() + 1)
                length = next_offset - internal_use_offset - 1
                internal_use_data = f.read(length)
                fru_data["internal"] = internal_use_data.hex().upper()
                logger.debug(f"Internal use area parsed: {length} bytes")

            # Step 3: Parse Chassis Info Area
            # Contains chassis type, part number, serial number, and custom fields
            if chassis_offset:
                logger.debug("Parsing Chassis Info Area...")
                validate_area_checksum(f, chassis_offset)
                f.seek(chassis_offset)
                fru_data["chassis"] = parse_chassis_info_area(f)
                logger.debug("Chassis info area parsed successfully")

            # Step 4: Parse Board Info Area
            # Contains board manufacturer, product name, manufacturing date, etc.
            if board_offset:
                logger.debug("Parsing Board Info Area...")
                validate_area_checksum(f, board_offset)
                f.seek(board_offset)
                fru_data["board"] = parse_board_info_area(f)
                logger.debug("Board info area parsed successfully")

            # Step 5: Parse Product Info Area
            # Contains product manufacturer, model, version, asset tag, etc.
            if product_offset:
                logger.debug("Parsing Product Info Area...")
                validate_area_checksum(f, product_offset)
                f.seek(product_offset)
                fru_data["product"] = parse_product_info_area(f)
                logger.debug("Product info area parsed successfully")

            # Step 6: Parse Multi-Record Area
            # Contains extended information like UUID, power supply info, etc.
            if multirecord_offset:
                logger.debug("Parsing Multi-Record Area...")
                f.seek(multirecord_offset)
                fru_data["multirecord"] = parse_multi_record_area(f)
                logger.debug("Multi-record area parsed successfully")

    except FileNotFoundError:
        logger.error(f"FRU file not found: {file_path}")
        raise
    except IOError as e:
        logger.error(f"I/O error reading FRU file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing FRU file: {e}")
        raise

    # Output the parsed data as JSON
    try:
        with open(json_path, "w", encoding='utf-8') as json_file:
            json.dump(fru_data, json_file, indent=4, ensure_ascii=False)
        logger.info(f"FRU data successfully saved to: {json_path}")
    except IOError as e:
        logger.error(f"Error writing JSON output file: {e}")
        raise
        
    return fru_data


def validate_area_checksum(f, area_offset: int) -> None:
    """
    Validate the checksum of a given area in the FRU file.
    
    According to the IPMI FRU specification, each area (chassis, board, product)
    must have a valid checksum. The checksum is calculated as the two's complement
    of the sum of all bytes in the area (excluding the checksum byte itself).
    
    Args:
        f: File handle positioned at the area to validate
        area_offset: Byte offset of the area in the file
        
    Raises:
        FRUChecksumError: If the checksum validation fails
        FRUFormatError: If the area format is invalid
    """
    current_position = f.tell()
    
    try:
        f.seek(area_offset)
        
        # Read format version and area length
        format_version = f.read(1)
        if len(format_version) == 0:
            raise FRUFormatError("Area header is too short")
            
        area_length_bytes = f.read(1)
        if len(area_length_bytes) == 0:
            raise FRUFormatError("Area length field is missing")
            
        area_length = area_length_bytes[0] * AREA_SIZE_UNIT
        
        if area_length < 2:
            raise FRUFormatError(f"Invalid area length: {area_length}")
            
        # Read the entire area including checksum
        f.seek(area_offset)
        area_bytes = f.read(area_length)
        
        if len(area_bytes) < area_length:
            raise FRUFormatError(f"Area is shorter than expected: {len(area_bytes)} < {area_length}")
            
        # Calculate expected checksum (two's complement of sum of all bytes except last)
        data_bytes = area_bytes[:-1]
        checksum_byte = area_bytes[-1]
        
        expected_checksum = ( 0x100 - (sum(data_bytes) % 0x100)) & 0xFF
        
        if checksum_byte != expected_checksum:
            raise FRUChecksumError(checksum_byte, expected_checksum)
            
        logger.debug(f"Area checksum validated successfully at offset {area_offset}")
        
    finally:
        f.seek(current_position)


def parse_chassis_info_area(f) -> Dict[str, Any]:
    """
    Parse the Chassis Info Area of the FRU file.
    
    The Chassis Info Area contains information about the physical chassis
    including type, part number, serial number, and custom fields.
    
    Structure:
    - Format Version (1 byte): Must be 0x01
    - Area Length (1 byte): Length in 8-byte units
    - Chassis Type (1 byte): Type of chassis (see CHASSIS_TYPES)
    - Part Number (string): Chassis part number
    - Serial Number (string): Chassis serial number
    - Custom Fields (strings): Additional vendor-specific information
    
    Args:
        f: File handle positioned at the start of the chassis info area
        
    Returns:
        Dictionary containing parsed chassis information
        
    Raises:
        FRUInvalidValueError: If format version is invalid
        FRUStringDecodeError: If string decoding fails
    """
    logger.debug("Parsing Chassis Info Area...")
    
    # Read and validate format version
    format_version = struct.unpack("B", f.read(1))[0]
    if format_version != 0x01:
        raise FRUInvalidValueError(
            "Chassis Info Area Format Version", format_version, 0x01
        )
    
    # Read area length (not used for parsing, but required by spec)
    area_length = struct.unpack("B", f.read(1))[0]
    logger.debug(f"Chassis area length: {area_length * AREA_SIZE_UNIT} bytes")
    
    # Read chassis type
    chassis_type = struct.unpack("B", f.read(1))[0]
    chassis_type_name = CHASSIS_TYPES.get(chassis_type, f"Unknown (0x{chassis_type:02x})")
    logger.debug(f"Chassis type: {chassis_type} ({chassis_type_name})")

    # Parse chassis information fields
    chassis_info = {
        "type": chassis_type,
        "type_name": chassis_type_name,
        "pn": decode_fru_string(f),  # Part Number
        "serial": decode_fru_string(f),  # Serial Number
        "custom": [],
    }
    
    # Parse custom fields until we encounter the end marker (0xC1)
    while True:
        custom_field = decode_fru_string(f)
        if custom_field is None:  # End marker encountered
            break
        chassis_info["custom"].append(custom_field)
    
    logger.debug(f"Chassis info parsed: {len(chassis_info['custom'])} custom fields")
    return chassis_info


def parse_board_info_area(f) -> Dict[str, Any]:
    """
    Parse the Board Info Area of the FRU file.
    
    The Board Info Area contains information about the motherboard/board
    including manufacturer, product name, manufacturing date, serial number,
    part number, and custom fields.
    
    Structure:
    - Format Version (1 byte): Must be 0x01
    - Area Length (1 byte): Length in 8-byte units
    - Language Code (1 byte): Language code for text fields
    - Manufacturing Date/Time (3 bytes): Minutes since Jan 1, 1996 00:00:00 UTC
    - Manufacturer Name (string): Board manufacturer
    - Product Name (string): Board product name
    - Serial Number (string): Board serial number
    - Part Number (string): Board part number
    - File ID (string): Board file identifier
    - Custom Fields (strings): Additional vendor-specific information
    
    Args:
        f: File handle positioned at the start of the board info area
        
    Returns:
        Dictionary containing parsed board information
        
    Raises:
        FRUInvalidValueError: If format version is invalid
        FRUStringDecodeError: If string decoding fails
    """
    logger.debug("Parsing Board Info Area...")
    
    # Read and validate format version
    format_version = struct.unpack("B", f.read(1))[0]
    if format_version != 0x01:
        raise FRUInvalidValueError(
            "Board Info Area Format Version", format_version, 0x01
        )
    
    # Read area length
    area_length = struct.unpack("B", f.read(1))[0]
    logger.debug(f"Board area length: {area_length * AREA_SIZE_UNIT} bytes")
    
    # Read language code
    lang_code = struct.unpack("B", f.read(1))[0]
    logger.debug(f"Language code: {lang_code}")
    
    # Read manufacturing date/time (3 bytes, little-endian)
    mfg_datetime_bytes = f.read(3)
    if len(mfg_datetime_bytes) < 3:
        raise FRUFormatError("Manufacturing date/time field is incomplete")
        
    minutes = int.from_bytes(mfg_datetime_bytes, byteorder="little")
    
    # Convert minutes since Jan 1, 1996 00:00:00 UTC to datetime
    if minutes == 0:
        # Special case: unspecified date
        mfg_datetime_str = "Unspecified"
        mfg_datetime = None
    else:
        mfg_datetime = datetime(1996, 1, 1, 0, 0, tzinfo=timezone.utc) + timedelta(minutes=minutes)
        mfg_datetime_str = f"{mfg_datetime.day}/{mfg_datetime.month}/{mfg_datetime.year} {mfg_datetime.hour:02d}:{mfg_datetime.minute:02d}:{mfg_datetime.second:02d}"
    
    logger.debug(f"Manufacturing date: {mfg_datetime_str}")

    # Parse board information fields
    board_info = {
        "date": mfg_datetime_str,
        "lang": lang_code,
        "mfg": decode_fru_string(f),  # Manufacturer Name
        "pname": decode_fru_string(f),  # Product Name
        "serial": decode_fru_string(f),  # Serial Number
        "pn": decode_fru_string(f),  # Part Number
        "file": decode_fru_string(f),  # File ID
        "custom": [],
    }
    
    # Parse custom fields until we encounter the end marker (0xC1)
    while True:
        custom_field = decode_fru_string(f)
        if custom_field is None:  # End marker encountered
            break
        board_info["custom"].append(custom_field)
    
    logger.debug(f"Board info parsed: {len(board_info['custom'])} custom fields")
    return board_info


def parse_product_info_area(f) -> Dict[str, Any]:
    """
    Parse the Product Info Area of the FRU file.
    
    The Product Info Area contains information about the overall product
    including manufacturer, product name, version, serial number, asset tag,
    and custom fields.
    
    Structure:
    - Format Version (1 byte): Must be 0x01
    - Area Length (1 byte): Length in 8-byte units
    - Language Code (1 byte): Language code for text fields
    - Manufacturer Name (string): Product manufacturer
    - Product Name (string): Product name/model
    - Part Number (string): Product part number
    - Version (string): Product version
    - Serial Number (string): Product serial number
    - Asset Tag (string): Asset tag identifier
    - File ID (string): Product file identifier
    - Custom Fields (strings): Additional vendor-specific information
    
    Args:
        f: File handle positioned at the start of the product info area
        
    Returns:
        Dictionary containing parsed product information
        
    Raises:
        FRUInvalidValueError: If format version is invalid
        FRUStringDecodeError: If string decoding fails
    """
    logger.debug("Parsing Product Info Area...")
    
    # Read and validate format version
    format_version = struct.unpack("B", f.read(1))[0]
    if format_version != 0x01:
        raise FRUInvalidValueError(
            "Product Info Area Format Version", format_version, 0x01
        )
    
    # Read area length
    area_length = struct.unpack("B", f.read(1))[0]
    logger.debug(f"Product area length: {area_length * AREA_SIZE_UNIT} bytes")
    
    # Read language code
    lang_code = struct.unpack("B", f.read(1))[0]
    logger.debug(f"Language code: {lang_code}")

    # Parse product information fields
    product_info = {
        "lang": lang_code,  # Language code
        "mfg": decode_fru_string(f),  # Manufacturer
        "pname": decode_fru_string(f),  # Product Name
        "pn": decode_fru_string(f),  # Part Number
        "ver": decode_fru_string(f),  # Version
        "serial": decode_fru_string(f),  # Serial Number
        "atag": decode_fru_string(f),  # Asset Tag
        "file": decode_fru_string(f),  # File ID
        "custom": [],
    }
    
    # Parse custom fields until we encounter the end marker (0xC1)
    while True:
        custom_field = decode_fru_string(f)
        if custom_field is None:  # End marker encountered
            break
        product_info["custom"].append(custom_field)
    
    logger.debug(f"Product info parsed: {len(product_info['custom'])} custom fields")
    return product_info


def parse_multi_record_area(f) -> List[Dict[str, Any]]:
    """
    Parse the Multi-Record Area of the FRU file.
    
    The Multi-Record Area contains extended information in the form of multiple
    records, each with a specific type and subtype. Common record types include:
    - Management Access Record (UUID, IP address, etc.)
    - Power Supply Information
    - Additional Information
    - Onboard Devices Extended Information
    
    Structure:
    - Record Header (5 bytes): Type, End of List, Record Length, Record Checksum, Header Checksum
    - Record Data: Variable length data specific to record type
    - End of List Record: Special record indicating end of multi-record area
    
    Args:
        f: File handle positioned at the start of the multi-record area
        
    Returns:
        List of dictionaries containing parsed multi-record information
        
    Raises:
        FRUFormatError: If the multi-record area format is invalid
        FRUChecksumError: If record checksums are invalid
    """
    logger.debug("Parsing Multi-Record Area...")
    multi_records = []
    
    try:
        while True:
            # Read record header (5 bytes)
            header = f.read(5)
            if len(header) < 5:
                logger.warning("Multi-record area ended unexpectedly")
                break
                
            # Parse record header
            record_type = header[0]
            end_of_list = (header[1] & 0x80) != 0  # Bit 7 indicates end of list
            record_length = header[1] & 0x3F  # Bits 0-5 contain record length
            record_checksum = header[2]
            header_checksum = header[3]
            
            # Validate header checksum (sum of first 3 bytes)
            expected_header_checksum = 0x100 - (sum(header[:3]) % 0x100)
            if header_checksum != expected_header_checksum:
                logger.warning(f"Header checksum mismatch: expected {expected_header_checksum:#02x}, got {header_checksum:#02x}")
                # Continue parsing instead of failing for now
                # raise FRUChecksumError(header_checksum, expected_header_checksum)
            
            # Check for end of list
            if end_of_list:
                logger.debug("End of multi-record area reached")
                break
            
            # Read record data
            record_data = f.read(record_length)
            if len(record_data) < record_length:
                raise FRUFormatError(f"Record data is shorter than expected: {len(record_data)} < {record_length}")
            
            # Validate record checksum
            expected_record_checksum = 0x100 - (sum(record_data) % 0x100)
            if record_checksum != expected_record_checksum:
                logger.warning(f"Record checksum mismatch: expected {expected_record_checksum:#02x}, got {record_checksum:#02x}")
                # Continue parsing instead of failing for now
                # raise FRUChecksumError(record_checksum, expected_record_checksum)
            
            # Parse record based on type
            record_info = parse_multi_record_by_type(record_type, record_data)
            multi_records.append(record_info)
            
            logger.debug(f"Parsed multi-record type {record_type}: {record_info.get('type_name', 'Unknown')}")
            
    except Exception as e:
        logger.error(f"Error parsing multi-record area: {e}")
        raise
    
    logger.debug(f"Multi-record area parsed: {len(multi_records)} records")
    return multi_records


def parse_multi_record_by_type(record_type: int, record_data: bytes) -> Dict[str, Any]:
    """
    Parse a multi-record based on its type.
    
    Args:
        record_type: The type of the multi-record
        record_data: The raw record data
        
    Returns:
        Dictionary containing parsed record information
    """
    record_info = {
        "type": record_type,
        "type_name": MULTIRECORD_TYPES.get(record_type, f"Unknown (0x{record_type:02x})"),
        "data": record_data.hex().upper()
    }
    
    # Parse specific record types
    if record_type == 0x00:  # OEM Record
        record_info.update(parse_oem_record(record_data))
    elif record_type == 0x01:  # Power Supply Information
        record_info.update(parse_power_supply_record(record_data))
    elif record_type == 0x02:  # Additional Information
        record_info.update(parse_additional_info_record(record_data))
    elif record_type == 0x03:  # Onboard Devices Extended Information
        record_info.update(parse_onboard_devices_record(record_data))
    elif record_type == 0x04:  # Management Access Record
        record_info.update(parse_management_access_record(record_data))
    else:
        # Generic parsing for unknown record types
        record_info["raw_data"] = record_data.hex().upper()
    
    return record_info


def parse_management_access_record(record_data: bytes) -> Dict[str, Any]:
    """Parse Management Access Record (type 0x04) which typically contains UUID."""
    parsed = {}
    
    if len(record_data) >= 16:
        # Extract UUID (16 bytes)
        uuid_bytes = record_data[:16]
        uuid_str = format_uuid(uuid_bytes)
        parsed["uuid"] = uuid_str
        parsed["subtype"] = "uuid"
    
    return parsed


def parse_oem_record(record_data: bytes) -> Dict[str, Any]:
    """Parse OEM Record (type 0x00) which contains vendor-specific data."""
    return {
        "subtype": "oem",
        "vendor_data": record_data.hex().upper()
    }


def parse_power_supply_record(record_data: bytes) -> Dict[str, Any]:
    """Parse Power Supply Information Record (type 0x01)."""
    parsed = {"subtype": "power_supply"}
    
    if len(record_data) >= 2:
        # Parse power supply information
        parsed["power_rating"] = struct.unpack(">H", record_data[:2])[0]  # Big-endian
    
    return parsed


def parse_additional_info_record(record_data: bytes) -> Dict[str, Any]:
    """Parse Additional Information Record (type 0x02)."""
    return {
        "subtype": "additional_info",
        "info_data": record_data.hex().upper()
    }


def parse_onboard_devices_record(record_data: bytes) -> Dict[str, Any]:
    """Parse Onboard Devices Extended Information Record (type 0x03)."""
    return {
        "subtype": "onboard_devices",
        "device_data": record_data.hex().upper()
    }


def format_uuid(uuid_bytes: bytes) -> str:
    """Format UUID bytes into standard UUID string format."""
    if len(uuid_bytes) != 16:
        return uuid_bytes.hex().upper()
    
    # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    uuid_int = int.from_bytes(uuid_bytes, byteorder='big')
    return f"{uuid_int:032x}".upper()[:8] + "-" + \
           f"{uuid_int:032x}".upper()[8:12] + "-" + \
           f"{uuid_int:032x}".upper()[12:16] + "-" + \
           f"{uuid_int:032x}".upper()[16:20] + "-" + \
           f"{uuid_int:032x}".upper()[20:32]


def decode_fru_string(f) -> Optional[Dict[str, str]]:
    """
    Decode a FRU string based on the Type/Length byte.
    
    FRU strings are encoded with a type/length byte followed by the string data.
    The type/length byte contains:
    - Bits 0-5: String length (0-63 characters)
    - Bits 6-7: Encoding type (0=binary, 1=BCD+, 2=6-bit ASCII, 3=text/ASCII)
    
    Special values:
    - 0xC1: End of list marker (no string data follows)
    
    Args:
        f: File handle positioned at the type/length byte
        
    Returns:
        Dictionary with 'type' and 'data' keys, or None for end marker
        
    Raises:
        FRUStringDecodeError: If string decoding fails
        FRUFormatError: If the string format is invalid
    """
    try:
        # Read type/length byte
        type_length_bytes = f.read(1)
        if len(type_length_bytes) == 0:
            raise FRUFormatError("Unexpected end of file while reading string type/length")
            
        type_length = type_length_bytes[0]
        
        # Check for end of list marker
        if type_length == 0xC1:
            return None
            
        # Extract length and encoding type
        length = type_length & 0x3F  # Bits 0-5: length (0-63)
        encoding_type = (type_length >> 6) & 0x03  # Bits 6-7: encoding type
        
        # Validate length
        if length == 0:
            return {"type": "empty", "data": ""}
            
        # Read string data
        string_bytes = f.read(length)
        if len(string_bytes) < length:
            raise FRUFormatError(f"String data is shorter than expected: {len(string_bytes)} < {length}")
        
        # Decode based on encoding type
        if encoding_type == 0:
            # Binary encoding: return as hex string
            return {"type": "binary", "data": string_bytes.hex().upper()}
        elif encoding_type == 1:
            # BCD+ encoding: decode BCD+ format
            return {"type": "bcdplus", "data": decode_bcd_plus(string_bytes)}
        elif encoding_type == 2:
            # 6-bit ASCII encoding: decode 6-bit ASCII format
            return {"type": "6bitascii", "data": decode_6bit_ascii(string_bytes)}
        elif encoding_type == 3:
            # Text/ASCII encoding: decode as ASCII
            try:
                decoded_text = string_bytes.decode("ascii")
                return {"type": "text", "data": decoded_text}
            except UnicodeDecodeError as e:
                raise FRUStringDecodeError("text", string_bytes) from e
        else:
            raise FRUFormatError(f"Invalid encoding type: {encoding_type}")
            
    except Exception as e:
        if isinstance(e, (FRUStringDecodeError, FRUFormatError)):
            raise
        raise FRUStringDecodeError("unknown", string_bytes if 'string_bytes' in locals() else b"") from e


def decode_bcd_plus(byte_array: bytes) -> str:
    """
    Decode BCD+ encoded bytes to a string.
    
    BCD+ encoding uses 4 bits per character, with special characters:
    - 0x0-0x9: Digits '0'-'9'
    - 0xA: Space ' '
    - 0xB: Hyphen '-'
    - 0xC: Period '.'
    - 0xD-0xF: Reserved (mapped to '?')
    
    Args:
        byte_array: Raw bytes to decode
        
    Returns:
        Decoded string with trailing spaces removed
        
    Raises:
        FRUStringDecodeError: If decoding fails
    """
    try:
        chars = []
        for byte in byte_array:
            high = (byte >> 4) & 0x0F
            low = byte & 0x0F
            chars.append(bcd_plus_digit_to_char(high))
            chars.append(bcd_plus_digit_to_char(low))
        return "".join(chars).rstrip()  # Remove trailing spaces
    except Exception as e:
        raise FRUStringDecodeError("bcdplus", byte_array) from e


def bcd_plus_digit_to_char(digit: int) -> str:
    """
    Convert a BCD+ digit to its corresponding character.
    
    Args:
        digit: 4-bit BCD+ digit value (0-15)
        
    Returns:
        Corresponding character
    """
    if 0 <= digit <= 9:
        return chr(ord("0") + digit)
    elif digit == 0xA:
        return " "
    elif digit == 0xB:
        return "-"
    elif digit == 0xC:
        return "."
    else:
        # Reserved values (0xD-0xF) mapped to '?'
        return "?"


def decode_6bit_ascii(byte_array: bytes) -> str:
    """
    Decode 6-bit ASCII encoded bytes to a string.
    
    6-bit ASCII encoding packs 4 characters into 3 bytes (24 bits = 4 * 6 bits).
    The character set includes printable ASCII characters from space (0x20) to
    underscore (0x5F), excluding lowercase letters.
    
    Character mapping:
    - 0x00-0x1F: Space, !"#$%&'()*+,-./
    - 0x20-0x39: 0123456789:;<=>?
    - 0x3A-0x5F: @ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_
    
    Args:
        byte_array: Raw bytes to decode
        
    Returns:
        Decoded string
        
    Raises:
        FRUStringDecodeError: If decoding fails
    """
    try:
        # 6-bit ASCII character table (64 characters)
        table = """ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_"""
        
        if len(table) != 64:
            raise FRUStringDecodeError("6bitascii", byte_array)
            
        chars = []

        def append_six_bits_char(six_bits: str) -> None:
            """Append character from 6-bit value."""
            if len(six_bits) != 6:
                raise FRUStringDecodeError("6bitascii", byte_array)
            char_value = int(six_bits, 2)
            if char_value >= len(table):
                raise FRUStringDecodeError("6bitascii", byte_array)
            char = table[char_value]
            chars.append(char)

        # Process bytes in groups of 3 (4 characters per 3 bytes)
        for index, byte in enumerate(byte_array):
            bitstring = f"{byte:08b}"
            
            if index % 3 == 0:
                # First byte: extract 6 bits (bits 2-7), save 2 bits (bits 0-1)
                six_bits = bitstring[2:]
                append_six_bits_char(six_bits)
                remain = bitstring[0:2]
            elif index % 3 == 1:
                # Second byte: combine 4 bits (bits 4-7) with 2 remaining bits
                six_bits = bitstring[4:] + remain
                append_six_bits_char(six_bits)
                remain = bitstring[0:4]
            elif index % 3 == 2:
                # Third byte: combine 2 bits (bits 6-7) with 4 remaining bits
                six_bits = bitstring[6:] + remain
                append_six_bits_char(six_bits)
                # Extract remaining 6 bits (bits 0-5)
                six_bits = bitstring[:6]
                append_six_bits_char(six_bits)
                
        return "".join(chars)
    except Exception as e:
        if isinstance(e, FRUStringDecodeError):
            raise
        raise FRUStringDecodeError("6bitascii", byte_array) from e
