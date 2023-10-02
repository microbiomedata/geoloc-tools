from typing import Optional, List, Set, Any, Tuple
from dataclasses import dataclass
import logging
import requests
import xml.etree.ElementTree as ET
import csv
import pytest
import os

LATLON = Tuple[float, float]


@dataclass
class GeoEngine():
    """
    This can wrap any number of external services

    In future this will wrap ORNL Identify
    """

    def get_elevation(self, latlon: LATLON) -> str:
        lat = latlon[0]
        lon = latlon[1]
        if not -90 <= lat <= 90:
            raise ValueError("Invalid Latitude: "+str(lat))
        if not -180 <= lon <= 180:
            raise ValueError("Invalid Longitude: "+str(lon))
        remX = (lon + 180) % 0.008333333333333
        remY = (lat + 90) % 0.008333333333333
        minX = lon - remX
        maxX = lon - remX + 0.008333333333333
        minY = lat - remY
        maxY = lat - remY + 0.008333333333333
        BBOX = str(minX) + ',' + str(minY) + ',' + str(maxX) + ',' + str(maxY)
        elevparams = {'originator': 'QAQCIdentify',
                      'SERVICE': 'WMS',
                      'VERSION': '1.1.1',
                      'REQUEST': 'GetFeatureInfo',
                      'SRS': 'EPSG:4326',
                      'WIDTH': '5',
                      'HEIGHT': '5',
                      'LAYERS': '10003_1',
                      'QUERY_LAYERS': '10003_1',
                      'X': '2',
                      'Y': '2',
                      'INFO_FORMAT': 'text/xml',
                      'BBOX': BBOX

                      }
        response = requests.get('https://webmap.ornl.gov/ogcbroker/wms', params=elevparams)
        if response.status_code == 200:
            elevxml = response.content.decode('utf-8')
            if elevxml == "":
                raise ValueError("No Elevation value returned")
            root = ET.fromstring(elevxml)
            results = (root[3].text)
            return results
        else:
            raise ApiException(response.status_code)

    def get_fao_soil_type(self, latlon: LATLON) -> str:
        # Routine to calculate the locations from lat/long
        lat = latlon[0]
        lon = latlon[1]
        if not -90 <= lat <= 90:
            raise ValueError("Invalid Latitude: "+str(lat))
        if not -180 <= lon <= 180:
            raise ValueError("Invalid Longitude: "+str(lon))
        remX = (lon + 180) % 0.5
        remY = (lat + 90) % 0.5
        minX = lon - remX
        maxX = lon - remX + 0.5
        minY = lat - remY
        maxY = lat - remY + 0.5

        # Read in the mapping file note need to get this path right
        #with open(git_root('sample_annotator/geolocation/zobler_540_MixS_lookup.csv')) as mapper:
        with open(os.path.dirname(__file__)+'/data/zobler_540_MixS_lookup.csv') as mapper:
            mapping = csv.reader(mapper)
            map = list(mapping)

        BBoxstring = str(minX) + ',' + str(minY) + ',' + str(maxX) + ',' + str(maxY)

        faosoilparams = {'INFO_FORMAT': 'text/xml',
                         'WIDTH': '5',
                         'originator': 'QAQCIdentify',
                         'HEIGHT': '5',
                         'LAYERS': '540_1_band1',
                         'REQUEST': 'GetFeatureInfo',
                         'SRS': 'EPSG:4326',
                         'BBOX': BBoxstring,
                         'VERSION': '1.1.1',
                         'X': '2',
                         'Y': '2',
                         'SERVICE': 'WMS',
                         'QUERY_LAYERS': '540_1_band1',
                         'map': '/sdat/config/mapfile//540/540_1_wms.map'}
        response = requests.get('https://webmap.ornl.gov/cgi-bin/mapserv', params=faosoilparams)
        if response.status_code == 200:
            faosoilxml = response.content.decode('utf-8')
            if faosoilxml == "":
                raise ValueError("Empty string returned")           
            root = ET.fromstring(faosoilxml)
            results = (root[5].text)
            results = results.split(':')
            results = results[1].strip()
            #results = 'bad'
            for res in map:
                if res[0] == results:
                    results = res[1]
                    return results
            raise ValueError("Response mapping failed")
        else:
            raise ApiException(response.status_code)
            
            
        
            
class ApiException(Exception):
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