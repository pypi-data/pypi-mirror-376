from datetime import datetime

import pytest

from paraphernalia.utils import download, slugify


@pytest.mark.parametrize(
    "args, expected",
    [
        (["hello world"], "hello-world"),
        (["hello", "world"], "hello_world"),
        (["numbers like 23 are ok"], "numbers-like-23-are-ok"),
        (["ABC"], "abc"),
        # Punctuation
        (["it doesn't blend"], "it-doesn-t-blend"),
        (["$£*^&£$+"], "-"),
        (["dots.are.forbidden"], "dots-are-forbidden"),
        # Special handling for datetime
        ([datetime(2021, 1, 1)], "2021-01-01_00h00"),
        ([datetime(2021, 1, 1).date()], "2021-01-01"),
        # Nested lists are flattened
        ([["nested", "list"]], "nested_list"),
        # Some cases to potentially revisit
        (["--hello--", "__world__"], "--hello--___world__"),
    ],
)
def test_slugify(args, expected):
    assert slugify(*args) == expected


def test_download_404():
    with pytest.raises(Exception) as excinfo:
        download("http://badurl.xyzzy/goo")
    assert "badurl" in excinfo.exconly()
