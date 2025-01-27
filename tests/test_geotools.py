import pytest

from nmdc_geoloc_tools import elevation, fao_soil_type, landuse, landuse_dates


def test_elevation_mount_everest():
    assert int(elevation((27.9881, 86.9250))) == 8752


def test_elevation_death_valley():
    assert int(elevation((36.5322649, -116.9325408))) == -66


def test_elevation_ocean():
    with pytest.raises(ValueError):
        elevation((0, 0))


def test_elevation_bad_coordinates():
    with pytest.raises(ValueError):
        elevation((-200, 200))


def test_soil_type_cambisols():
    assert fao_soil_type((32.95047, -87.393259)) == "Cambisols"


def test_soil_type_water():
    assert fao_soil_type((0, 0)) == "Water"


def test_soil_type_bad_coordinates():
    with pytest.raises(ValueError):
        fao_soil_type((-200, 200))


def test_landuse_bad_coordinates():
    with pytest.raises(ValueError):
        landuse((-200, 200), "2001-01-01", "2002-01-01")


def test_landuse_date_death_valley():
    dates = landuse_dates((36.5322649, -116.9325408))
    assert dates[0] == "2001-01-01"


def test_landuse_death_valley():
    data = landuse((36.5322649, -116.9325408), "2001-01-01", "2002-01-01")
    assert data["LCCS1"][0]["envo_term"] == "area of barren land"
