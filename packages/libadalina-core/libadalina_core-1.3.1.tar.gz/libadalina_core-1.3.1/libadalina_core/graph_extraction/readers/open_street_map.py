import os.path
from shapely.io import from_wkt

from libadalina_core.exceptions.input_file_exception import InputFileException
from libadalina_core.graph_extraction.readers.reader import MapReader, MandatoryColumns, OneWay, RoadTypes
import geopandas as gpd
import pandas as pd

class OpenStreetMapReader(MapReader):
    """
    A class to read OpenStreetMap (OSM) data files and convert them into a GeoDataFrame with standardized columns.
    """

    CRS = 4326 # OSM data are exported in WGS84


    def read(self, file_path: str) -> gpd.GeoDataFrame:
        """
        Read an OSM data file and return a GeoDataFrame with the required columns.
        Accepts CSV, Shapefile, and GeoPackage formats.

        Parameters
        ----------
        file_path : str
            The path to the OSM data file. Must contain 'osm_id', 'name', 'oneway', and 'geometry' columns.

        Returns
        -------
        gpd.GeoDataFrame
            A GeoDataFrame containing only the mandatory columns with standardized names.
        """
        if file_path.endswith('.csv'):
            return self.read_csv(file_path)
        elif file_path.endswith('.shp'):
            return self.read_shp(file_path)
        elif file_path.endswith('.gpkg'):
            return self.read_gpkg(file_path)

        raise InputFileException(f'no reader found for file {file_path}')

    def read_csv(self, file_path: str) -> gpd.GeoDataFrame:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'file {file_path} does not exist')

        df = pd.read_csv(file_path, sep=',')
        return self.from_dataframe(df)

    def read_shp(self, file_path: str) -> gpd.GeoDataFrame:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'file {file_path} does not exist')

        return self._map_columns(gpd.read_file(file_path))
    
    def read_gpkg(self, file_path: str) -> gpd.GeoDataFrame:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'file {file_path} does not exist')

        layers = gpd.list_layers(file_path)
        layer_name = layers.loc[0, 'name']

        return self._map_columns(gpd.read_file(file_path, layer=layer_name))

    def from_dataframe(self, df: pd.DataFrame) -> gpd.GeoDataFrame:
        """
        Convert a pandas DataFrame of OSM data to a GeoDataFrame with the required columns.

        Parameters
        ----------
        df : pd.DataFrame
            The OSM data as a pandas DataFrame. Must contain 'osm_id', 'name', 'oneway', and 'geometry' columns.

        Returns
        -------
        gpd.GeoDataFrame
            A GeoDataFrame containing only the mandatory columns with standardized names.
        """
        df.loc[:, 'geometry'] = df['geometry'].apply(from_wkt)
        return self._map_columns(gpd.GeoDataFrame(df, geometry='geometry', crs=self.CRS))

    def _map_columns(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        gdf['name'] = gdf['name'].fillna('')
        gdf = self._filter_roads(gdf)
        gdf = self.map_and_reduce(gdf, {
            MandatoryColumns.id: 'osm_id',
            MandatoryColumns.road_name: 'name',
            MandatoryColumns.oneway: 'oneway'
        })
        
        oneway_mapping = {
            'F': OneWay.Forward.value,
            'T': OneWay.Backward.value,
            'B': OneWay.Both.value
        }
        gdf.loc[:, MandatoryColumns.oneway.value] = gdf[MandatoryColumns.oneway.value].map(oneway_mapping).fillna(
            OneWay.Both.value)
        return gdf

    def _filter_roads(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Filter roads based on the specified road type.
        Road types of OSM are defined in https://download.geofabrik.de/osm-data-in-gis-formats-free.pdf
        Parameters
        ----------
        gdf : geopandas.GeoDataFrame
            The input GeoDataFrame containing road data with a 'code' column representing road types.

        Returns
        -------
        geopandas.GeoDataFrame
            A GeoDataFrame containing only the roads that match the specified road type.
        """
        if self._road_types == RoadTypes.CAR_ONLY:
            return gdf[(
                ((gdf['code'] >= 5110) & (gdf['code'] <= 5119)) |
                ((gdf['code'] >= 5130) & (gdf['code'] <= 5139)) |
                ((gdf['code'] >= 5121) & (gdf['code'] <= 5122))
            )]
        elif self._road_types == RoadTypes.MAIN_ROADS:
            return gdf[(
                    ((gdf['code'] >= 5110) & (gdf['code'] <= 5119)) |
                    ((gdf['code'] >= 5130) & (gdf['code'] <= 5139))
            )]
        else:
            return gdf
