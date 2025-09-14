from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter


class Converter(AdminConverterMixin, FiboaBaseConverter):
    sources = "https://service.gdi-sh.de/SH_OpenGBD/feeds/Atom_SH_Feldblockfinder_OpenGBD/data/Feldbloecke_2024_GPKG.zip"
    id = "de_sh"
    admin_subdivision_code = "SH"
    short_name = "Germany, Schleswig-Holstein"
    title = "Field boundaries for Schleswig-Holstein (SH), Germany"
    description = """A field block (German: "Feldblock") is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated by one or more farmers with one or more crops, is fully or partially set aside or is fully or partially taken out of production."""
    providers = [
        {
            "name": "Land Schleswig-Holstein",
            "url": "https://sh-mis.gdi-sh.de/catalog/#/datasets/iso/21f67269-780f-4f3c-8f66-03dde27acfe7",
            "roles": ["producer", "licensor"],
        }
    ]
    license = "dl-de/zero-2-0"
    extensions = {"https://fiboa.org/flik-extension/v0.2.0/schema.yaml"}
    columns = {
        "geometry": "geometry",
        "fachguelti": "determination:datetime",
        "FLIK": ["flik", "id"],
        "Flaeche": "metrics:area",
        "HBN": "hbn",
    }
    missing_schemas = {"properties": {"hbn": {"type": "string"}}}
