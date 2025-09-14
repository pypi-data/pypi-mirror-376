import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import ec_url


class Converter(AdminConverterMixin, FiboaBaseConverter):
    sources = "https://download.inspire.ruokavirasto-awsa.com/data/2023/LandUse.ExistingLandUse.GSAAAgriculturalParcel.gpkg"
    id = "fi"
    short_name = "Finland"
    title = "Finnish Crop Fields (Maatalousmaa)"
    description = """
    The Finnish Food Authority (FFA) since 2020 produces spatial data sets,
    more specifically in this context the "Field parcel register" and "Agricultural parcel containing spatial data".
    A set called "Agricultural land: arable land, permanent grassland or permanent crop (land use)".
    """
    providers = [
        {
            "name": "Finnish Food Authority",
            "url": "https://www.ruokavirasto.fi/en/about-us/open-information/spatial-data-sets/",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "Finnish Food Authority"
    license = "CC-BY-4.0"
    columns = {
        "geometry": "geometry",
        "PERUSLOHKOTUNNUS": "id",
        "LOHKONUMERO": "block_id",
        "area": "metrics:area",
        "VUOSI": "determination:datetime",
        "KASVIKOODI": "crop:code",
        "KASVIKOODI_SELITE_FI": "crop:name",
    }
    column_migrations = {
        # Make year (1st January) from column "VUOSI"
        "VUOSI": lambda col: pd.to_datetime(col, format="%Y"),
    }
    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    column_additions = {"crop:code_list": ec_url("fi_2020.csv")}

    area_is_in_ha = False
    area_calculate_missing = True

    missing_schemas = {
        "properties": {
            "block_id": {"type": "int64"},
        }
    }
