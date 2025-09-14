import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import ec_url, load_ec_mapping


class Converter(AdminConverterMixin, FiboaBaseConverter):
    sources = {
        "http://epub.sjv.se/inspire/inspire/wfs?SERVICE=WFS%20&REQUEST=GetFeature%20&VERSION=1.0.0%20&TYPENAMES=inspire:arslager_skifte%20&outputFormat=shape-zip%20&CQL_FILTER=arslager=%272023%27%20%20and%20geom%20is%20not%20null%20&format_options=CHARSET:UTF-8": "se2023.zip"
    }
    id = "se"
    short_name = "Sweden"
    title = "Swedish Crop Fields (Jordbruksskiften)"
    description = """
    A crop field (Jordbruksskift) is a contiguous area of land within a block where a farmer grows a crop or otherwise manages the land.
    To receive compensation for agricultural support (EU support), farmers apply for support from the
    Swedish Agency for Agriculture via a SAM application. The data set contains parcels where the area
    applied for and the area decided on are the same. The data is published at the end of a year.
    """
    providers = [
        {
            "name": "Jordbruksverket (The Swedish Board of Agriculture)",
            "url": "https://jordbruksverket.se/",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "Jordbruksverket"
    license = "CC-0"  # "Open Data"
    columns = {
        "geometry": "geometry",
        "id": "id",
        "faststalld": "metrics:area",
        "grdkod_mar": "crop:code",
        "crop:name": "crop:name",
        "arslager": "determination:datetime",
    }
    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    column_additions = {"crop:code_list": ec_url("se_2021.csv")}
    column_migrations = {
        # Make year (1st January) from column "arslager"
        "arslager": lambda col: pd.to_datetime(col, format="%Y")
    }

    def migrate(self, gdf):
        """
        Perform migration of the GeoDataFrame (migrate step).
        """
        ec_mapping = load_ec_mapping("se_2021.csv")
        original_name_mapping = {int(e["original_code"]): e["original_name"] for e in ec_mapping}

        gdf["id"] = gdf["blockid"] + "_" + gdf["skiftesbet"]
        gdf["crop:name"] = gdf["grdkod_mar"].map(original_name_mapping)
        return gdf
