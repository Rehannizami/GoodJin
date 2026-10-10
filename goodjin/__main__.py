"""GoodJin main module executable entry point."""

import sys
from pathlib import Path

# Ensure package root is in sys.path
package_root = Path(__file__).resolve().parent.parent
if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))

from goodjin.cli import main

if __name__ == "__main__":
    main()
