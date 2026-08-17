"""build.py and validate.py live in site/ and import each other by bare name,
so site/ has to be on sys.path before either can be imported."""

import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
if str(SITE) not in sys.path:
    sys.path.insert(0, str(SITE))
