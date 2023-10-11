from src.geotools.geotools import GeoEngine
import pytest

class TestGeotools:
    ge = GeoEngine()
    def test_elevation_Mount_Everest(self):
        assert int(self.ge.get_elevation((27.9881, 86.9250))) == 8752
        
    def test_elevation_Death_Valley(self):
        assert int(self.ge.get_elevation((36.5322649, -116.9325408))) == -66
        
    def test_elevation_Ocean(self):
        with pytest.raises(ValueError):
            self.ge.get_elevation((0,0))
        
    def test_elevation_Bad_Coordinates(self):
        with pytest.raises(ValueError):
            self.ge.get_elevation((-200, 200))
            
    def test_soil_type_Cambisols(self):
        assert self.ge.get_fao_soil_type((32.95047, -87.393259)) == "Cambisols"
        
    def test_soil_type_Water(self):
        assert self.ge.get_fao_soil_type((0, 0)) == "Water"
        
    def test_soil_type_Bad_Coordinates(self):
        with pytest.raises(ValueError):
            self.ge.get_fao_soil_type((-200, 200))
            
    def test_landuse_Bad_Coordinates(self):
        with pytest.raises(ValueError):
            self.ge.get_landuse((-200, 200),'2001-01-01','2002-01-01')
            
    def test_landuse_date_Death_Valley(self):
        dates=self.ge.get_landuse_dates((36.5322649, -116.9325408))
        assert dates[0] == "2001-01-01"
        
    def test_landuse_Death_Valley(self):
        data=self.ge.get_landuse((36.5322649, -116.9325408),'2001-01-01','2002-01-01')
        assert data['LCCS1'][0]['envo_term'] == "area of barren land"