"""
0x6C1 - Hex Translator Package
==============================

A comprehensive tool for converting between hexadecimal representations
and their corresponding text or numeric values with file support.
"""

from .cli import (
    hex_to_text,
    text_to_hex,
    number_to_hex,
    hex_to_number,
    format_hex,
    process_file
)

__version__ = "1.0.0"
__author__ = "celestine1729"
__email__ = "celestine1729@proton.me"

__all__ = [
    "hex_to_text",
    "text_to_hex",
    "number_to_hex",
    "hex_to_number",
    "format_hex",
    "process_file"
]
