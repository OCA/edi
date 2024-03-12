odoo.define("base_import_pdf_by_template.BaseImportPdfSimpleMenu", function (require) {
    "use strict";

    const FavoriteMenu = require("web.FavoriteMenu");
    const {useModel} = require("web.Model");
    const {Component} = owl;

    class BaseImportPdfSimpleMenu extends Component {
        constructor() {
            super(...arguments);
            this.model = useModel("searchModel");
        }
        openWizardBaseImportPdfUpload() {
            const ctx = this.model.config.context;
            ctx.default_model = this.model.config.modelName;
            this.trigger("do-action", {
                action: "base_import_pdf_by_template.action_wizard_base_import_pdf_upload",
                options: {
                    additional_context: ctx,
                },
            });
        }
        static shouldBeDisplayed() {
            return true;
        }
    }
    BaseImportPdfSimpleMenu.props = {};
    BaseImportPdfSimpleMenu.template = "BaseImportPdfSimple.ImportRecords";
    FavoriteMenu.registry.add(
        "base-import-pdf-simple-menu",
        BaseImportPdfSimpleMenu,
        1
    );
    return BaseImportPdfSimpleMenu;
});
