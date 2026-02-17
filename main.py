#!/usr/bin/env python3
"""Entry point for Firefly analyzer."""

import sys
from pathlib import Path

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from firefly_analyzer.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
