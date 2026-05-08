#!/usr/bin/env python3
"""Aconcagua SPRT Test Tool - Main entry point."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_test.cli import cli

if __name__ == "__main__":
    cli()