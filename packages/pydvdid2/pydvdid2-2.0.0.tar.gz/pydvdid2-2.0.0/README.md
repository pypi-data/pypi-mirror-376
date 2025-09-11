pydvdid2
========

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pydvdid2?style=for-the-badge)](https://pypi.org/project/pydvdid2)
[![PyPI - Downloads](https://img.shields.io/pypi/dw/pydvdid2?style=for-the-badge)](https://pypi.org/project/pydvdid2)

## Overview

[_pydvdid2_][pydvdid2] is a continuation of the stale [pydvdid][pydvdid] Python
package. Just like its predecessor, this library is a pure Python
implementation of the Windows API [`IDvdInfo2::GetDiscID`][winmethod] method,
as used by Windows Media Center to compute a 'practically unique' 64-bit
[CRC][crc] for metadata retrieval.

[pydvdid2]: https://github.com/samvv/pydvdid2
[pydvdid]: https://github.com/sjwood/pydvdid
[winmethod]: https://msdn.microsoft.com/en-us/library/windows/desktop/dd376453.aspx
[dvdid]: http://dvdid.cjkey.org.uk/
[crc]: https://en.wikipedia.org/wiki/Cyclic_redundancy_check

## Differences from `pydvdid`

 - Integrated [pull request #1][pull] by
   [rlaphoenix](https://github.com/rlaphoenix) in the original repo, making it
   possible to calculate the CRC64 without mounting the disk
 - Introduced a `pyproject.toml`
 - Dependencies have been updated
 - Typings have been added where possible
 - Fixed some logic error discovered during typing

[pull]: https://github.com/sjwood/pydvdid/pull/1

## Motivation

I needed a zero-knowledge way to recover some basic information about an
inserted DVD or a mounted ISO image, and whilst googling ran across
[dvdid][dvdid]. A compiled solution didn't fit with my requirement, so I
re-implemented it as a Python module. Kudos go to Christopher Key for
originally developing dvdid and documenting the algorithm so thoroughly.

pydvdid2 is envisaged to be useful for DVD ripping scripts, custom Growl
notifications, and media centre related home automation tasks.

## Compatibility

Works only with Python 3.

Support for Windows, Mac OS and Linux.

## Availability

Get it from PyPI or directly from GitHub.

### PyPI

|PyPI status|
|PyPI version|
|PyPI format|
|PyPI python versions|

```sh
pip install pydvdid2
```

### GitHub

Download a tagged version from the releases page, if available.

## Examples

### From the shell

```sh
$ crc64=$(pydvdid2 /dev/sr0)
$ echo $crc64
f8f9d45140065acc
$ curl --get https://1337server.pythonanywhere.com/api/v1/?mode=s&crc64=$crc64
{
  "mode": "search",
  "results": {
    "0": {
      "crc_id": "f8f9d45140065acc",
      "date_added": "2023-02-04 20:47:28.839849",
      "disctype": "None",
      "hasnicetitle": "True",
      "imdb_id": "tt0208092",
      "label": "SNATCH",
      "no_of_titles": "None",
      "poster_img": "None",
      "title": "Snatch",
      "tmdb_id": "None",
      "validated": "False",
      "video_type": "movie",
      "year": "2000"
    }
  },
  "success": true
}
```

### From Python

pydvdid2 has a decidely simple API, with the important bits imported into the package level so they can be conveniently imported directly from the package.


```python
>>> from pydvdid import compute
>>> crc64 = compute("/dev/sr0")  # or "E:" e.t.c
>>> str(crc64)
'f8f9d45140065acc'
>>> from urllib import urlopen
>>> urlopen(f"https://1337server.pythonanywhere.com/api/v1/?mode=s&crc64={crc64}").read()
{
  "mode": "search",
  "results": {
    "0": {
      "crc_id": "f8f9d45140065acc",
      "date_added": "2023-02-04 20:47:28.839849",
      "disctype": "None",
      "hasnicetitle": "True",
      "imdb_id": "tt0208092",
      "label": "SNATCH",
      "no_of_titles": "None",
      "poster_img": "None",
      "title": "Snatch",
      "tmdb_id": "None",
      "validated": "False",
      "video_type": "movie",
      "year": "2000"
    }
  },
  "success": true
}
```

## License

Apache License, Version 2.0
