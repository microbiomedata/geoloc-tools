import csv
import json
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

import requests

LATLON = Tuple[float, float]


@dataclass
class GeoEngine:
    """
    Wraps ORNL Identify to retrieve elevation data in meters, soil types, and land use.
    """

    def get_elevation(self, latlon: LATLON) -> float:
        """
        Accepts decimal degrees latitude and longitude as an array (array[latitude, longitude]) and returns the elevation value in meters as a float.
        """
        lat = latlon[0]
        lon = latlon[1]
        if not -90 <= lat <= 90:
            raise ValueError("Invalid Latitude: " + str(lat))
        if not -180 <= lon <= 180:
            raise ValueError("Invalid Longitude: " + str(lon))
        # Generate bounding box used in query from lat & lon. 0.008333333333333 comes from maplayer resolution provided by ORNL
        remX = (lon + 180) % 0.008333333333333
        remY = (lat + 90) % 0.008333333333333
        minX = lon - remX
        maxX = lon - remX + 0.008333333333333
        minY = lat - remY
        maxY = lat - remY + 0.008333333333333
        BBOX = str(minX) + "," + str(minY) + "," + str(maxX) + "," + str(maxY)
        elevparams = {
            "originator": "QAQCIdentify",
            "SERVICE": "WMS",
            "VERSION": "1.1.1",
            "REQUEST": "GetFeatureInfo",
            "SRS": "EPSG:4326",
            "WIDTH": "5",
            "HEIGHT": "5",
            "LAYERS": "10003_1",
            "QUERY_LAYERS": "10003_1",
            "X": "2",
            "Y": "2",
            "INFO_FORMAT": "text/xml",
            "BBOX": BBOX,
        }
        response = requests.get(
            "https://webmap.ornl.gov/ogcbroker/wms", params=elevparams
        )
        if response.status_code == 200:
            elevxml = response.content.decode("utf-8")
            if elevxml == "":
                raise ValueError("No Elevation value returned")
            root = ET.fromstring(elevxml)
            results = root[3].text
            return float(results)
        else:
            raise ApiException(response.status_code)

    def get_fao_soil_type(self, latlon: LATLON) -> str:
        """
        Accepts decimal degrees latitude and longitude as an array (array[latitude, longitude]) and returns the soil type as a string.
        """
        lat = latlon[0]
        lon = latlon[1]
        if not -90 <= lat <= 90:
            raise ValueError("Invalid Latitude: " + str(lat))
        if not -180 <= lon <= 180:
            raise ValueError("Invalid Longitude: " + str(lon))
        # Generate bounding box used in query from lat & lon. 0.5 comes from maplayer resolution provided by ORNL
        remX = (lon + 180) % 0.5
        remY = (lat + 90) % 0.5
        minX = lon - remX
        maxX = lon - remX + 0.5
        minY = lat - remY
        maxY = lat - remY + 0.5

        # Read in the mapping file note need to get this path right
        with open(
            os.path.dirname(__file__) + "/data/zobler_540_MixS_lookup.csv"
        ) as mapper:
            mapping = csv.reader(mapper)
            map = list(mapping)

        BBoxstring = str(minX) + "," + str(minY) + "," + str(maxX) + "," + str(maxY)

        faosoilparams = {
            "INFO_FORMAT": "text/xml",
            "WIDTH": "5",
            "originator": "QAQCIdentify",
            "HEIGHT": "5",
            "LAYERS": "540_1_band1",
            "REQUEST": "GetFeatureInfo",
            "SRS": "EPSG:4326",
            "BBOX": BBoxstring,
            "VERSION": "1.1.1",
            "X": "2",
            "Y": "2",
            "SERVICE": "WMS",
            "QUERY_LAYERS": "540_1_band1",
            "map": "/sdat/config/mapfile//540/540_1_wms.map",
        }
        response = requests.get(
            "https://webmap.ornl.gov/cgi-bin/mapserv", params=faosoilparams
        )
        if response.status_code == 200:
            faosoilxml = response.content.decode("utf-8")
            if faosoilxml == "":
                raise ValueError("Empty string returned")
            root = ET.fromstring(faosoilxml)
            results = root[5].text
            results = results.split(":")
            results = results[1].strip()
            for res in map:
                if res[0] == results:
                    results = res[1]
                    return results
            raise ValueError("Response mapping failed")
        else:
            raise ApiException(response.status_code)

    def get_landuse_dates(self, latlon: LATLON) -> []:
        """
        Accepts decimal degrees latitude and longitude as an array (array[latitude, longitude]) and returns as array of valid dates (YYYY-MM-DD format) for the landuse requests.
        """
        lat = latlon[0]
        lon = latlon[1]
        if not -90 <= lat <= 90:
            raise ValueError("Invalid Latitude: " + str(lat))
        if not -180 <= lon <= 180:
            raise ValueError("Invalid Longitude: " + str(lon))
        landuseparams = {"latitude": lat, "longitude": lon}
        response = requests.get(
            "https://modis.ornl.gov/rst/api/v1/MCD12Q1/dates", params=landuseparams
        )
        if response.status_code == 200:
            landuseDates = response.content.decode("utf-8")
            if landuseDates == "":
                raise ValueError("No valid Landuse dates returned")
            data = json.loads(landuseDates)
            validDates = []
            for date in data["dates"]:
                validDates.append(date["calendar_date"])
            return validDates
        else:
            raise ApiException(response.status_code)

    def get_landuse(self, latlon: LATLON, startDate, endDate) -> {}:
        """
        Accepts decimal degrees latitude and longitude as an array (array[latitude, longitude]), the start date (YYYY-MM-DD), and end date (YYYY-MM-DD) and returns a dictionary containing the land use values for the classification systems for the dates requested.
        """
        lat = latlon[0]
        lon = latlon[1]
        if not -90 <= lat <= 90:
            raise ValueError("Invalid Latitude: " + str(lat))
        if not -180 <= lon <= 180:
            raise ValueError("Invalid Longitude: " + str(lon))
        # function accepts dates in YYYY-MM-DD format, but API requires a unique format (AYYYYDOY)
        date_format = "%Y-%m-%d"
        start_date_obj = datetime.strptime(startDate, date_format)
        end_date_obj = datetime.strptime(endDate, date_format)

        apiStartDate = (
            "A" + str(start_date_obj.year) + str(start_date_obj.strftime("%j"))
        )
        apiEndDate = "A" + str(end_date_obj.year) + str(end_date_obj.strftime("%j"))

        landuseparams = {
            "latitude": lat,
            "longitude": lon,
            "startDate": apiStartDate,
            "endDate": apiEndDate,
            "kmAboveBelow": 0,
            "kmLeftRight": 0,
        }
        response = requests.get(
            "https://modis.ornl.gov/rst/api/v1/MCD12Q1/subset", params=landuseparams
        )
        # Retrieve Classification System mapping
        with open(
            os.path.dirname(__file__) + "/data/ENVO_Landuse_Systems_lookup.csv"
        ) as mapper:
            mapping = csv.reader(mapper)
            sytems_map = list(mapping)
        # Retrieve Classification System to ENVO mapping
        with open(
            os.path.dirname(__file__) + "/data/ENVO_Landuse_lookup.csv"
        ) as mapper:
            mapping = csv.reader(mapper)
            landuse_map = list(mapping)
        if response.status_code == 200:
            landuse = response.content.decode("utf-8")
            results = {}
            if landuse == "":
                raise ValueError("No Landuse value returned")
            data = json.loads(landuse)
            for band in data["subset"]:
                system = "NONE"
                band["data"] = list(map(int, band["data"]))
                for res in sytems_map:
                    if res[1] == band["band"]:
                        system = res[0]
                for res in landuse_map:
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
