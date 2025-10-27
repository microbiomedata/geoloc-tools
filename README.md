# GeoEngine geolocation tool
Library to request information about a location regarding the elevation, soil type, and landuse from various web services:

* [ORNL MODIS](https://modis.ornl.gov/rst/ui/#!/products/get_products)
* [Google Maps Platform](https://developers.google.com/maps/documentation)

## Development

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)

### Setup

Install dependencies with uv. This will also create a new virtual environment if necessary.

```bash
uv sync
```

### Testing

Run the test suite using the Makefile target `test`.

```bash
make test
```

### Linting

Run the linter using the Makefile target `lint`.

```bash
make lint
```

Some issues can be automatically fixed by running the Makefile target `lint-fix`.

```bash
make lint-fix
```

### Releasing

To release a new version to PyPI, create a new GitHub Release with a tag in the format `vX.Y.Z`. This will trigger a GitHub Action that will publish the new version to PyPI.
