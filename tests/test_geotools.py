import pytest

from nmdc_geoloc_tools.geotools import GeoEngine


@pytest.fixture()
def engine():
    return GeoEngine()


def test_elevation_mount_everest(engine):
    assert int(engine.get_elevation((27.9881, 86.9250))) == 8752


def test_elevation_death_valley(engine):
    assert int(engine.get_elevation((36.5322649, -116.9325408))) == -66


def test_elevation_ocean(engine):
    with pytest.raises(ValueError):
        engine.get_elevation((0, 0))


def test_elevation_bad_coordinates(engine):
    with pytest.raises(ValueError):
        engine.get_elevation((-200, 200))


def test_soil_type_cambisols(engine):
    assert engine.get_fao_soil_type((32.95047, -87.393259)) == "Cambisols"


def test_soil_type_water(engine):
    assert engine.get_fao_soil_type((0, 0)) == "Water"


def test_soil_type_bad_coordinates(engine):
    with pytest.raises(ValueError):
        engine.get_fao_soil_type((-200, 200))


def test_landuse_bad_coordinates(engine):
    with pytest.raises(ValueError):
        engine.get_landuse((-200, 200), "2001-01-01", "2002-01-01")


def test_landuse_date_death_valley(engine):
    dates = engine.get_landuse_dates((36.5322649, -116.9325408))
    assert dates[0] == "2001-01-01"


def test_landuse_death_valley(engine):
    data = engine.get_landuse(
        (36.5322649, -116.9325408), "2001-01-01", "2002-01-01"
    )
    assert data["LCCS1"][0]["envo_term"] == "area of barren land"
