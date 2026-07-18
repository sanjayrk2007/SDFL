# SDFL Platform root package
import os
import sys
import importlib

# Prevent name collision with the standard library 'platform' module.
# We temporarily remove the current directory from sys.path and sys.modules
# to import the standard library platform module, and then merge its attributes here.
original_sys_path = list(sys.path)
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Remove local paths that might resolve to our platform package
while current_dir in sys.path:
    sys.path.remove(current_dir)
while "" in sys.path:
    sys.path.remove("")
if "." in sys.path:
    sys.path.remove(".")

# Temporarily pop ourselves from sys.modules so importlib looks at the standard library
self_module = sys.modules.pop("platform", None)

try:
    std_platform = importlib.import_module("platform")
    for attr in dir(std_platform):
        if not attr.startswith("__"):
            globals()[attr] = getattr(std_platform, attr)
except ImportError:
    pass
finally:
    # Restore the original sys.path and sys.modules
    sys.path = original_sys_path
    if self_module is not None:
        sys.modules["platform"] = self_module
