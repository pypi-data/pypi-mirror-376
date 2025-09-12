"""CSV data loader using pandas."""

from ... import matchers
from ...core import Attachment, loader


@loader(match=matchers.csv_match)
def csv_to_pandas(att: Attachment) -> Attachment:
    """Load CSV into pandas DataFrame with automatic input source handling."""
    try:
        from io import StringIO

        import pandas as pd

        # Use the new text_content property - no more repetitive patterns!
        content = att.text_content

        # For CSV, we need StringIO for pandas regardless of source
        if isinstance(content, str):
            att._obj = pd.read_csv(StringIO(content))
        else:
            # Fallback for direct file path
            att._obj = pd.read_csv(att.path)

    except ImportError as err:
        raise ImportError(
            "pandas is required for CSV loading. Install with: pip install pandas"
        ) from err
    return att
