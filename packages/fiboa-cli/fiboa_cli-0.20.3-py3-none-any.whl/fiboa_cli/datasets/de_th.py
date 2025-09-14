import re

import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter


class Converter(AdminConverterMixin, FiboaBaseConverter):
    sources = "https://www.geoproxy.geoportal-th.de/download-service/opendata/agrar/DGK_Thue.zip"

    id = "de_th"
    admin_subdivision_code = "TH"
    short_name = "Germany, Thuringia"
    title = "Field boundaries for Thuringia, Germany"
    description = """
    For use in the application procedure of the Integrated Administration and Control System (IACS), digital data layers are required that represent the current situation of agricultural use with the required accuracy. The field block is a contiguous agricultural area of one or more farmers surrounded by permanent boundaries. The field block thus contains information on the geographical location of the outer boundaries of the agricultural area. Reference parcels are uniquely numbered throughout Germany (Feldblockident - FBI). They also have a field block size (maximum eligible area) and a land use category.

    The following field block types exist:

    - Utilized agricultural area (UAA)
    - Landscape elements (LE)
    - Special use areas (SF)
    - Forest areas (FF)

    The field blocks are classified separately according to the main land uses of arable land (`AL`), grassland (`GL`), permanent crops (`DA`, `OB`, `WB`), including agroforestry systems with an approved utilization concept and according to the BNK for no "agricultural land" (`NW`, `EF` and `PK`) and others.

    Landscape elements (LE) are considered part of the eligible agricultural area under defined conditions. In Thuringia, these permanent conditional features are designated as a separate field block (FB) and are therefore part of the Thuringian area reference system (field block reference). They must have a clear reference to an UAA (agricultural land), i.e. they are located within an arable, permanent grassland or permanent crop area or border directly on it.

    To produce the DGK-Lw, (official) orthophotos from the Thuringian Land Registry and Surveying Administration (TLBG) and orthophotos from the TLLLR's own aerial surveys are interpreted. The origin of this image data is 50% of the state area each year, so that up-to-date image data is available for the entire Thuringian state area every year.
    """

    providers = [
        {
            "name": "Thüringer Landesamt für Landwirtschaft und Ländlichen Raum",
            "url": "https://geomis.geoportal-th.de/geonetwork/srv/ger/catalog.search#/metadata/D872F2D6-60BC-11D6-B67D-00E0290F5BA0",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "© GDI-Th"
    license = "dl-de/by-2-0"

    extensions = {"https://fiboa.org/flik-extension/v0.2.0/schema.yaml"}

    columns = {
        "geometry": "geometry",
        "BEZUGSJAHR": "valid_year",
        "FBI": "flik",
        "FBI_KURZ": "id",
        "FB_FLAECHE": "metrics:area",
        "FBI_VJ": "flik_last_year",
        "FB_FL_VJ": "area_last_year",
        "TK10": "tk10",
        "AFO": "afo",
        # Don't add LF, all values are 'LF' after the filter below
        #   'LF': 'lf',
        "BNK": "bnk",
        "KOND_LE": "kond_le",
        "AENDERUNG": "change",
        "GEO_UPDAT": "determination:datetime",
    }

    delim = re.compile(r"\s*,\s*")
    column_migrations = {
        "AFO": lambda column: column.map({"J": True}).fillna(value=False).astype(bool),
        "KOND_LE": lambda column: column.map({"J": True}).fillna(value=False).astype(bool),
        "AENDERUNG": lambda column: column.map(
            {"Geaendert": True, "Unveraendert": False, "Neu": None}
        ),
        "FBI_VJ": lambda column: column.str.split(Converter.delim, regex=True),
    }

    def migrate(self, gdf):
        col = "GEO_UPDAT"
        gdf[col] = pd.to_datetime(gdf[col], format="%d.%m.%Y", utc=True)
        return gdf

    column_filters = {"LF": lambda col: col == "LF"}

    # Schemas for the fields that are not defined in fiboa
    # Keys must be the values from the COLUMNS dict, not the keys
    missing_schemas = {
        "required": ["valid_year", "area_last_year", "tk10", "bnk"],
        "properties": {
            "valid_year": {
                # could also be uint16 or string
                "type": "int16"
            },
            "flik_last_year": {
                "type": "array",
                "items": {
                    # as defined in the flik extension schema
                    "type": "string",
                    "minLength": 16,
                    "maxLength": 16,
                    "pattern": "^[A-Z]{2}[A-Z0-9]{2}[A-Z0-9]{2}[A-Z0-9]{10}$",
                },
            },
            "area_last_year": {
                # as define in the area schema
                "type": "float",
                "exclusiveMinimum": 0,
                "maximum": 100000,
            },
            "tk10": {"type": "string"},
            "afo": {"type": "boolean"},
            "bnk": {"type": "string"},
            "kond_le": {"type": "boolean"},
            "change": {"type": "boolean"},
        },
    }
