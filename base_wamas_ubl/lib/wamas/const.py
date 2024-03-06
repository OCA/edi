from .wamas_grammar import (
    art,
    arte,
    artean,
    ausk,
    auskq,
    ausp,
    bkorr,
    kretk,
    kretkq,
    kretp,
    kretpq,
    kst,
    kstaus,
    lba,
    lbabq,
    lbaeq,
    lbamq,
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

DICT_DETECT_WAMAS_TYPE = {
    "ART": "Product",
    "AUSK": "Picking",
    "AUSKQ": "PickingResponse",
    "KRETK": "Return",
    "KRETKQ": "ReturnResponse",
    "KST": "Customer",
    "LST": "Supplier",
    "WATEKQ": "PickingResponse",
    "WEAK": "Reception",
    "WEAKQ": "ReceptionResponse",
    "BKORR": "InventoryCorrection",
    "LBABQ": "InventoryResponse",
    "LBAMQ": "InventoryResponse",
}

##
# WAMAS GRAMMAR
##

DICT_WAMAS_GRAMMAR = {
    "ART": art.grammar,
    "ARTE": arte.grammar,
    "ARTEAN": artean.grammar,
    "AUSK": ausk.grammar,
    "AUSP": ausp.grammar,
    "BKORR": bkorr.grammar,
    "KRETK": kretk.grammar,
    "KRETP": kretp.grammar,
    "WEAK": weak.grammar,
    "WEAP": weap.grammar,
    "AUSKQ": auskq.grammar,
    "KRETKQ": kretkq.grammar,
    "KRETPQ": kretpq.grammar,
    "KST": kst.grammar,
    "KSTAUS": kstaus.grammar,
    "LBA": lba.grammar,
    "LBABQ": lbabq.grammar,
    "LBAEQ": lbaeq.grammar,
    "LBAMQ": lbamq.grammar,
    "LST": lst.grammar,
    "WATEKQ": watekq.grammar,
    "WATEPQ": watepq.grammar,
    "WEAKQ": weakq.grammar,
    "WEAPQ": weapq.grammar,
}

##
# WAMAS TO UBL
##

LST_TELEGRAM_TYPE_IGNORE_W2D = ["AUSPQ", "TOURQ", "TAUSPQ"]

DICT_UBL_TEMPLATE = {
    "ReceptionResponse": "ubl_template/reception.xml",
    "ReturnResponse": "ubl_template/return.xml",
    "PickingResponse": "ubl_template/picking.xml",
}

##
# DICT TO WAMAS
##

SUPPORTED_DICT_TO_WAMAS = {
    "Product": ["ART"],  # "ARTE", "ARTEAN"],
    "Packaging": ["ARTE"],
    "Barcode": ["ARTEAN"],
    "Customer": ["KST"],  # "KSTAUS"],
    "CustomerDeliveryPreferences": ["KSTAUS"],
    "Supplier": ["LST"],
}

##
# UBL TO WAMAS
##

SUPPORTED_UBL_TO_WAMAS = {
    "Reception": ["WEAK", "WEAP"],
    "Picking": ["AUSK", "AUSP"],
    "Return": ["KRETK", "KRETP"],
}

LST_TELEGRAM_TYPE_SUPPORT_D2W = [
    "ART",
    "ARTE",
    "ARTEAN",
    "WEAK",
    "WEAP",
    "AUSK",
    "AUSP",
    "BKORR",
    "KRETK",
    "KRETP",
    "KST",
    "KSTAUS",
    "LBA",
    "LBABQ",
    "LBAMQ",
    "LBAEQ",
    "LST",
]


##
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


DICT_PARENT_KEY = {"WATEKQ": ["IvTek_TeId"]}


DICT_CHILD_KEY = {"WATEPQ": {"IvTep_TeId": "IvTek_TeId"}}
