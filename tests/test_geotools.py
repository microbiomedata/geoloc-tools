from src.geotools.geotools import GeoEngine
import pytest

class TestGeotools:
    ge = GeoEngine()
    def test_elevation_Mount_Everest(self):
        assert int(self.ge.get_elevation((27.9881, 86.9250))) == 8752
        
    def test_elevation_Death_Valley(self):
        assert int(self.ge.get_elevation((27.9881, 86.9250))) == 8752
        
    def test_elevation_Ocean(self):
        with pytest.raises(ValueError):
            self.ge.get_elevation((0,0))
        
    def test_elevation_Bad_Coordinates(self):
        with pytest.raises(ValueError):
            self.ge.get_elevation([-200, 200])
            
    def test_soil_type_Cambisols(self):
        assert self.ge.get_fao_soil_type((32.95047, -87.393259)) == "Cambisols"
        
    def test_soil_type_Water(self):
        assert self.ge.get_fao_soil_type((0, 0)) == "Water"
        
    def test_soil_type_Bad_Coordinates(self):
        with pytest.raises(ValueError):
            self.ge.get_fao_soil_type([-200, 200])