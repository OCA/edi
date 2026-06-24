from odoo import models


class EdiLocalMixin(models.AbstractModel):
    _name = "edi.local.mixin"
    _description = "EDI Local Mixin"

    def get_users_notifications(self):
        return (
            self.env["res.users"]
            .search(
                [
                    (
                        "groups_id",
                        "in",
                        self.env.ref("edi_local.group_admin_edi_local").id,
                    )
                ]
            )
            .mapped("partner_id.id")
        )

    def get_url_configuration_edi(self):
        self.ensure_one()
        return (
            f"{self.get_base_url()}/web#id={self.id}"
            f"&model={self._name}&view_type=form"
        )

    def notification_message_edi(
        self,
        edi_local_id,
        message_text=None,
        message_values=None,
    ):
        self.ensure_one()
        body = message_text % message_values if message_values else message_text
        self.with_context(mail_notify_force_send=True).message_post(
            body=body,
            body_is_html=True,
            notify_author=True,
            partner_ids=edi_local_id.get_users_notifications(),
        )
