from collections import OrderedDict

grammar = OrderedDict(
    {
        "Telheader_Quelle": {
            "type": "str",
            "length": 10,
            "dp": False,
            "ubl_path": False,
            "df_val": False,
            "df_func": "get_source",
        },
        "Telheader_Ziel": {
            "type": "str",
            "length": 10,
            "dp": False,
            "ubl_path": False,
            "df_val": False,
            "df_func": "get_destination",
        },
        "Telheader_TelSeq": {
            "type": "int",
            "length": 6,
            "dp": False,
            "df_val": False,
            "df_func": "get_sequence_number",
        },
        "Telheader_AnlZeit": {
            "type": "datetime",
            "length": 14,
            "dp": False,
            "df_val": False,
            "df_func": "get_current_datetime",
        },
        "Satzart": {
            "type": "str",
            "length": 9,
            "dp": False,
            "df_val": "KST000052",
            "df_func": False,
        },
        "Kst_Mand": {
            "type": "str",
            "length": 3,
            "dp": False,
            "dict_key": False,
            "df_val": "000",
            "df_func": False,
        },
        "Kst_KuNr": {
            "type": "str",
            "length": 13,
            "dp": False,
            "dict_key": "ref",
            "df_val": False,
            "df_func": False,
        },
        "Kst_LiefAdrs_Name": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": "delivery_name",
            "df_val": False,
            "df_func": False,
        },
        "Kst_LiefAdrs_Name2": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_LiefAdrs_Name3": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_LiefAdrs_Name4": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_LiefAdrs_Anrede": {
            "type": "str",
            "length": 15,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_LiefAdrs_Adr": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": "delivery_street",
            "df_val": False,
            "df_func": False,
        },
        "Kst_LiefAdrs_Adr2": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": "delivery_street2",
            "df_val": False,
            "df_func": False,
        },
        "Kst_LiefAdrs_PLZ": {
            "type": "str",
            "length": 10,
            "dp": False,
            "dict_key": "delivery_zip",
            "df_val": False,
            "df_func": False,
        },
        "Kst_LiefAdrs_Ort": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": "delivery_city",
            "df_val": False,
            "df_func": False,
        },
        "Kst_LiefAdrs_OrtTeil": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": "delivery_state",
            "df_func": False,
        },
        "Kst_LiefAdrs_Land": {
            "type": "str",
            "length": 4,
            "dp": False,
            "dict_key": "delivery_country_code",
            "df_val": False,
            "df_func": False,
        },
        "Kst_LiefAdrs_Tel": {
            "type": "str",
            "length": 35,
            "dp": False,
            "dict_key": "delivery_phone",
            "df_val": False,
            "df_func": False,
        },
        "Kst_LiefAdrs_Fax": {
            "type": "str",
            "length": 35,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_LiefAdrs_Email": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": "delivery_email",
            "df_val": False,
            "df_func": False,
        },
        "Kst_LiefAdrs_WWW": {
            "type": "str",
            "length": 35,
            "dp": False,
            "dict_key": "delivery_website",
            "df_val": False,
            "df_func": False,
        },
        "Kst_LiefAdrs_ILN": {
            "type": "str",
            "length": 13,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_Name": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": "invoicing_name",
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_Name2": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_Name3": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_Name4": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_Anrede": {
            "type": "str",
            "length": 15,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_Adr": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": "invoicing_street",
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_Adr2": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": "invoicing_street2",
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_PLZ": {
            "type": "str",
            "length": 10,
            "dp": False,
            "dict_key": "invoicing_zip",
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_Ort": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": "invoicing_city",
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_OrtTeil": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": "invoicing_state",
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_Land": {
            "type": "str",
            "length": 4,
            "dp": False,
            "dict_key": "invoicing_country_code",
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_Tel": {
            "type": "str",
            "length": 35,
            "dp": False,
            "dict_key": "invoicing_phone",
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_Fax": {
            "type": "str",
            "length": 35,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_Email": {
            "type": "str",
            "length": 40,
            "dp": False,
            "dict_key": "invoicing_email",
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_WWW": {
            "type": "str",
            "length": 35,
            "dp": False,
            "dict_key": "invoicing_website",
            "df_val": False,
            "df_func": False,
        },
        "Kst_Adrs_ILN": {
            "type": "str",
            "length": 13,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_DVRNr": {
            "type": "str",
            "length": 15,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_UIDNr": {
            "type": "str",
            "length": 15,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_LokKstTyp_MaxTEHoehe": {
            "type": "int",
            "length": 6,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_KSTTYP_KstTypId": {
            "type": "str",
            "length": 10,
            "dp": False,
            "dict_key": False,
            "df_val": "Standard",
            "df_func": False,
        },
        "Kst_LokKstTyp_EanQuittErl": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": "J",
            "df_func": False,
        },
        "Kst_LokKstTyp_EartErl": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": "N",
            "df_func": False,
        },
        "Kst_LokKstTyp_EMatQErl": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": "N",
            "df_func": False,
        },
        "Kst_LokKstTyp_EtikettKz": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": "N",
            "df_func": False,
        },
        "Kst_LokKstTyp_FeldKQuittErl": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": "J",
            "df_func": False,
        },
        "Kst_LokKstTyp_FeldQuittErl": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": "J",
            "df_func": False,
        },
        "Kst_LokKstTyp_KomGewInitKz": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": "N",
            "df_func": False,
        },
        "Kst_LokKstTyp_KomMngInitKz": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": "J",
            "df_func": False,
        },
        "Kst_LokKstTyp_KomPosInitKz": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": "J",
            "df_func": False,
        },
        "Kst_LokKstTyp_KontErl": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": "N",
            "df_func": False,
        },
        "Kst_LokKstTyp_KontIntWa": {
            "type": "int",
            "length": 4,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_LokKstTyp_KstGrp": {
            "type": "str",
            "length": 5,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_LokKstTyp_LiefSAnz": {
            "type": "int",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_LokKstTyp_LiefSLay": {
            "type": "str",
            "length": 20,
            "dp": False,
            "dict_key": False,
            "df_val": "Standard",
            "df_func": False,
        },
        "Kst_LokKstTyp_MkkErl": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": "N",
            "df_func": False,
        },
        "Kst_LokKstTyp_OkQuittErl": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": "N",
            "df_func": False,
        },
        "Kst_LokKstTyp_TeQuittErl": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": "J",
            "df_func": False,
        },
        "Kst_LokKstTyp_UeberliefErl": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": "N",
            "df_func": False,
        },
        "Kst_SatzKz": {
            "type": "str",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
        "Kst_SperrKzWa": {
            "type": "bool",
            "length": 1,
            "dp": False,
            "dict_key": False,
            "df_val": False,
            "df_func": False,
        },
    }
)