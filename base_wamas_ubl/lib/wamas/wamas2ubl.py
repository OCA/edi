# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import argparse
import logging
from collections import OrderedDict
from pprint import pformat

from freezegun import freeze_time

from . import const, miniqweb, utils

# FIXME: replace by Dotty ?
from .structure import obj

_logger = logging.getLogger("wamas2ubl")


class Extractor:
    def __init__(self, data):
        self.data = data
        self.transfers = {}
        self.packages = {}

    def get_head(self, telegram_type, key_name, head=None):
        """Converts a list of dict into a dict of dict

        Parameters:
            telegram_type: the key to get the list out of data
            key_name: the key in the dict that serves as key in the new dict
            head: the result dict that is build
        """
        if telegram_type not in self.data:
            raise ValueError("Missing telegram: %s" % telegram_type)

        if head is None:
            head = self.transfers
        for item in self.data[telegram_type]:
            key = item[key_name]
            if key not in head:
                head[key] = item
            else:
                _logger.debug(
                    "Redundant %s (transfer) record found, ignoring: %s",
                    telegram_type,
                    key,
                )

    def get_line(
        self,
        telegram_type,
        transfer_key1_name,
        transfer_key2_name=False,
        package_key_name=False,
        group_by_key=False,
        group_by_key_values=(),
    ):
        """Process a list of dict as lines of the transfers

        Parameters:
            telegram_type: the key to get the list out of data
            transfer_key1_name: the key in the dict that serves to identify the
                               parent in transfers
            transfer_key2_name: the key in the dict that serves to identify a sub-transfer
            group_by_key: the key in the dict that serves to group the lines
            group_by_key_values: the values to sum when grouping by group_by_key
            package_key_name: the key in the dict that serves to identify the
                              related package
        """

        def _add_line_to_transfer(
            line, transfer, group_by_key=False, group_by_key_values=()
        ):
            if not group_by_key:
                transfer.setdefault("lines", []).append(line)
                return

            for transfer_line in transfer.get("lines", []):
                if group_by_key and line.get(group_by_key) == transfer_line.get(
                    group_by_key
                ):
                    # Sum values grouped by group_by_key
                    for group_by_key_value in group_by_key_values:
                        transfer_line[group_by_key_value] += line.get(
                            group_by_key_value
                        )
                    return
            transfer.setdefault("lines", []).append(line)

        transfers = {}
        if telegram_type not in self.data:
            raise ValueError("Missing telegram: %s" % telegram_type)

        for line in self.data[telegram_type]:
            key = line.get(transfer_key1_name)
            if key not in self.transfers:
                _logger.debug(
                    "Found %s (line) record for unknown transfer, ignoring: %s",
                    telegram_type,
                    key,
                )
                continue

            # Create a key for the sub-transfer
            if transfer_key2_name and line.get(transfer_key2_name):
                key = (key, line[transfer_key2_name])
            if key not in transfers:
                # Copy parent transfer data
                transfers[key] = OrderedDict(self.transfers[line[transfer_key1_name]])
            # Sum values grouped by group_by_key
            _add_line_to_transfer(
                line,
                transfers[key],
                group_by_key,
                group_by_key_values,
            )

            if not package_key_name:
                continue
            package_id = line[package_key_name]
            package = self.packages.get(package_id)
            if not package:
                _logger.debug(
                    "Found %s (line) record with unknown package, ignoring: %s",
                    telegram_type,
                    package_id,
                )
                continue
            line["package"] = package
            transfers[key].setdefault("packages", []).append(package)
        self.transfers = transfers


def wamas2dict(msg):
    """
    Converts a wamas message to a dict

    Parameters:
        msg (str): The msg to convert

    Returns:
        dict: key=telegram type, value=list of OrderedDict
    """
    result = {}
    supported_telegrams = utils.get_supported_telegram()
    for line in msg.splitlines():
        if not line:
            continue
        telegram_type = utils.get_telegram_type(line)
        # ignore useless telegram types
        if telegram_type in const.LST_TELEGRAM_TYPE_IGNORE_W2D:
            continue
        if telegram_type not in supported_telegrams:
            raise Exception("Invalid telegram type: %s" % telegram_type)
        grammar = utils.get_grammar(telegram_type)
        d = utils.fw2dict(line, grammar, telegram_type)
        val = result.setdefault(telegram_type, [])
        val.append(d)
    _logger.debug(pformat(result))
    return result


