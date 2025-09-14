#!/usr/bin/env python3
"""
JSBucket CLI entry point.

This script provides a clean entry point for the JSBucket command-line interface
without module import conflicts.
"""

if __name__ == "__main__":
    from jsbucket.core import main
    main()
