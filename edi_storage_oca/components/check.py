# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.tools import pycompat

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class EDIStorageCheckComponentMixin(Component):

    _name = "edi.storage.component.check"
    _inherit = [
        "edi.component.check.mixin",
        "edi.storage.component.mixin",
    ]
    _usage = "storage.check"

    def check(self):
        return self._exchange_output_check()

    def _exchange_output_check(self):
        """Check status output exchange and update record.

        1. check if the file has been processed already (done)
        2. if yes, post message and exit
        3. if not, check for errors
        4. if no errors, return

        :return: boolean
            * False if there's nothing else to be done
            * True if file still need action
        """
        if self._get_remote_file("done"):
            _logger.info(
                "%s done for: %s",
                self.exchange_record.model,
                self.exchange_record.name,
            )
            if (
                not self.exchange_record.edi_exchange_state
                == "output_sent_and_processed"
            ):
                self.exchange_record.edi_exchange_state = "output_sent_and_processed"
                self.exchange_record._notify_done()
            return False

        error = self._get_remote_file("error")
        if error:
            _logger.info(
                "%s error for: %s",
                self.exchange_record.model,
                self.exchange_record.name,
            )
            # Assume a text file will be placed there w/ the same name and error suffix
            err_filename = self.exchange_record.exchange_filename + ".error"
            error_report = self._get_remote_file("error", filename=err_filename)
            if self.exchange_record.edi_exchange_state == "output_sent":
                self.exchange_record.update(
                    {
                        "edi_exchange_state": "output_sent_and_error",
                        "exchange_error": pycompat.to_text(error_report),
                    }
                )
                self.exchange_record._notify_error("process_ko")
            return False
        return True

    # FIXME: this is not used ATM -> should be refactored
    # into an incoming exchange.
    # The backend will look for records needing an ack
    # and generate and ack record.
    def _exchange_output_handle_ack(self):
        ack_type = self.exchange_record.type_id.ack_type_id
        filename = ack_type._make_exchange_filename(self.exchange_record)
        ack_file = self._get_remote_file("done", filename=filename)
        if ack_file:
            self.backend.create_record(
                ack_type.code,
                {
                    "parent_id": self.exchange_record.id,
                    "exchange_file": ack_file,
                    "edi_exchange_state": "input_received",
                },
            )
            self.exchange_record._notify_ack_received()
        else:
            self.exchange_record._notify_ack_missing()
