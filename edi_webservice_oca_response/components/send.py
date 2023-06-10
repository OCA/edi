# Copyright 2022 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from requests import HTTPError

from odoo.addons.component.core import Component


class EDIWebserviceSend(Component):
    _inherit = "edi.webservice.send"

    def __init__(self, work_context):
        super().__init__(work_context)
        self.ws_settings = getattr(work_context, "webservice", {})
        self.webservice_backend = self.backend.webservice_backend_id

    def send(self):
        try:
            response_content = super().send()
        except HTTPError as err:
            response_content = err.response.content
            status_code = err.response.status_code
            raise err from err
        except Exception as ex:
            status_code = False
            response_content = ""
            raise ex from ex
        else:
            status_code = 200
        finally:
            self.exchange_record._set_file_content(
                response_content, field_name="ws_response_content"
            )
            self.exchange_record.ws_response_status_code = status_code
