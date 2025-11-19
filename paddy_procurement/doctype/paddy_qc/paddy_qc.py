import frappe
from frappe.model.document import Document
from frappe.utils import flt
from paddy_procurement.helpers import get_rate_for, get_procurement_setting

class PaddyQC(Document):
    def validate(self):
        if not self.weighbridge_entry:
            frappe.throw("Weighbridge Entry is required.")

    def on_submit(self):
        try:
            wb_name = self.weighbridge_entry
            wb_net_weight = flt(frappe.db.get_value("Weighbridge Entry", wb_name, "net_weight") or 0)
            moisture = flt(self.moisture_percent or 0)
            impurity = flt(self.impurity_percent or 0)

            rate, ded_percent_point = get_rate_for(frappe.db.get_value("Weighbridge Entry", wb_name, "variety"), moisture)
            moisture_threshold = flt(get_procurement_setting("moisture_threshold", 14.0))
            moisture_deduction_percent = 0.0
            if moisture > moisture_threshold and ded_percent_point:
                extra_points = moisture - moisture_threshold
                moisture_deduction_percent = extra_points * ded_percent_point

            total_ded_percent = moisture_deduction_percent + impurity
            deduction_kg = (total_ded_percent / 100.0) * wb_net_weight
            final_qty = max(0.0, wb_net_weight - deduction_kg)

            self.final_payable_weight = flt(final_qty)
            self.deduction_amount = flt(deduction_kg) * flt(rate or 0.0)
            self.moisture_deduction_percent = moisture_deduction_percent
            self.total_deduction_percent = total_ded_percent

            self.save()

            pr_name = frappe.db.get_value("Weighbridge Entry", wb_name, "generated_purchase_receipt")
            if pr_name:
                pr = frappe.get_doc("Purchase Receipt", pr_name)
                if pr.docstatus == 0 and pr.items:
                    pr.items[0].qty = self.final_payable_weight
                    pr.items[0].rate = rate or pr.items[0].rate
                    pr.save()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "paddy_procurement.PaddyQC.on_submit_error")
            frappe.throw("An error occurred while processing QC. Check error log.")
