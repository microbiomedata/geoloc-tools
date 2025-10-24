import pytest
import requests
import requests_mock

from nmdc_geoloc_tools import elevation, fao_soil_type, landuse, landuse_dates


def test_elevation_mount_everest():
    with requests_mock.Mocker() as m:
        m.get(
            "https://maps.googleapis.com/maps/api/elevation/json",
            additional_matcher=lambda request: request.qs
            == {"locations": ["27.9881,86.925"], "key": ["test_api_key"]},
            json={"results": [{"elevation": 8729}]},
        )
        assert int(elevation((27.9881, 86.9250), "test_api_key")) == 8729


def test_elevation_death_valley():
    with requests_mock.Mocker() as m:
        m.get(
            "https://maps.googleapis.com/maps/api/elevation/json",
            additional_matcher=lambda request: request.qs
            == {"locations": ["36.5322649,-116.9325408"], "key": ["test_api_key"]},
            json={"results": [{"elevation": -80}]},
        )
        assert int(elevation((36.5322649, -116.9325408), "test_api_key")) == -80


def test_elevation_ocean():
    with requests_mock.Mocker() as m:
        m.get(
            "https://maps.googleapis.com/maps/api/elevation/json",
            additional_matcher=lambda request: request.qs
            == {"locations": ["0,0"], "key": ["test_api_key"]},
            json={"results": [{"elevation": -3492}]},
        )
        assert int(elevation((0, 0), "test_api_key")) == -3492


def test_elevation_bad_coordinates():
    with pytest.raises(ValueError):
        elevation((-200, 200), "test_api_key")


def test_elevation_caching(mocker):
    with requests_mock.Mocker() as m:
        m.get(
            "https://maps.googleapis.com/maps/api/elevation/json",
            additional_matcher=lambda request: request.qs
            == {"locations": ["45,-120"], "key": ["test_api_key"]},
            json={"results": [{"elevation": 100}]},
        )

        # Spy on requests.get method
        spy = mocker.spy(requests, "get")

        result1 = elevation((45, -120), "test_api_key")
        assert result1 == 100
        assert spy.call_count == 1

        result2 = elevation((45, -120), "test_api_key")
        assert result2 == 100
        assert spy.call_count == 1
        m.get(
            "https://maps.googleapis.com/maps/api/elevation/json",
            additional_matcher=lambda request: request.qs
            == {"locations": ["46,-120"], "key": ["test_api_key"]},
            json={"results": [{"elevation": 100}]},
        )
        result3 = elevation((46, -120), "test_api_key")
        assert result3 == 100
        assert spy.call_count == 2


def test_soil_type_cambisols():
    with pytest.raises(NotImplementedError):
        fao_soil_type((32.95047, -87.393259))


def test_soil_type_water():
    with pytest.raises(NotImplementedError):
        fao_soil_type((0, 0))


def test_soil_type_bad_coordinates():
    with pytest.raises(NotImplementedError):
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