def dict2ubl(msg_type, data, extra_data=False):
    if extra_data is False:
        extra_data = {"DeliveryCustomerParty": {}, "DespatchSupplierParty": {}}

    # Analyze/transform wamas file content
    extractor = Extractor(data)

    if msg_type == "ReceptionResponse":
        extractor.get_head("WEAKQ", "IvWevk_WevId_WevNr")
        extractor.get_line(
            "WEAPQ",
            "IvWevp_WevId_WevNr",
            transfer_key2_name="IvWevp_WEAP_WeaId_WeaNr",
            # Group by key article
            group_by_key="IvWevp_MId_AId_ArtNr",
            # Sum quanties and weights grouped
            group_by_key_values=("IvWevp_LiefMngs_Mng", "IvWevp_LiefMngs_Gew"),
        )
    elif msg_type == "ReturnResponse":
        extractor.get_head("KRETKQ", "IvKretk_KretId_KretNr")
        extractor.get_line("KRETPQ", "IvKretp_KretId_KretNr")
    elif msg_type == "PickingResponse":
        extractor.get_head("AUSKQ", "IvAusk_AusId_AusNr")
        if "WATEKQ" not in extractor.data and "WATEPQ" not in extractor.data:
            extractor.get_line("AUSPQ", "IvAusp_UrAusId_AusNr")
        else:
            extractor.get_head("WATEKQ", "IvTek_TeId", extractor.packages)
            extractor.get_line(
                "WATEPQ", "IvAusp_UrAusId_AusNr", package_key_name="IvTep_TeId"
            )
    else:
        raise Exception("Invalid message type: %s" % msg_type)

    pickings = extractor.transfers
    _logger.debug("Number of pickings: %d", len(pickings))
    for order_id, picking in pickings.items():
        _logger.debug("ID: %s", order_id)
        packages = pickings[order_id].get("packages")
        if packages:
            _logger.debug("Number of packages: %s", len(packages))
        _logger.debug(pformat(picking))

    # Get template
    ubl_template_path = const.DICT_UBL_TEMPLATE[msg_type]
    with utils.file_open(utils.file_path(ubl_template_path)) as tmpl_file:
        ubl_template = tmpl_file.read()

    # Convert
    ubls = []
    for picking in pickings.values():
        ubl = render_ubl(ubl_template, picking, extra_data=extra_data)
        ubls.append(ubl)
    _logger.debug("Number of UBL files generated: %d", len(ubls))
    return ubls


def render_ubl(ubl_template, data, extra_data=False):
    t = miniqweb.QWebXml(ubl_template)
    # Convert dict to object to use dotted notation in template
    globals_dict = {
        "record": obj(data),
        "get_date": utils.get_date,
        "get_time": utils.get_time,
        "get_current_date": utils.get_current_date,
        "extra_data": extra_data,
    }
    xml = t.render(globals_dict)
    return xml


def wamas2ubl(wamas_msg, extra_data=False):
    data = wamas2dict(wamas_msg)
    msg_type = utils.detect_wamas_type(wamas_msg)
    return dict2ubl(msg_type, data, extra_data=extra_data)


@freeze_time("2023-05-01")
def main():
    parser = argparse.ArgumentParser(
        description="Converts wamas message into UBLs documents.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="enable debug log")
    parser.add_argument(
        "-f", "--format", default="ubl", choices=["dict", "ubl"], help="result format"
    )
    parser.add_argument(
        "-o", "--output", dest="outputfile", help="write result in this file"
    )
    parser.add_argument("inputfile", help="read message from this file")
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    infile = utils.file_open(args.inputfile).read()
    if args.format == "dict":
        res = pformat(wamas2dict(infile))
    else:
        res = "\n".join(wamas2ubl(infile))
    if args.outputfile:
        fd = utils.file_open(args.outputfile, "w")
        fd.write(res)
    else:
        print(res)  # pylint: disable=print-used


if __name__ == "__main__":
    main()
