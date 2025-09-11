
from pathlib import Path

import pytest
from pydvdid2 import compute


isos = [ path for path in Path('test-data').iterdir() if path.suffix == '.iso' ]


@pytest.mark.parametrize("iso_path", isos)
def test_generated_iso(iso_path: Path) -> None:
    with open(iso_path.parent / (iso_path.stem + '.crc64'), 'r') as f:
        expected = f.read().strip()
    actual = compute(str(iso_path))
    assert(expected == str(actual))

