"""
Allow running pyekw as a module: python -m pyekw.
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
