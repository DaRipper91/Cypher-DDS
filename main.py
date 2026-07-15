"""Buildozer/python-for-android entry point for the Cypher-DDS mobile app.

Buildozer expects main.py at the project root (source.dir in
buildozer.spec). The project itself uses a src/ layout like the rest of
Cypher-DDS, so this just puts that on sys.path and hands off to the real
app in cypher_dds.mobile.app.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from cypher_dds.mobile.app import main  # noqa: E402

if __name__ == "__main__":
    main()
