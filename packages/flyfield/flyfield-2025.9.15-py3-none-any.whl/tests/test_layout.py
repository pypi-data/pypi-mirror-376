import pytest
from flyfield.layout import calculate_layout_fields, assign_numeric_blocks

# Helper to quickly create a box dict with minimal info
def make_box(page_num, bottom, x0=0, x1=10, fill="", field_type=None):
    return {
        "page_num": page_num,
        "bottom": bottom,
        "x0": x0,
        "x1": x1,
        "fill": fill,
        "field_type": field_type,
        "left": x0,  # needed for sorting in assign_numeric_blocks
    }

def test_calculate_layout_fields_basic_grouping():
    # Boxes with same page and close bottoms → same line
    boxes = [
        make_box(1, 100, 0, 10),
        make_box(1, 100.5, 11, 20),
        make_box(1, 20, 0, 10),
        make_box(2, 100, 0, 10),
    ]
    page_dict = calculate_layout_fields(boxes)
    assert 1 in page_dict and 2 in page_dict
    # Boxes with same bottom should share same line number
    lines = {b["line"] for b in page_dict[1]}
    assert len(lines) == 2  # two distinct lines expected

def test_calculate_layout_fields_blocks_and_fill():
    boxes = [
        make_box(1, 100, 0, 10, fill="abc"),
        make_box(1, 100, 15, 20, fill=" def "),
        make_box(1, 20, 0, 10, fill="ghi"),
    ]
    page_dict = calculate_layout_fields(boxes)
    # Blocks should be assigned
    for b in page_dict[1]:
        assert "block" in b
        # block_fill is cleaned combined fill for non-currency field_types
        if b.get("block_length", 0) > 0 and b.get("field_type") not in ("DollarCents", "Dollars"):
            assert "block_fill" in b

def test_assign_numeric_blocks_merges_runs():
    rows = [
        {
            "block_length": 3,
            "pgap": None,
            "left": 0,
            "line": 1,
            "block_width": 10,
            "field_type": None,
            "block_fill": "100",
        },
        {
            "block_length": 3,
            "pgap": 5,
            "left": 20,
            "line": 1,
            "block_width": 10,
            "field_type": None,
            "block_fill": "200",
        },
        {
            "block_length": 2,
            "pgap": 10,
            "left": 40,
            "line": 1,
            "block_width": 8,
            "field_type": None,
            "block_fill": "300",
        },
    ]
    page_dict = {1: rows}
    updated = assign_numeric_blocks(page_dict)
    # The first block of run should have assigned field_type Currency or CurrencyDecimal
    assert updated[1][0].get("field_type") in ("Currency", "CurrencyDecimal")
    # The block_length is aggregated correctly
    assert updated[1][0]["block_length"] >= 3

@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("706935", 7069.35),
        ("35", 0.35),
        ("0", 0.0),
        ("", 0.0),
        ("abc12345", 123.45),
    ],
)
def test_parse_implied_decimal(input_str, expected):
    from flyfield.utils import parse_implied_decimal
    assert abs(parse_implied_decimal(input_str) - expected) < 1e-6
