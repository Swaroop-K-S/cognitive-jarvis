try:
    import daytona
    print(f"✅ Daytona imported successfully: {daytona.__file__}")
except ImportError as e:
    print(f"❌ Failed to import daytona: {e}")

try:
    import structlog
    print(f"✅ Structlog imported successfully.")
except ImportError as e:
    print(f"❌ Failed to import structlog: {e}")
