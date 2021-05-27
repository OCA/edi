# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from freezegun import freeze_time

from odoo.tools import mute_logger

from .common import TestEDIStorageBase

LOGGERS = (
    "odoo.addons.edi_storage_oca.components.check",
    "odoo.addons.edi_oca.models.edi_backend",
)


@freeze_time("2020-10-21 10:30:00")
class TestEDIBackendOutput(TestEDIStorageBase):
    @mute_logger(*LOGGERS)
    def test_export_file_sent(self):
        """Send, no errors."""
        self.record.edi_exchange_state = "output_pending"
        mocked_paths = {self._file_fullpath("pending"): self.fakepath}
        # TODO: test send only w/out cron (make sure check works)
        # self._test_send(self.record, mocked_paths=mocked_paths)
        self._test_run_cron(mocked_paths)
        self._test_result(
            self.record,
            {"edi_exchange_state": "output_sent"},
            expected_messages=[
                {
                    "message": self.record._exchange_status_message("send_ok"),
                    "level": "info",
                }
            ],
        )

    @mute_logger(*LOGGERS)
    def test_export_file_already_done(self):
        """Already sent, successfully."""
        self.record.edi_exchange_state = "output_sent"
        mocked_paths = {self._file_fullpath("done"): self.fakepath}
        # TODO: test send only w/out cron (make sure check works)
        self._test_run_cron(mocked_paths)
        # As we simulate to find a file in `done` folder,
        # we should get the final good state
        # and only one call to ftp
        self._test_result(
            self.record,
            {"edi_exchange_state": "output_sent_and_processed"},
            state_paths=("done",),
            expected_messages=[
                {
                    "message": self.record._exchange_status_message("process_ok"),
                    "level": "info",
                }
            ],
        )

    # FIXME: ack should be handle as an incoming record (new machinery to be added)
    # @mute_logger(*LOGGERS)
    # def test_export_file_already_done_ack_needed_not_found(self):
    #     self.record.edi_exchange_state = "output_sent"
    #     self.record.type_id.ack_needed = True
    #     mocked_paths = {
    #         self._file_fullpath("done"): self.fakepath,
    #     }
    #     self._test_run_cron(mocked_paths)
    #     # No ack file found, warning message is posted
    #     self._test_result(
    #         self.record,
    #         {"edi_exchange_state": "output_sent_and_processed"},
    #         state_paths=("done",),
    #         expected_messages=[
    #             {
    #                 "message": self.record._exchange_status_message("ack_missing"),
    #                 "level": "warning",
    #             },
    #             {
    #                 "message": self.record._exchange_status_message("process_ok"),
    #                 "level": "info",
    #             },
    #         ],
    #     )

    # @mute_logger(*LOGGERS)
    # def test_export_file_already_done_ack_needed_found(self):
    #     self.record.edi_exchange_state = "output_sent"
    #     self.record.type_id.ack_needed = True
    #     mocked_paths = {
    #         self._file_fullpath("done"): self.fakepath,
    #         self._file_fullpath("done", ack=True): self.fakepath_ack,
    #     }
    #     self._test_run_cron(mocked_paths)
    #     # Found ack file, set on record
    #     self._test_result(
    #         self.record,
    #         {
    #             "edi_exchange_state": "output_sent_and_processed",
    #             "ack_file": base64.b64encode(b"ACK filecontent"),
    #         },
    #         state_paths=("done",),
    #         expected_messages=[
    #             {
    #                 "message": self.record._exchange_status_message("ack_received"),
    #                 "level": "info",
    #             },
    #             {
    #                 "message": self.record._exchange_status_message("process_ok"),
    #                 "level": "info",
    #             },
    #         ],
    #     )

    @mute_logger(*LOGGERS)
    def test_already_sent_process_error(self):
        """Already sent, error process."""
        self.record.edi_exchange_state = "output_sent"
        mocked_paths = {
            self._file_fullpath("error"): self.fakepath,
            self._file_fullpath("error-report"): self.fakepath_error,
        }
        self._test_run_cron(mocked_paths)
        # As we simulate to find a file in `error` folder,
        # we should get a call for: done, error and then the read of the report.
        self._test_result(
            self.record,
            {
                "edi_exchange_state": "output_sent_and_error",
                "exchange_error": "ERROR XYZ: line 2 broken on bla bla",
            },
            state_paths=("done", "error", "error-report"),
            expected_messages=[
                {
                    "message": self.record._exchange_status_message("process_ko"),
                    "level": "error",
                }
            ],
        )

    @mute_logger(*LOGGERS)
    def test_cron_full_flow(self):
        """Already sent, update the state via cron."""
        self.record.edi_exchange_state = "output_sent"
        rec1 = self.record
        partner2 = self.env.ref("base.res_partner_2")
        partner3 = self.env.ref("base.res_partner_3")
        rec2 = self.record.copy(
            {
                "model": partner2._name,
                "res_id": partner2.id,
                "exchange_filename": "rec2.csv",
            }
        )
        rec3 = self.record.copy(
            {
                "model": partner3._name,
                "res_id": partner3.id,
                "exchange_filename": "rec3.csv",
                "edi_exchange_state": "output_sent_and_error",
            }
        )
        mocked_paths = {
            self._file_fullpath("done", record=rec1): self.fakepath,
            self._file_fullpath("error", record=rec2): self.fakepath,
            self._file_fullpath("error-report", record=rec2): self.fakepath_error,
            self._file_fullpath("done", record=rec3): self.fakepath,
        }
        self._test_run_cron(mocked_paths)
        self._test_result(
            rec1,
            {"edi_exchange_state": "output_sent_and_processed"},
            state_paths=("done",),
            expected_messages=[
                {
                    "message": rec1._exchange_status_message("process_ok"),
                    "level": "info",
                }
            ],
        )
        self._test_result(
            rec2,
            {
                "edi_exchange_state": "output_sent_and_error",
                "exchange_error": "ERROR XYZ: line 2 broken on bla bla",
            },
            state_paths=("done", "error", "error-report"),
            expected_messages=[
                {
                    "message": rec2._exchange_status_message("process_ko"),
                    "level": "error",
                }
            ],
        )
        self._test_result(
            rec3,
            {"edi_exchange_state": "output_sent_and_processed"},
            state_paths=("done",),
            expected_messages=[
                {
                    "message": rec3._exchange_status_message("process_ok"),
                    "level": "info",
                }
            ],
        )
