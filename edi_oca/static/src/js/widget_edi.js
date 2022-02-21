/* Copyright 2019 Tecnativa - David Vidal
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

odoo.define("edi_oca.FieldEdiConfiguration", function (require) {
    "use strict";

    var AbstractField = require("web.AbstractField");
    var field_registry = require("web.field_registry");

    var FieldEdiConfiguration = AbstractField.extend({
        description: "Field for EDI Missing configurations",
        // We want to maintain it black in order to show nothing on the header
        template: "edi_oca.FieldEdiConfiguration",
        supportedFieldTypes: ["serialized"],
        events: _.extend({}, AbstractField.prototype.events, {
            "click button": "_onClickGenerateEdiConfiguration",
        }),
        _onClickGenerateEdiConfiguration: function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var button = ev.target.closest("button");
            var type = button.dataset.name;
            var self = this;
            this._rpc({
                model: this.model,
                method: "edi_create_exchange_record",
                args: [[this.res_id], parseInt(type, 10)],
                context: this.record.getContext({}),
            }).then(function (action) {
                self.trigger_up("do_action", {action: action});
            });
        },
    });

    field_registry.add("edi_configuration", FieldEdiConfiguration);
    return FieldEdiConfiguration;
});
