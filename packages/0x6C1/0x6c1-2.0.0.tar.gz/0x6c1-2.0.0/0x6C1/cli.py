#!/usr/bin/env python3
"""
0x6C1 - Command Line Interface for Hex Translator
"""

import argparse
import binascii
import struct
import sys
from pathlib import Path

def hex_to_text(hex_string):
    """
    Convert a hexadecimal string to readable text.
    
    Args:
        hex_string (str): A string containing hexadecimal characters (0-9, A-F, a-f)
        
    Returns:
        str: The decoded text string
        
    Raises:
        ValueError: If the hex string is invalid or cannot be decoded
    """
    try:
        # Remove any spaces or non-hex characters
        hex_string = ''.join(c for c in hex_string if c in '0123456789ABCDEFabcdef')
        
        # Check if we have a valid hex string
        if len(hex_string) == 0:
            raise ValueError("Empty hex string")
        if len(hex_string) % 2 != 0:
            raise ValueError("Invalid hex string length (must be even number of characters)")
            
        # Convert hex to bytes and then decode to string
        text = bytes.fromhex(hex_string).decode('utf-8')
        return text
    except (ValueError, binascii.Error, UnicodeDecodeError) as e:
        raise ValueError(f"Hex to text conversion failed: {str(e)}")

def text_to_hex(text_string):
    """
    Convert a text string to its hexadecimal representation.
    
    Args:
        text_string (str): Any text string to convert to hex
        
    Returns:
        str: The hexadecimal representation of the input string
        
    Raises:
        ValueError: If the text cannot be encoded to bytes
    """
    try:
        # Encode text to bytes and then convert to hex
        hex_string = text_string.encode('utf-8').hex()
        return hex_string
    except UnicodeEncodeError as e:
        raise ValueError(f"Text to hex conversion failed: {str(e)}")

def number_to_hex(number, float_bits=64):
    """
    Convert a number to its hexadecimal representation.
    
    Args:
        number (str or int or float): The number to convert
        float_bits (int): Bit size for floating-point conversion (32 or 64)
        
    Returns:
        str: Hexadecimal representation of the number
        
    Raises:
        ValueError: If the number is invalid or cannot be converted
    """
    try:
        # Handle both integers and strings that represent numbers
        if isinstance(number, str):
            # Check if it's a float
            if '.' in number:
                num = float(number)
                # Convert float to hex using IEEE 754 representation
                if float_bits == 32:
                    hex_rep = struct.pack('>f', num).hex()
                else:  # 64-bit by default
                    hex_rep = struct.pack('>d', num).hex()
                return hex_rep
            else:
                num = int(number)
        else:
            num = int(number)
            
        # Format as hex with "0x" prefix
        return hex(num)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Number to hex conversion failed: {str(e)}")

def hex_to_number(hex_string, is_float=False):
    """
    Convert a hexadecimal string to a number.
    
    Args:
        hex_string (str): Hexadecimal string to convert
        is_float (bool): Whether to interpret as floating-point number
        
    Returns:
        int or float: The converted number
        
    Raises:
        ValueError: If the hex string is invalid or cannot be converted
    """
    try:
        # Remove any spaces or non-hex characters
        hex_string = ''.join(c for c in hex_string if c in '0123456789ABCDEFabcdef')
        
        if is_float:
            # Convert hex to float
            if len(hex_string) < 8:  # Minimum for float (32-bit)
                hex_string = hex_string.ljust(8, '0')
            elif len(hex_string) > 16:  # Maximum for double (64-bit)
                hex_string = hex_string[:16]
            elif len(hex_string) > 8 and len(hex_string) < 16:
                hex_string = hex_string.ljust(16, '0')
                
            # Determine appropriate format
            if len(hex_string) <= 8:
                byte_data = bytes.fromhex(hex_string.ljust(8, '0'))
                return struct.unpack('>f', byte_data)[0]
            else:
                byte_data = bytes.fromhex(hex_string.ljust(16, '0'))
                return struct.unpack('>d', byte_data)[0]
        else:
            # Convert to integer
            return int(hex_string, 16)
    except (ValueError, struct.error) as e:
        raise ValueError(f"Hex to number conversion failed: {str(e)}")

