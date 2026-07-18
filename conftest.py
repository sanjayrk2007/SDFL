import os
import sys
import platform

# Resolve namespace collision: turn the standard library 'platform' module
# into a package by defining its __path__ to point to our local 'platform' directory.
# This allows pytest and logging to run normally while letting python resolve
# platform.coordinator, platform.client, platform.tests, etc.
current_dir = os.path.dirname(os.path.abspath(__file__))
platform_path = os.path.join(current_dir, "platform")

if hasattr(platform, "__path__"):
    if platform_path not in platform.__path__:
        platform.__path__.append(platform_path)
else:
    platform.__path__ = [platform_path]
