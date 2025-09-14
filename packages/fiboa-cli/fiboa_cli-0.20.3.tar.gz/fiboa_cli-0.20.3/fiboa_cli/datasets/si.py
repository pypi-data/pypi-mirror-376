from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import ec_url


class Converter(AdminConverterMixin, FiboaBaseConverter):
    sources = {"https://rkg.gov.si/razno/portal_analysis/KMRS_2023.rar": ["KMRS_2023.shp"]}
    id = "si"
    short_name = "Slovenia"
    title = "Slovenia Crop Fields"
    description = """
    The Slovenian government provides slightly different, relevant open data sets called GERK, KMRS, RABA and EKRZ.
    This converter uses the KRMS dataset, which includes CAP applications of the last year and discerns
    around 150 different crop categories.
    """
    providers = [
        {
            "name": "Ministry of Agriculture, Forestry and Food (Ministrstvo za kmetijstvo, gozdarstvo in prehrano)",
            "url": "https://www.gov.si/drzavni-organi/ministrstva/ministrstvo-za-kmetijstvo-gozdarstvo-in-prehrano/",
            "roles": ["producer", "licensor"],
        }
    ]

    license = {
        "title": "Javno dostopni podatki: Publicly available data",
        "href": "https://rkg.gov.si/vstop/",
        "type": "text/html",
        "rel": "license",
    }

    columns = {
        "geometry": "geometry",
        "ID": "id",
        "GERK_PID": "block_id",
        "AREA": "metrics:area",
        "SIFRA_KMRS": "crop:code",
        "RASTLINA": "crop:name",
        "CROP_LAT_E": "crop:name_en",
    }
    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    column_additions = {"crop:code_list": ec_url("si_2021.csv")}
    column_migrations = {"geometry": lambda col: col.make_valid()}
    area_is_in_ha = False
    missing_schemas = {
        "properties": {
            "block_id": {"type": "uint64"},
        }
    }
