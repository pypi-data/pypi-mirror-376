def safe_filename(name: str) -> str:
    """Convert text into a filesystem-safe filename."""
    return "".join(c if c.isalnum() else "_" for c in name).strip("_")
