"""
Functions which wrap ORNL Identify to retrieve elevation data in meters, soil types, and land use.
"""

import csv
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from functools import cache, lru_cache
from pathlib import Path
from typing import Tuple

import requests
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LATLON = Tuple[float, float]


@cache
def read_data_csv(filename: str) -> list:
    with open(Path(__file__).parent / "data" / filename) as file:
        mapping = csv.reader(file)
        return list(mapping)


def _zobler_soil_type_lookup() -> list:
    return read_data_csv("zobler_540_MixS_lookup.csv")


def _envo_landuse_systems_lookup() -> list:
    return read_data_csv("ENVO_Landuse_Systems_lookup.csv")


def _envo_landuse_lookup() -> list:
    return read_data_csv("ENVO_Landuse_lookup.csv")


def _validate_latlon(latlon: LATLON):
    lat = latlon[0]
    lon = latlon[1]
    if not -90 <= lat <= 90:
        raise ValueError(f"Invalid Latitude: {lat}")
    if not -180 <= lon <= 180:
        raise ValueError(f"Invalid Longitude: {lon}")
    return lat, lon


def _bbox(lat: float, lon: float, resolution: float) -> str:
    rem_x = (lon + 180) % resolution
    rem_y = (lat + 90) % resolution
    min_x = lon - rem_x
    max_x = lon - rem_x + resolution
    min_y = lat - rem_y
    max_y = lat - rem_y + resolution
    return f"{min_x},{min_y},{max_x},{max_y}"


@lru_cache
def elevation(latlon: LATLON) -> float:
    """
    Accepts decimal degrees latitude and longitude as an array (array[latitude, longitude]) and
    returns the elevation value in meters as a float.
    """
    lat, lon = _validate_latlon(latlon)
    params = {"locations": f"{lat},{lon}", "key": GOOGLE_API_KEY}
    response = requests.get(
        "https://maps.googleapis.com/maps/api/elevation/json", params=params
    )
    if response.status_code == 200:
        elevjson = response.json()
        if elevjson["results"] == []:
            raise ValueError("No Elevation value returned")
        results = elevjson["results"][0]["elevation"]
        return float(results)
    else:
        raise ApiException(response.status_code)


@lru_cache
def fao_soil_type(latlon: LATLON) -> str:
    """
    Accepts decimal degrees latitude and longitude as an array (array[latitude, longitude]) and
    returns the soil type as a string.
    """
    lat, lon = _validate_latlon(latlon)
    # Generate bounding box used in query from lat & lon. 0.5 comes from maplayer resolution
    # provided by ORNL
    bbox = _bbox(lat, lon, 0.5)

    fao_soil_params = {
        "INFO_FORMAT": "text/xml",
        "WIDTH": "5",
        "originator": "QAQCIdentify",
        "HEIGHT": "5",
        "LAYERS": "540_1_band1",
        "REQUEST": "GetFeatureInfo",
        "SRS": "EPSG:4326",
        "BBOX": bbox,
        "VERSION": "1.1.1",
        "X": "2",
        "Y": "2",
        "SERVICE": "WMS",
        "QUERY_LAYERS": "540_1_band1",
        "map": "/sdat/config/mapfile/540/540_1_wms.map",
    }
    response = requests.get(
        "https://webmap.ornl.gov/cgi-bin/mapserv", params=fao_soil_params
    )
    if response.status_code == 200:
        fao_soil_xml = response.content.decode("utf-8")
        if fao_soil_xml == "":
            raise ValueError("Empty string returned")
        root = ET.fromstring(fao_soil_xml)
        results = root[5].text
        results = results.split(":")
        results = results[1].strip()
        for res in _zobler_soil_type_lookup():
            if res[0] == results:
                results = res[1]
                return results
        raise ValueError("Response mapping failed")
    else:
        raise ApiException(response.status_code)


