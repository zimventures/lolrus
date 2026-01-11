"""
lolrus - I has a bucket!

A desktop S3-compatible object storage browser.
"""

import sys


def main() -> int:
    """Main entry point for lolrus."""
    from lolrus.app import LolrusApp

    app = LolrusApp()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
