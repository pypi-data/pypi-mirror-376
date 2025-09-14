"""
Xml2GUI - A powerful framework for creating GUI applications using XML files

This framework allows you to create beautiful desktop applications using simple XML files,
without writing complex Python code. It supports both PyQt5 and PyQt-Fluent-Widgets UI libraries.

Features:
- Zero programming experience required
- Intuitive XML syntax
- Automatic Python code generation
- One-click compilation to EXE
- Rich widget support
- Modern interface design
- Simplified event handling
"""

__version__ = "1.0.0"
__author__ = "huang1057"
__license__ = "GPL-3.0"

from .parser import XmlParser
from .generator import PythonGenerator
from .compiler import Compiler

__all__ = ["XmlParser", "PythonGenerator", "Compiler"]