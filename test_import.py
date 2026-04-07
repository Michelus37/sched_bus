import sys
import shutil
from pathlib import Path

# Clear pycache
pycache = Path("__pycache__")
if pycache.exists():
    shutil.rmtree(pycache)
    print("Cleared __pycache__")

# Clear modules
for mod in list(sys.modules.keys()):
    if any(x in mod for x in ['vision', 'state_detector', 'test_']):
        del sys.modules[mod]

# Now import fresh
from vision import PILScreenCapture
print("Successfully imported PILScreenCapture")
print(f"PILScreenCapture: {PILScreenCapture}")
