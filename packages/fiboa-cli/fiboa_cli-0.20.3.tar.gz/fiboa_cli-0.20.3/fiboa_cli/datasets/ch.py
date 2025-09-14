import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter


class Converter(AdminConverterMixin, FiboaBaseConverter):
    sources = None
    data_access = """
    Data must be obtained from the Swiss open data portal at https://www.geodienste.ch/services/lwb_nutzungsflaechen .

    One can filter on "Verfügbarkeit" == "Frei erhältlich" to select only the open data.
    That leaves out Cantons AR, NW, OW, VD and LI as on this date (2014-11-12).
    The downloaded data can be shared with a open_by license. See https://opendata.swiss/de/terms-of-use .

    Use the `-i` CLI parameter to provide the data source.
    Download the Open data response to a local gpkg file (use `.gpkg` as file extension).

    fiboa convert ch -o swiss.parquet -i lwb_nutzungsflaechen_lv95/geopackage/lwb_nutzungsflaechen_v2_0_lv95.gpkg
    """
    id = "ch"
    short_name = "Switzerland"
    title = "Field boundaries for Switzerland"
    description = "The cropfields of Switzerland (Nutzungsflächen) are published per administrative subdivision called Canton."
    providers = [
        {
            "name": "Konferenz der kantonalen Geoinformations- und Katasterstellen",
            "url": "https://www.kgk-cgc.ch/",
            "roles": ["producer", "licensor"],
        }
    ]
    index_as_id = True
    license = {
        "title": "opendata.swiss terms of use",
        "href": "https://opendata.swiss/en/terms-of-use",
        "type": "text/html",
        "rel": "license",
    }
    columns = {
        "geometry": "geometry",
        "id": "id",
        "flaeche_m2": "metrics:area",
        "kanton": "admin:subdivision_code",
        "nutzung": "crop_name",
        "bezugsjahr": "determination:datetime",
    }
    column_filters = {
        "ist_ueberlagernd": lambda col: col == False,  # noqa: E712
    }
    area_is_in_ha = False
    area_calculate_missing = True
    column_migrations = {
        "bezugsjahr": lambda col: pd.to_datetime(col, format="%Y"),
    }
    missing_schemas = {
        "properties": {
            "crop_name": {"type": "string"},
        }
    }
