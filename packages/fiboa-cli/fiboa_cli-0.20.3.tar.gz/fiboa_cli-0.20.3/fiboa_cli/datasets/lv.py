from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import EuroCropsConverterMixin, ec_url

count = 3000


class Converter(AdminConverterMixin, EuroCropsConverterMixin, FiboaBaseConverter):
    sources = {
        "https://karte.lad.gov.lv/arcgis/services/lauki/MapServer/WFSServer"
        f"?request=GetFeature&service=wfs&version=2.0.0&typeNames=Lauki&count={count}&startindex={count * i}": f"lv_{i}_{count}.xml"
        for i in range(
            500000 // count
        )  # TODO number should be dynamic, stop reading with 0 results
    }

    id = "lv"
    short_name = "Latvia"
    title = "Latvia Lauki Parcels"
    description = """
    Latvia offers parcel data on a [public map, available to any user](https://www.lad.gov.lv/lv/lauku-registra-dati).

    The land register is a geographic information system (GIS) that gathers information about agricultural land eligible for state and European Union support from direct support scheme payments or environmental, climate, and rural landscape improvement payments.

    The GIS of the field register contains a database of field blocks with interconnected spatial cartographic data and information of attributes subordinate to them: geographic attachment, identification numbers, and area information.

    Relevant datasets are: Country blocks (Lauku Bloki), Fields (Lauki), and Landscape elements.
    """
    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    providers = [
        {
            "name": "Rural Support Service Republic of Latvia (Lauku atbalsta dienests)",
            "url": "https://www.lad.gov.lv/lv/lauku-registra-dati",
            "roles": ["licensor", "producer"],
        }
    ]
    attribution = "Lauku atbalsta dienests"
    license = "CC-BY-SA-4.0"  # Not sure, taken from Eurocrops. It is "public" and free and "available to any user"
    columns = {
        "OBJECTID": "id",
        "PARCEL_ID": "parcel_id",
        "geometry": "geometry",
        "DATA_CHANGED_DATE": "determination:datetime",
        "area": "metrics:area",
        "crop:code_list": "crop:code_list",
        "PRODUCT_CODE": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
    }
    missing_schemas = {
        "properties": {
            "parcel_id": {
                "type": "uint64",
            }
        }
    }
    ec_mapping_csv = "lv_2021.csv"

    area_calculate_missing = True

    def migrate(self, gdf):
        gdf = super().migrate(gdf)

        original_name_mapping = {
            int(e["original_code"]): e["original_name"] for e in self.ec_mapping
        }
        name_mapping = {int(e["original_code"]): e["translated_name"] for e in self.ec_mapping}
        gdf["crop:code_list"] = ec_url("lv_2021.csv")
        gdf["crop:name"] = gdf["PRODUCT_CODE"].map(original_name_mapping)
        gdf["crop:name_en"] = gdf["PRODUCT_CODE"].map(name_mapping)
        return gdf
