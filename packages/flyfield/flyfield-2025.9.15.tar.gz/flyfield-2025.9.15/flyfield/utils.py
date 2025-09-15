import os
import re

from .config import COLOR_WHITE as TARGET_COLOUR


def add_suffix_to_filename(filename, suffix):
    """
    Add a suffix before the file extension in a filename.
    """
    base, ext = os.path.splitext(filename)
    return f"{base}{suffix}{ext}"


def colour_match(color, target_color=TARGET_COLOUR, tol=1e-3):
    """
    Check if an input RGB or RGBA color matches the target color within a tolerance.

    Args:
        color (tuple): Color tuple expected as normalized RGB or RGBA (values in range [0.0, 1.0]).
        target_color (tuple): Target RGB tuple (normalized floats) to match against.
        tol (float): Tolerance for color difference on each channel.

    Returns:
        bool: True if the color matches the target within tolerance, otherwise False.

    Note:
        If the input color has an alpha channel (RGBA), the alpha component is ignored.
    """
    if not color or len(color) < 3:
        return False
    # Compare only RGB channels; ignore alpha if present
    return all(abs(a - b) < tol for a, b in zip(color[:3], target_color))


def int_to_rgb(color_int):
    """
    Convert a 24-bit integer color in 0xRRGGBB format to normalized RGB tuple of floats.

    Args:
        color_int (int): Integer encoding color as 0xRRGGBB.

    Returns:
        tuple: Normalized (r, g, b) floats in range [0.0, 1.0].
    """
    r = ((color_int >> 16) & 0xFF) / 255
    g = ((color_int >> 8) & 0xFF) / 255
    b = (color_int & 0xFF) / 255
    return (r, g, b)


def clean_fill_string(line_text):
    """
    Clean a concatenated fill text string by removing single spaces while preserving double spaces as single spaces.

    Args:
        line_text (str): Raw concatenated text containing spaces.

    Returns:
        str: Cleaned string with double spaces replaced by single spaces and single spaces removed.
    """
    line_text = re.sub(r" {2,}", "<<<SPACE>>>", line_text)
    line_text = line_text.replace(" ", "")
    line_text = line_text.replace("<<<SPACE>>>", " ")
    return line_text


def allowed_text(text, field_type=None):
    """
    Determine whether a text string is allowed inside a box based on predefined allowed patterns.
    Helps to filter out pre-filled or invalid box contents.

    Args:
        text (str): Text extracted from a box.
        field_type (str or None): Optional current field type guess to refine allowed patterns.

    Returns:
        tuple: (bool indicating if allowed, detected field type or None)
    """
    allowed_text_by_type = {
        "DollarCents": {".", ".00."},
        "Dollars": {".00", ".00.00"},
    }
    generic_allowed_text = {"S", "M", "I", "T", "H"}
    if field_type in allowed_text_by_type:
        allowed_set = allowed_text_by_type[field_type] | generic_allowed_text
        if text in allowed_set:
            return True, field_type
        else:
            return False, None
    else:
        for ftype, texts in allowed_text_by_type.items():
            if text in texts:
                return True, ftype
        if text in generic_allowed_text:
            return True, None
        return False, None


def format_money_space(amount, decimal=True):
    """
    Format a numeric amount to a string with:
    - space as thousands separator
    - space as decimal separator (if decimals included)
    """
    if decimal:
        s = f"{amount:,.2f}"
        int_part, dec_part = s.split(".")
        int_part = int_part.replace(",", " ")
        return f"{int_part} {dec_part}"
    else:
        s = f"{int(amount):,}"
        int_part = s.replace(",", " ")
        return int_part


def parse_money_space(money_str, decimal=True):
    """
    Parse a string formatted as above back to float or int.
    Expects:
    - space-separated thousands
    - space-separated decimal part (if decimal True)
    """
    if decimal:
        if " " in money_str:
            parts = money_str.rsplit(" ", 1)
            int_part = parts[0].replace(" ", "")
            dec_part = parts[1]
            combined = f"{int_part}.{dec_part}"
            return float(combined)
        else:
            # No decimal part found, treat as int
            return float(money_str.replace(" ", ""))
    else:
        return int(money_str.replace(" ", ""))


def parse_implied_decimal(s):
    """
    Parse a numeric string with implied two-digit decimal.

    Examples:
        "706935" -> 7069.35
        "35" -> 0.35
        "0" -> 0.0

    Args:
        s (str): Numeric string containing only digits

    Returns:
        float: Parsed float with last two digits as decimal fraction
    """
    s = s.strip()
    digits_only = re.sub(r"\D", "", s)

    if not digits_only:
        return 0.0

    if len(digits_only) <= 2:
        # If only 1 or 2 digits, treat as fractional part
        combined = f"0.{digits_only.zfill(2)}"
    else:
        combined = f"{digits_only[:-2]}.{digits_only[-2:]}"
    return float(combined)


def version():
    """
    Get installed package version using importlib.metadata.

    Returns:
        str: Version string, or 'unknown' if not found.
    """
    try:
        # Python 3.8+
        from importlib.metadata import PackageNotFoundError
        from importlib.metadata import version as pkg_version
    except ImportError:
        # For Python <3.8
        from importlib_metadata import PackageNotFoundError
        from importlib_metadata import version as pkg_version

    try:
        return pkg_version("flyfield")
    except PackageNotFoundError:
        return "unknown"


def parse_pages(pages_str):
    """
    Parse a string of page numbers and ranges into a sorted list of integers.

    Example: "1,3,5-7" → [1, 3, 5, 6, 7]

    Args:
        pages_str (str): Comma-separated pages and ranges.

    Returns:
        list[int]: Sorted list of page numbers.
    """
    pages = set()
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            start_str, end_str = part.split("-")
            start, end = int(start_str), int(end_str)
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    return sorted(pages)


def conditional_merge_list(main_list, ref_list, match_key, keys_to_merge):
    """
    Merge specified keys from reference records into main records if they share the same match_key value.

    This function iterates over main_list (list of dictionaries), and for each record,
    it finds a record in ref_list with the same value for match_key.
    When a match is found, keys from keys_to_merge are copied from the reference
    record into the main record. The main_list is updated in-place.

    Parameters
    ----------
    main_list : list of dict
        The list of dictionaries to update, e.g. [{'code': ..., 'value': ...}, ...].
    ref_list : list of dict
        The reference list providing keys and values to merge, e.g. [{'code': ..., 'field_type': ...}, ...].
    match_key : str
        The key used to find matches between items in main_list and ref_list.
    keys_to_merge : iterable of str
        The keys to copy from the reference record into the main record on match.

    Returns
    -------
    None
        Updates main_list records in place.

    Example
    -------
    >>> data = [{'code': 'A', 'value': 1}, {'code': 'B', 'value': 2}]
    >>> boxes = [{'code': 'A', 'field_type': 'ID'}, {'code': 'B', 'field_type': 'ID'}]
    >>> conditional_merge_list(data, boxes, 'code', ['field_type'])
    >>> print(data)
    [{'code': 'A', 'value': 1, 'field_type': 'ID'}, {'code': 'B', 'value': 2, 'field_type': 'ID'}]
    """
    # Build lookup dictionary for efficient matching
    ref_lookup = {item[match_key]: item for item in ref_list if match_key in item}
    for record in main_list:
        ref_record = ref_lookup.get(record.get(match_key))
        if ref_record:
            for key in keys_to_merge:
                if key in ref_record:
                    record[key] = ref_record[key]
