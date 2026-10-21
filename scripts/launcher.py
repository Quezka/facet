"""Entry script for frozen builds (PyInstaller needs a file, not a module)."""
from facet.app import main

raise SystemExit(main())
