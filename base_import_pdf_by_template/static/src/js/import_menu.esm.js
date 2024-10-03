/** @odoo-module **/

import {DropdownItem} from "@web/core/dropdown/dropdown_item";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {archParseBoolean} from "@web/views/utils";
import {Component} from "@odoo/owl";
import {STATIC_ACTIONS_GROUP_NUMBER} from "@web/search/action_menus/action_menus";

const cogMenuRegistry = registry.category("cogMenu");
export class BaseImportPdfSimpleMenu extends Component {
    static template = "base_import_pdf_by_template.ImportRecords";
    static components = {DropdownItem};

    setup() {
        this.action = useService("action");
    }

    openWizardBaseImportPdfUpload() {
        const {context, resModel} = this.env.searchModel;
        context.default_model = resModel;
        this.action.doAction(
            "base_import_pdf_by_template.action_wizard_base_import_pdf_upload",
            {additionalContext: context}
        );
    }
}

export const BaseImportPdfSimpleMenuItem = {
    Component: BaseImportPdfSimpleMenu,
    groupNumber: STATIC_ACTIONS_GROUP_NUMBER,
    isDisplayed: ({config, isSmall}) =>
        !isSmall &&
        config.actionType === "ir.actions.act_window" &&
        ["kanban", "list"].includes(config.viewType) &&
        archParseBoolean(config.viewArch.getAttribute("import"), true) &&
        archParseBoolean(config.viewArch.getAttribute("create"), true),
};

cogMenuRegistry.add("base-import-pdf-simple-menu", BaseImportPdfSimpleMenuItem, {
    sequence: 2,
});
