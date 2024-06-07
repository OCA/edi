# Copyright 2023 ALBA Software S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


import datetime
import logging

from pydifact.segmentcollection import Interchange, Message
from pydifact.segments import Segment

from odoo import api, models

logger = logging.getLogger(__name__)


# https://github.com/nerdocs/pydifact
class BasePydifact(models.AbstractModel):
    _name = "base.edifact"
    _description = "Generate and parse Edifact documents"

    MAP_AGENCY_CODE_2_RES_PARTNER_NAMEREF = {"9": "gln"}
    CURRENCY_SYMBOLS = {
        "EUR": "€",
        "USD": "$",
    }
    PRODUCT_CODE_TYPES = {"EN": "EAN", "UP": "UPC", "SRV": "GTIN"}

    @api.model
    def pydifact_import(self, names):
        classes = {
            "Segment": Segment,
            "Message": Message,
            "Interchange": Interchange,
        }
        return [classes.get(name, None) for name in names]

    @api.model
    def pydifact_obj(self, docu):
        obj = []
        interchange = self._loads_edifact(docu)
        header_seg = interchange.get_header_segment()
        header_dict = dict()
        header_dict[header_seg.tag] = header_seg.elements
        obj.append(header_dict)
        for message in interchange.get_messages():
            segms = []
            msg = {
                "reference_number": message.reference_number,
                "type": message.type,
                "version": message.version,
                "identifier": message.identifier,
                "HEADER_TAG": message.HEADER_TAG,
                "FOOTER_TAG": message.FOOTER_TAG,
                "characters": str(message.characters),
                "extra_header_elements": message.extra_header_elements,
                "has_una_segment": message.has_una_segment,
            }
            logger.info(message)
            for segment in message.segments:
                logger.info(
                    "Segment tag: {}, content: {}".format(segment.tag, segment.elements)
                )
                # segms.append((segment.tag, segment.elements))
                seg = dict()
                seg[segment.tag] = segment.elements
                segms.append(seg)
            msg["segments"] = segms
            obj.append(msg)
        return obj

    @api.model
    def _loads_edifact(self, order_file):
        # TODO: use chardet library for get encoding
        try:
            interchange = Interchange.from_str(order_file.decode())
        except UnicodeDecodeError:
            interchange = Interchange.from_str(order_file.decode("latin-1"))
        return interchange

    @api.model
    def _get_msg_type(self, interchange):
        seg = interchange.get_segment("UNH")
        # MSG_TYPE, EDIFACT_MSG_TYPE_RELEASE
        return (seg[1][0], "{}{}".format(seg[1][1], seg[1][2]))

    @api.model
    def map2odoo_date(self, dt):
        # '102'
        date_format = "%Y%m%d%H%M%S"
        length_dt = len(dt[1])
        if length_dt % 2 == 0 and length_dt in range(8, 13, 2):
            date_format = date_format[0 : length_dt - 2]
        dtt = datetime.datetime.strptime(dt[1], date_format)
        return dtt.date()

    @api.model
    def map2odoo_partner(self, seg):
        """
        BY. Party to which merchandise is sold.
            NAD+BY+5550534000017::9'
            NAD segment: ['BY', ['5550534001649', '', '9']]

        SU. Party which manufactures or otherwise has possession of
            goods,and consigns or makes them available in trade.
            NAD+SU+<Supplier GLN>::9'
        """

        partner_dict = {}
        codes = ["BY", "SU"]
        reference_code = seg[0]
        if reference_code not in codes:
            raise NotImplementedError(f"Code '{reference_code}' not implemented")
        #
        party_identification = seg[1]
        party_id = party_identification[0]
        agency_code = party_identification[2]
        nameref = self.MAP_AGENCY_CODE_2_RES_PARTNER_NAMEREF.get(agency_code, "gln")
        partner_dict[nameref] = party_id
        return partner_dict

    @api.model
    def map2odoo_address(self, seg):
        """
        DP. Party to which goods should be delivered, if not identical with
            consignee.
            NAD+DP+5550534000086::9+++++++DE'
            NAD segment: ['DP', ['5550534022101', '', '9'], '', '', '', '', '', '', 'ES']
        IV. Party to whom an invoice is issued.
            NAD+IV+5450534005838::9++AMAZON EU SARL:NIEDERLASSUNG
            DEUTSCHLAND+MARCEL-BREUER-STR. 12+MUENCHEN++80807+DE

        :returns: {
            'type':
            'partner': {'gln':''}
            'address': {...}
        }
        """
        if seg[0] not in ("DP", "IV"):
            return False
        order_type = "delivery" if seg[0] == "DP" else "invoice"
        address = dict(type=order_type, partner={}, address={})
        # PARTY IDENTIFICATION DETAILS
        iden = seg[1]
        party_id = iden[0]
        agency_code = iden[2]
        nameref = self.MAP_AGENCY_CODE_2_RES_PARTNER_NAMEREF.get(agency_code, "gln")
        address["partner"][nameref] = party_id
        d = address["address"]
        # Fallback if address information is missing
        try:
            if isinstance(seg, Segment):
                lenght_seg = len(seg.elements)
            else:
                lenght_seg = len(seg)
        except ValueError:
            lenght_seg = 0
        # PARTY NAME
        if lenght_seg > 2 and bool(seg[2]):
            d["name"] = seg[2]
        if lenght_seg > 3 and bool(seg[3]):
            d["name"] = "{}{}".format(f"{d['name']}. " if d.get("name") else "", seg[3])
        if lenght_seg > 4 and bool(seg[4]):
            # Street address and/or PO Box number in a structured address: one to three lines.
            d["street"] = seg[4]
        if lenght_seg > 5 and bool(seg[5]):
            d["city"] = seg[5]
        if lenght_seg > 6 and bool(seg[6]):
            # Country sub-entity identification
            d["state_code"] = seg[6]
        if lenght_seg > 7 and bool(seg[7]):
            d["zip"] = seg[7]
        if lenght_seg > 8 and bool(seg[8]):
            # Country, coded ISO 3166
            d["country_code"] = seg[8]

        return address

    @api.model
    def map2odoo_currency(self, seg):
        """
        ['2', 'EUR', '9']
        """
        # Identification of the name or symbol of the monetary unit involved in the transaction.
        currency_coded = seg[1]
        return {
            "iso": currency_coded,
            "symbol": self.CURRENCY_SYMBOLS.get(currency_coded, False),
        }

    @api.model
    def map2odoo_product(self, seg, pia=None):
        """
        :seg: LIN segment
            ['1', '', ['8885583503464', 'EN']]
        EN. International Article Numbering Association (EAN)
        UP. UPC (Universal product code)
        SRV. GTIN
        :pia: PIA segment
            ['5', ['1276', 'SA', '', '9']]
        SA. Supplier's Article Number
        """
        res = {}
        # Set default code based on SA if given
        if pia is not None and pia[1][0]:
            res["code"] = pia[1][0]
        code = seg[2][0] if len(list(seg)) > 2 else False
        if code:
            field = "code" if seg[2][1] == "SRV" else "barcode"
            res[field] = code
        return res

    @api.model
    def map2odoo_qty(self, seg):
        """
        'QTY' EDI segment: [['21', '2']]
        '21'. Ordered quantity
        """
        return float(seg[0][1])

    @api.model
    def map2odoo_unit_price(self, seg=None):
        """
        'PRI' EDI segment: [['AAA', '19.75']]
        Price qualifier:
        * 'AAA'. Calculation net
        * 'AAB'. Calculation gross
        """
        if seg:
            pri = seg[0]
            if pri[0] == "AAA":
                return float(pri[1])
            # TODO: Add price calculation formula
            if pri[0] == "AAB":
                return float(pri[1])
        return 0.0

    @api.model
    def map2odoo_description(self, seg):
        """
        'IMD' EDI segment: ['F', '79', ['', '', '', 'Description']]
        F: Label
        79: Other description
        """
        if seg:
            description = seg[2][3]
            return description
        return None

    def _safe_segment_element(self, value):
        if value is False:
            return ""
        return str(value)

    @api.model
    def create_segment(self, *elements):
        cleaned_elements = []
        for element in elements:
            if isinstance(element, list):
                cleaned_elements.append(
                    [self._safe_segment_element(value) for value in element]
                )
            else:
                cleaned_elements.append(self._safe_segment_element(element))
        return Segment(*cleaned_elements)

    def create_interchange(self, sender, recipient, control_ref, syntax_identifier):
        """
        Create an interchange (started by UNB segment, ended by UNZ segment)

        :param list sender: Identification of the sender of the interchange.
            example: ["40410", "14"]
                - 40410: Identification of the sender of the interchange
                - 14: EAN (European Article Numbering Association)
        :param list recipient: Identification of the recipient of the interchange.
            example: ["40411", "14"]
        :param str control_ref: Unique reference assigned by the sender to an interchange.
            example: "10"
        :param list syntax_identifier: Identification of the agency controlling
            the syntax and indication of syntax level, plus the syntax version number.
            example: ["UNOC", "3"]

        :return: Interchange object representing the created interchange.
        :rtype: Interchange
        """
        if not sender or not recipient or not control_ref or not syntax_identifier:
            raise ValueError("All parameters must have values and not be False")

        interchange = Interchange(
            sender=(sender),
            recipient=(recipient),
            control_reference=str(control_ref),
            syntax_identifier=(syntax_identifier),
        )
        return interchange
