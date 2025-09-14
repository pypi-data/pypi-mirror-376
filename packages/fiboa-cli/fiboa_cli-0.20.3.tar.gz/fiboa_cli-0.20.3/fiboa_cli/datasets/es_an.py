from loguru import logger

from .commons.data import read_data_csv
from .es import ESBaseConverter


class ANConverter(ESBaseConverter):
    variants = {
        "2024": "https://www.juntadeandalucia.es/ssdigitales/festa/agriculturapescaaguaydesarrollorural/2024/SP24_REC_{code}.zip",
        "2023": "https://www.juntadeandalucia.es/ssdigitales/festa/agriculturapescaaguaydesarrollorural/2023/SP23_REC_{code}.zip",
        "2022": "https://www.juntadeandalucia.es/export/drupaljda/01_SP22_REC_PROV_{code}.zip",
        "2021": "https://www.juntadeandalucia.es/export/drupaljda/V1_01_SP21_REC_PROV_{code}.zip",
        "2020": "https://www.juntadeandalucia.es/export/drupaljda/SP20_REC_PROV_{filename}.zip",
        "2019": "https://www.juntadeandalucia.es/export/drupaljda/SIGPAC2019_REC_PROV_{filename}.zip",
        "2018": "https://www.juntadeandalucia.es/export/drupaljda/SIGPAC2018_REC_PROV_{filename}.zip",
        "2017": "https://www.juntadeandalucia.es/export/drupaljda/sp17_rec_{code}.zip",
    }

    id = "es_an"
    short_name = "Spain Andalusia"
    title = "Spain Andalusia Crop fields"
    description = """
    SIGPAC is the Geographic Information System for the Identification of Agricultural Plots ,
    created through collaboration between the Spanish Agricultural Guarantee Fund (FEGA) and
    the different Autonomous Communities, within the scope of their territories, as an element
    of the Integrated Management and Control System of the direct aid regimes. It has the character
    of a public register of administrative profile, and contains updated information on the
    plots that may benefit from community aid related to the surface area, providing graphic
    support for these and their subdivisions (ENCLOSURES) with defined agricultural uses or
    developments.
    """
    providers = [
        {
            "name": "Junta de Andalucía",
            "url": "https://www.juntadeandalucia.es/",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "©Junta de Andalucía"
    # The end user is required to be informed, ..., that the cartography and geographic information is available free of charge on the website of the Ministry of Agriculture, Fisheries and Rural Development.
    license = {
        # CC-SA-BY-ND
        "title": "Pursuant to Law 37/2007 of 16 November on the reuse of public sector information and Law 3/2013 of 24 July approving the Statistical and Cartographic Plan of Andalusia 2013-2017, the geographic information of SIGPAC is made available to the public.",
        "href": "https://www.juntadeandalucia.es/organismos/agriculturapescaaguaydesarrollorural/servicios/sigpac/visor/paginas/sigpac-descarga-informacion-geografica-shapes-provincias.html#toc-condiciones-de-uso-para-la-licencia-de-uso-comercial",
        "type": "text/html",
        "rel": "license",
    }
    columns = {
        "geometry": "geometry",
        "ID_RECINTO": "id",
        "CD_PROV": "admin_province_code",
        "CD_MUN": "admin_municipality_code",
        "NU_AREA": "metrics:area",
        "CD_USO": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
    }

    area_is_in_ha = False
    area_calculate_missing = True

    column_additions = ESBaseConverter.column_additions | {
        "determination:datetime": "2024-03-28T00:00:00Z",
    }

    missing_schemas = {
        "properties": {
            "admin_province_code": {"type": "string"},
            "admin_municipality_code": {"type": "string"},
        }
    }

    def get_urls(self):
        if not self.variant:
            self.variant = next(iter(self.variants))
            logger.warning(f"Choosing first year {self.variant}")
        else:
            assert self.variant in self.variants, f"Wrong year {self.variant}"

        url = self.variants[self.variant]
        data = read_data_csv("es_an_prv.csv")

        def fname(line):
            return f"SP{int(self.variant) % 100}_REC_{line['code']}.shp"

        return {url.format(**line): [fname(line)] for line in data}
