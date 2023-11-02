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
        interchange = Interchange.from_str(order_file.decode())
        return interchange

    @api.model
    def _get_msg_type(self, interchange):
        seg = interchange.get_segment("UNH")
        # MSG_TYPE, EDIFACT_MSG_TYPE_RELEASE
        return (seg[1][0], "{}{}".format(seg[1][1], seg[1][2]))

    @api.model
    def map2odoo_date(self, dt):
        # '102'
        dtt = datetime.datetime.strptime(dt[1], "%Y%m%d")
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
        # PARTY NAME
        if bool(seg[2]):
            d["name"] = seg[2]
        if bool(seg[3]):
            d["name"] = "{}{}".format(f"{d['name']}. " if d.get("name") else "", seg[3])
        if bool(seg[4]):
            # Street address and/or PO Box number in a structured address: one to three lines.
            d["street"] = seg[4]
        if bool(seg[5]):
            d["city"] = seg[5]
        if bool(seg[6]):
            # Country sub-entity identification
            d["state_code"] = seg[6]
        if bool(seg[7]):
            d["zip"] = seg[7]
        if bool(seg[8]):
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
    def map2odoo_product(self, seg):
        """
        :seg: LIN segment
            ['1', '', ['8885583503464', 'EN']]
        EN. International Article Numbering Association (EAN)
        UP. UPC (Universal product code)
        SRV. GTIN
        """
        product = seg[2]
        pct = product[1]
        return dict(code=product[0]) if pct == "SRV" else dict(barcode=product[0])

    @api.model
    def map2odoo_qty(self, seg):
        """
        'QTY' EDI segment: [['21', '2']]
        '21'. Ordered quantity
        """
        return float(seg[0][1])

    @api.model
    def map2odoo_unit_price(self, seg):
        """
        'PRI' EDI segment: [['AAA', '19.75']]
        Price qualifier:
        * 'AAA'. Calculation net
        * 'AAB'. Calculation gross
        """
        pri = seg[0]
        if pri[0] == "AAA":
            return float(pri[1])
        return 0.0
