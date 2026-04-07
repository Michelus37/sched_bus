import shutil
from pathlib import Path

pycache = Path("__pycache__")
if pycache.exists():
    shutil.rmtree(pycache)
    print(f"Deleted {pycache}")
else:
    print(f"{pycache} does not exist")

# Also clear sys modules
import sys
for mod in list(sys.modules.keys()):
    if any(x in mod for x in ['models', 'detector', 'card', 'test_']):
        del sys.modules[mod]
        print(f"Cleared {mod}")

print("Cache cleared!")