@lru_cache
def landuse_dates(latlon: LATLON) -> []:
    """
    Accepts decimal degrees latitude and longitude as an array (array[latitude, longitude]) and
    returns as array of valid dates (YYYY-MM-DD format) for the landuse requests.
    """
    lat, lon = _validate_latlon(latlon)
    landuse_params = {"latitude": lat, "longitude": lon}
    response = requests.get(
        "https://modis.ornl.gov/rst/api/v1/MCD12Q1/dates", params=landuse_params
    )
    if response.status_code == 200:
        landuse_dates_json = response.content.decode("utf-8")
        if landuse_dates_json == "":
            raise ValueError("No valid Landuse dates returned")
        data = json.loads(landuse_dates_json)
        valid_dates = []
        for date in data["dates"]:
            valid_dates.append(date["calendar_date"])
        return valid_dates
    else:
        raise ApiException(response.status_code)


@lru_cache
def landuse(latlon: LATLON, start_date, end_date) -> {}:
    """
    Accepts decimal degrees latitude and longitude as an array (array[latitude, longitude]), the
    start date (YYYY-MM-DD), and end date (YYYY-MM-DD) and returns a dictionary containing the
    land use values for the classification systems for the dates requested.
    """
    lat, lon = _validate_latlon(latlon)
    # function accepts dates in YYYY-MM-DD format, but API requires a unique format (AYYYYDOY)
    date_format = "%Y-%m-%d"
    start_date_obj = datetime.strptime(start_date, date_format)
    end_date_obj = datetime.strptime(end_date, date_format)

    api_start_date = "A" + str(start_date_obj.year) + str(start_date_obj.strftime("%j"))
    api_end_date = "A" + str(end_date_obj.year) + str(end_date_obj.strftime("%j"))

    landuse_params = {
        "latitude": lat,
        "longitude": lon,
        "startDate": api_start_date,
        "endDate": api_end_date,
        "kmAboveBelow": 0,
        "kmLeftRight": 0,
    }
    response = requests.get(
        "https://modis.ornl.gov/rst/api/v1/MCD12Q1/subset", params=landuse_params
    )
    if response.status_code == 200:
        landuse = response.content.decode("utf-8")
        results = {}
        if landuse == "":
            raise ValueError("No Landuse value returned")
        data = json.loads(landuse)
        for band in data["subset"]:
            system = "NONE"
            band["data"] = list(map(int, band["data"]))
            for res in _envo_landuse_systems_lookup():
                if res[1] == band["band"]:
                    system = res[0]
            for res in _envo_landuse_lookup():
                if res[8] == system and int(res[1]) in band["data"]:
                    envo_term = res[2]
                    if envo_term == "":
                        envo_term = "ENVO Term unavailable"
                    entry = {
                        "date": band["calendar_date"],
                        "envo_term": envo_term,
                        "system_description": res[6],
                        "system_term": res[0],
                    }
                    try:
                        results[system].append(entry)
                    except KeyError:
                        results[system] = []
                        results[system].append(entry)
        return results
    else:
        raise ApiException(response.status_code)


class ApiException(Exception):
    """
    Exception class for the various API requests used by GeoEngine.
    """

    def __init__(self, status_code):
        if status_code == 400:
            message = "API Exception - Bad Request."
        elif status_code == 401:
            message = "API Exception - Unauthorized."
        elif status_code == 403:
            message = "API Exception - Forbidden."
        elif status_code == 404:
            message = "API Exception - Not Found."
        elif status_code == 429:
            message = "API Exception - Resource Exhausted."
        elif status_code == 500:
            message = "API Exception - Internal Server Error."
        elif status_code == 502:
            message = "API Exception - Bad Gateway."
        elif status_code == 503:
            message = "API Exception - Service Unavailable. Try again later."
        elif status_code == 504:
            message = "API Exception - Gateway Timeout."
        else:
            message = f"API Exception - Status Code: {status_code}."

        super().__init__(message)
