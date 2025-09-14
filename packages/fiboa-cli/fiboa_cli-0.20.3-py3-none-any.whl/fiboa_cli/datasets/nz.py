import pandas as pd
from vecorel_cli.vecorel.extensions import ADMIN_DIVISION

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.data import read_data_csv


class NZCropConverter(FiboaBaseConverter):
    data_access = "Download manually from https://data.mfe.govt.nz/layer/105407-irrigated-land-area-raw-2020-update/"

    id = "nz"
    short_name = "New Zealand"
    title = "Irrigated land area"
    description = """
This dataset covers Irrigated Land. Adapted by Ministry for the Environment and Statistics
New Zealand to provide for environmental reporting transparency

The spatial data covers all mainland regions of New Zealand, with the exception of Nelson, which is not believed to
contain significant irrigated areas. The spatial dataset is an update of the national dataset that was first
created in 2017. The current update has incorporated data from the 2019 – 2020 irrigation season.
"""

    providers = [
        {
            "name": "NZ Ministry for the environment",
            "url": "https://environment.govt.nz/",
            "roles": ["producer"],
        },
        {
            "name": "Aqualinc Research Limited",
            "url": "https://environment.govt.nz/publications/national-irrigated-land-spatial-dataset-2020-update",
            "roles": ["licensor"],
        },
    ]
    license = "CC-BY-4.0"
    extensions = {ADMIN_DIVISION}
    index_as_id = True
    columns = {
        "id": "id",
        "geometry": "geometry",
        "type": "type",
        "area_ha": "metrics:area",
        "yearmapped": "determination:datetime",
        "Region": "admin:subdivision_code",
    }
    column_migrations = {"yearmapped": lambda col: pd.to_datetime(col, format="%Y")}
    column_additions = {
        "admin:country_code": "NZ",
    }
    missing_schemas = {
        "properties": {
            "type": {
                "type": "string",
            },
        }
    }

    def migrate(self, gdf):
        # MAP back; https://www.iso.org/obp/ui/#iso:code:3166:NZ
        rows = read_data_csv("nz_region_codes.csv")
        mapping = {row["Subdivision name"]: row["3166-2 code"][len("NZ-") :] for row in rows}
        gdf["Region"] = gdf["Region"].map(mapping)
        return gdf
