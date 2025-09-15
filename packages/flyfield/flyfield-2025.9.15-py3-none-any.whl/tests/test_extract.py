import pytest
from flyfield.extract import remove_duplicates, sort_boxes

def make_box(page_num=1, x0=0, y0=0, x1=10, y1=10, bottom=10, left=0):
    return {
        "page_num": page_num,
        "x0": x0,
        "y0": y0,
        "x1": x1,
        "y1": y1,
        "bottom": bottom,
        "left": left,
    }

def test_remove_duplicates_removes_close_points():
    boxes = [
        make_box(),
        make_box(x0=0.0001),  # Near-duplicate of first box
        make_box(x0=20),
    ]
    cleaned = remove_duplicates(boxes)
    assert len(cleaned) == 2
    # Ensure original first point remains
    assert any(abs(b["x0"]) < 1e-5 for b in cleaned)

def test_sort_boxes_orders_by_page_and_position():
    boxes = [
        make_box(page_num=1, bottom=100, left=10),
        make_box(page_num=1, bottom=100, left=5),
        make_box(page_num=2, bottom=150, left=-1),
    ]
    sorted_boxes = sort_boxes(boxes)
    # Sorted by page first
    assert sorted_boxes[0]["page_num"] == 1
    assert sorted_boxes[-1]["page_num"] == 2
    # Within page 1, highest bottom first then left
    assert sorted_boxes[0]["left"] == 5
    assert sorted_boxes[1]["left"] == 10

# Additional tests could mock fitz and test extract_boxes, filter_boxes if desired,
# but those require PDF fixture files or mocks of fitz objects.

