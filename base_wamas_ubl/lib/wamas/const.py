# TODO: Find "clean" way to manage imports for both module & CLI contexts
try:
    from .structure import MappingDict
    from .wamas_grammar import (
        art,
        arte,
        artean,
        ausk,
        auskq,
        ausp,
        kretk,
        kretkq,
        kretp,
        kretpq,
        kst,
        kstaus,
        lst,
        watekq,
        watepq,
        weak,
        weakq,
        weap,
        weapq,
    )
except ImportError:
    from structure import MappingDict
    from wamas_grammar import (
        art,
        arte,
        artean,
        ausk,
        auskq,
        ausp,
        kretk,
        kretkq,
        kretp,
        kretpq,
        kst,
        kstaus,
        lst,
        watekq,
        watepq,
        weak,
        weakq,
        weap,
        weapq,
    )


##
# WAMAS CONST
##

DEFAULT_TIMEZONE = "Europe/Zurich"
SYSTEM_WAMAS = "WAMAS"
SYSTEM_ERP = "ODOO"


##
# WAMAS FORMAT SPECS
##

TELEGRAM_HEADER_GRAMMAR = {
    "Telheader_Quelle": 10,
    "Telheader_Ziel": 10,
    "Telheader_TelSeq": 6,
    "Telheader_AnlZeit": 14,
    "Satzart": 9,
}

##
# WAMAS GRAMMAR
##


LST_TELEGRAM_TYPE_SUPPORT_D2W = [
    "ART",
    "ARTE",
    "ARTEAN",
    "WEAK",
    "WEAP",
    "AUSK",
    "AUSP",
    "KRETK",
    "KRETP",
    "KST",
    "KSTAUS",
    "LST",
]


DICT_WAMAS_GRAMMAR = {
    "art": art.grammar,
    "arte": arte.grammar,
    "artean": artean.grammar,
    "ausk": ausk.grammar,
    "ausp": ausp.grammar,
    "kretk": kretk.grammar,
    "kretp": kretp.grammar,
    "weak": weak.grammar,
    "weap": weap.grammar,
    "auskq": auskq.grammar,
    "kretkq": kretkq.grammar,
    "kretpq": kretpq.grammar,
    "kst": kst.grammar,
    "kstaus": kstaus.grammar,
    "lst": lst.grammar,
    "watekq": watekq.grammar,
    "watepq": watepq.grammar,
    "weakq": weakq.grammar,
    "weapq": weapq.grammar,
}


##
# WAMAS TO UBL
##


LST_TELEGRAM_TYPE_SUPPORT_W2D = [
    "ART",
    "ARTE",
    "ARTEAN",
    "AUSK",
    "AUSKQ",
    "AUSP",
    "KRETK",
    "KRETKQ",
    "KRETP",
    "KRETPQ",
    "KST",
    "KSTAUS",
    "LST",
    "WATEKQ",
    "WATEPQ",
    "WEAK",
    "WEAKQ",
    "WEAP",
    "WEAPQ",
]


LST_TELEGRAM_TYPE_IGNORE_W2D = ["AUSPQ", "TOURQ", "TAUSPQ"]


DICT_TUPLE_KEY_RECEPTION = {
    ("WEAKQ", "WEAPQ"): (
        "ubl_template/reception.xml",
        ("WEAKQ", "IvWevk_WevId_WevNr"),
        ("WEAPQ", "IvWevp_WevId_WevNr"),
    ),
    ("KRETKQ", "KRETPQ"): (
        "ubl_template/return.xml",
        ("KRETKQ", "IvKretk_KretId_KretNr"),
        ("KRETPQ", "IvKretp_KretId_KretNr"),
    ),
}


DICT_TUPLE_KEY_PICKING = {
    ("AUSKQ", "WATEKQ", "WATEPQ"): "ubl_template/picking.xml",
}


DICT_FLOAT_FIELD = {
    "IvWevp_LiefMngs_Mng": (12, 3),
    "IvKretp_AnmMngs_Mng": (12, 3),
    "Mngs_Mng": (12, 3),
    "IvTek_GesGew": (12, 3),
}


##
# CONVERT UNIT CODE
##

LST_FIELD_UNIT_CODE = [
    "HostEinheit",
    "Art_Anzeige_Einheit",
    "Arte_Einheit",
    "ArtEan_EST_Einheit",
]


MAPPING_UNITCODE_WAMAS_TO_UBL = {
    # DespatchLine/DeliveredQuantity[unitCode]
    # https://docs.peppol.eu/poacc/upgrade-3/codelist/UNECERec20/
    "unitCode": MappingDict(
        {
            "BOT": "XBQ",  # plastic bottle
            "BOUT": "C62",  # Unit
            "BOITE": "XBX",  # box
            "LITRE": "LTR",  # litre
            "PET": "XBO",  # glass bottle
            "TETRA": "X4B",  # tetra pack
            "": False,  # undefined,
        }
    )
}


MAPPING_UNITCODE_UBL_TO_WAMAS = {"unitCode": MappingDict()}
for key, value in MAPPING_UNITCODE_WAMAS_TO_UBL["unitCode"].items():
    MAPPING_UNITCODE_UBL_TO_WAMAS["unitCode"][value] = key


##
# CHECK WAMAS
##

DICT_DETECT_WAMAS_TYPE = {
    ("WEAK", "WEAP"): "Reception",
    ("WEAKQ", "WEAPQ"): "Reception",
    ("AUSK", "AUSP"): "Picking",
    ("AUSKQ", "WATEKQ", "WATEPQ"): "Picking",
    ("KRETK", "KRETP"): "Return",
    ("KRETKQ", "KRETPQ"): "Return",
    ("KSTAUS",): "Customer Delivery Preference",
    ("LST",): "Supplier",
    ("ART",): "Product",
    ("ARTE",): "Product Packaging",
    ("ARTEAN",): "Product EAN",
    ("ART", "ARTE"): "Product and Product Packaging",
    ("ART", "ARTEAN"): "Product and Product EAN",
    ("ARTE", "ARTEAN"): "Product Packaging and Product EAN",
    ("ART", "ARTE", "ARTEAN"): "Product, Product Packaging and Product EAN",
    ("KST",): "Customer",
}
# WAMAS TO WAMAS
##


LST_VALID_TELEGRAM_IN = [
    "AUSK",
    "AUSP",
    "KRETK",
    "KRETP",
    "WATEK",
    "WATEP",
    "WEAK",
    "WEAP",
]


DICT_CONVERT_WAMAS_TYPE = {
    "AUSK": ["AUSKQ", "WATEKQ"],
    "AUSP": ["WATEPQ"],
    "KRETK": ["KRETKQ"],
    "KRETP": ["KRETPQ"],
    "WEAK": ["WEAKQ"],
    "WEAP": ["WEAPQ"],
}


DICT_WAMAS_GRAMMAR_OUT = {
    "auskq": auskq.grammar_convert,
    "kretkq": kretkq.grammar_convert,
    "kretpq": kretpq.grammar_convert,
    "watekq": watekq.grammar_convert,
    "watepq": watepq.grammar_convert,
    "weakq": weakq.grammar_convert,
    "weapq": weapq.grammar_convert,
}


DICT_PARENT_KEY = {"WATEKQ": ["IvTek_TeId"]}


DICT_CHILD_KEY = {"WATEPQ": {"IvTep_TeId": "IvTek_TeId"}}