def format_hex(hex_string, group_size=2, prefix=""):
    """
    Format a hexadecimal string for better readability.
    
    Args:
        hex_string (str): The hex string to format
        group_size (int): Number of characters in each group
        prefix (str): Prefix to add to each group (e.g., "0x")
        
    Returns:
        str: Formatted hex string with spaces between groups
    """
    # Remove any existing spaces and prefix if present
    hex_string = hex_string.replace(' ', '').replace('0x', '')
    
    # Group the hex characters
    grouped = [hex_string[i:i+group_size] for i in range(0, len(hex_string), group_size)]
    
    # Add prefix to each group if specified
    if prefix:
        grouped = [prefix + group for group in grouped]
    
    return ' '.join(grouped)

def process_file(input_file, output_file, operation, **kwargs):
    """
    Process a file with the specified operation.
    
    Args:
        input_file (str): Path to the input file
        output_file (str): Path to the output file
        operation (function): The conversion function to apply
        **kwargs: Additional arguments to pass to the operation
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Apply operation
        result = operation(content, **kwargs)
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(str(result))
        
        return True
    except Exception as e:
        print(f"File processing error: {str(e)}", file=sys.stderr)
        return False

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="0x6C1 - Hex Translator",
        epilog="""
Examples:
  0x6C1 --hex "48656c6c6f"                    # Convert hex to text
  0x6C1 --text "Hello World"                  # Convert text to hex
  0x6C1 --numhex 255                         # Convert number to hex
  0x6C1 --hexnum "ff"                         # Convert hex to integer
  0x6C1 --hexfloat "40091eb851eb851f"         # Convert hex to float
  0x6C1 --file input.txt --output output.txt --hex  # Process files
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add mutually exclusive group for conversion types
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--hex', '-x', type=str, help='Convert hex string to text')
    group.add_argument('--text', '-t', type=str, help='Convert text to hex string')
    group.add_argument('--numhex', '-n', type=str, help='Convert number to hex string')
    group.add_argument('--hexnum', '-i', type=str, help='Convert hex string to integer')
    group.add_argument('--hexfloat', '-f', type=str, help='Convert hex string to float')
    
    # Add file options
    parser.add_argument('--file', type=str, help='Input file for conversion')
    parser.add_argument('--output', type=str, help='Output file for results')
    
    # Add formatting options
    parser.add_argument('--group-size', '-g', type=int, default=2, 
                       help='Group size for formatting hex output (default: 2)')
    parser.add_argument('--prefix', '-p', type=str, default="", 
                       help='Prefix for hex groups (e.g., "0x")')
    parser.add_argument('--float-bits', '-b', type=int, choices=[32, 64], default=64,
                       help='Bit size for floating-point conversion (32 or 64, default: 64)')
    
    args = parser.parse_args()
    
    try:
        # Handle file operations
        if args.file:
            if not args.output:
                print("Error: Output file required when using --file", file=sys.stderr)
                sys.exit(1)
                
            input_path = Path(args.file)
            if not input_path.exists():
                print(f"Error: Input file '{args.file}' does not exist", file=sys.stderr)
                sys.exit(1)
                
            # Determine operation based on arguments
            if args.hex:
                success = process_file(args.file, args.output, hex_to_text)
            elif args.text:
                success = process_file(args.file, args.output, text_to_hex)
            elif args.numhex:
                success = process_file(args.file, args.output, number_to_hex, float_bits=args.float_bits)
            elif args.hexnum:
                success = process_file(args.file, args.output, lambda x: hex_to_number(x, False))
            elif args.hexfloat:
                success = process_file(args.file, args.output, lambda x: hex_to_number(x, True))
                
            if success:
                print(f"Successfully processed {args.file} -> {args.output}")
            else:
                sys.exit(1)
                
        else:
            # Handle direct conversions
            if args.hex:
                result = hex_to_text(args.hex)
                print(result)
            elif args.text:
                hex_result = text_to_hex(args.text)
                formatted_hex = format_hex(hex_result, args.group_size, args.prefix)
                print(formatted_hex)
            elif args.numhex:
                hex_result = number_to_hex(args.numhex, args.float_bits)
                formatted_hex = format_hex(hex_result, args.group_size, args.prefix)
                print(formatted_hex)
            elif args.hexnum:
                result = hex_to_number(args.hexnum, False)
                print(result)
            elif args.hexfloat:
                result = hex_to_number(args.hexfloat, True)
                print(result)
                
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
