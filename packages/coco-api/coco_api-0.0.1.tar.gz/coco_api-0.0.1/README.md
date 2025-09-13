# coco-api

Minimal Python package template for coco-api.

## Install

Once published:

- `pip install coco-api`

## Usage

- `python`
- `>>> from coco_api import CocoAPI`
- `>>> client = CocoAPI()`
- `>>> client.ping()`
- `{'status': 'ok', 'version': '0.0.1'}`
- `>>> client.greet('World')`
- `'Hello, World!'`

## Build & publish

- `python -m pip install --upgrade build twine`
- `python -m build`  # creates `dist/` artifacts
- `twine check dist/*`
- `twine upload dist/*`  # requires PyPI credentials

## Notes

- Package import name is `coco_api` (underscore), distribution name is `coco-api` (hyphen).
- Update `authors` in `pyproject.toml` and bump `version` before release.
