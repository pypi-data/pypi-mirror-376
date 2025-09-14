from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import ec_url


class Converter(AdminConverterMixin, FiboaBaseConverter):
    variants = {
        2024: "https://inspire.lfrz.gv.at/009501/ds/inspire_schlaege_2024-2_polygon.gpkg.zip",
        2023: "https://inspire.lfrz.gv.at/009501/ds/inspire_schlaege_2023-2_polygon.gpkg.zip",
        2022: "https://inspire.lfrz.gv.at/009501/ds/inspire_schlaege_2022_polygon.gpkg.zip",
        2021: "https://inspire.lfrz.gv.at/009501/ds/inspire_schlaege_2021_polygon.gpkg.zip",
        2020: "https://inspire.lfrz.gv.at/009501/ds/inspire_schlaege_2020_polygon.gpkg.zip",
        2019: "https://inspire.lfrz.gv.at/009501/ds/inspire_schlaege_2019_polygon.gpkg.zip",
        2018: "https://inspire.lfrz.gv.at/009501/ds/inspire_schlaege_2018_polygon.gpkg.zip",
    }

    id = "at_crop"
    country = "AT"
    short_name = "Austria"
    title = "Field boundaries for Austria"
    description = """
    **Crop Field boundaries for Austria - INVEKOS Schläge Österreich 2021.**

    This layer includes all field uses recorded by the applicants, which serve as the basis for the funding process. A field
    is a contiguous area of a piece of land that is cultivated for a growing season with only one crop (field use type) and
    uniform management requirements or as a landscape element type in accordance with Annex 1 of the regulation of the responsible
    Federal Ministry with horizontal rules for the area of the Common Agricultural Policy (Horizontal CAP Regulation)
    StF: BGBl. II No. 100/2015 or is simply maintained in good agricultural and ecological condition in accordance with
    Art. 94 of Regulation (EU) No. 1306/2013 and is digitized in the GIS as a polygon or as a point.
    """
    providers = [
        {
            "name": "Agrarmarkt Austria",
            "url": "https://geometadatensuche.inspire.gv.at/metadatensuche/inspire/api/records/9db8a0c3-e92a-4df4-9d55-8210e326a7ed",
            "roles": ["producer", "licensor"],
        }
    ]
    license = "CC-BY-4.0"
    columns = {
        "GEO_ID": "id",
        "INSPIRE_ID": "inspire:id",
        "geometry": "geometry",
        "SNAR_CODE": "crop:code",
        "SNAR_BEZEICHNUNG": "crop:name",
        "SL_FLAECHE_BRUTTO_HA": "metrics:area",
        "GEOM_DATE_CREATED": "determination:datetime",
    }
    column_additions = {"crop:code_list": ec_url("at_2021.csv")}
    extensions = {
        "https://fiboa.org/inspire-extension/v0.3.0/schema.yaml",
        "https://fiboa.org/crop-extension/v0.2.0/schema.yaml",
    }
