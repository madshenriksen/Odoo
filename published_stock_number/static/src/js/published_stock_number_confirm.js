/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { ListRenderer } from "@web/views/list/list_renderer";
import { KanbanRecord } from "@web/views/kanban/kanban_record";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { onMounted, onPatched } from "@odoo/owl";

const ICON_SRC = "/published_stock_number/static/src/img/published_stock_number.png";
const ICON_CLASS = "o_published_stock_number_icon_js";

function hasPublishedStockNumber(record) {
    return Boolean(record?.data?.published_stock_number);
}

function ensureIconNearName(container, active) {
    if (!container) {
        return;
    }
    const existing = container.querySelector(`.${ICON_CLASS}`);
    if (!active) {
        existing?.remove();
        return;
    }

    if (existing) {
        return;
    }

    const name =
        container.querySelector(".o_field_widget[name='name']") ||
        container.querySelector("[name='name']") ||
        container.querySelector("[data-name='name']") ||
        container.querySelector(".o_name") || 
	container.querySelector('.d-flex.mb-0.h5:has([name="is_favorite"])');

    if (!name?.parentElement) {
        return;
    }

    const img = document.createElement("img");
    img.src = ICON_SRC;
    img.alt = "Published Stock Number";
    img.title = "Published Stock Number";
    img.className = ICON_CLASS;
    name.prepend(img);
}

function scanListRows(renderer) {
    const records = renderer.props?.list?.records || [];
    const rows = renderer.tableRef?.el?.querySelectorAll("tbody tr.o_data_row") || [];
    rows.forEach((row, index) => ensureIconNearName(row, hasPublishedStockNumber(records[index])));
}

patch(ListRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        onMounted(() => scanListRows(this));
        onPatched(() => scanListRows(this));
    },
});

patch(KanbanRecord.prototype, {
    setup() {
        super.setup(...arguments);
        const renderIcon = () => ensureIconNearName(this.rootRef?.el, hasPublishedStockNumber(this.props?.record));
        onMounted(renderIcon);
        onPatched(renderIcon);
    },
});

patch(FormController.prototype, {
    async saveButtonClicked(params = {}) {
        const root = this.model?.root;
        const data = root?.data || {};
        const wasPublishedStockNumber = Boolean(root?._values?.published_stock_number);

        if (this.props?.resModel === "product.template" && wasPublishedStockNumber) {
            return new Promise((resolve) => {
                this.dialogService.add(ConfirmationDialog, {
                    title: "Published Stock Number",
                    body: "You are about to edit a Published Stock Number. Are you sure you want to proceed?",
                    confirmLabel: "OK",
                    cancelLabel: "Discard",
                    confirm: async () => {
                        const result = await super.saveButtonClicked(params);
                        resolve(result);
                    },
                    cancel: async () => {
                        if (root?.discard) {
                            await root.discard();
                        }
                        resolve(false);
                    },
                });
            });
        }

        return super.saveButtonClicked(params);
    },
});
