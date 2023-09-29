from geotools import geotools

gt = geotools.GeoEngine()
pt = [38.10921437,-76.59772843]
try:
	data = gt.get_elevation(pt)
	print("Elevation is: "+str(data))
except Exception as e:
	print(e)

try:
	data = gt.get_fao_soil_type(pt)
	print("Soil Type is: "+data)
except geotools.ApiException as e:
	print(e)
