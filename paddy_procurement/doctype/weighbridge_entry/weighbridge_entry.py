import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate
from paddy_procurement.helpers import calculate_net_weight, get_rate_for, get_procurement_setting

class WeighbridgeEntry(Document):
    def validate(self):
        self.net_weight = calculate_net_weight(self.gross_weight or 0, self.tare_weight or 0)
        if self.net_weight < 0:
            frappe.throw("Net weight cannot be negative.")

    def on_submit(self):
        try:
            auto_create = get_procurement_setting("auto_create_purchase_receipt_on_submit", False)
            if not auto_create:
                return
            if frappe.db.get_value("Weighbridge Entry", self.name, "generated_purchase_receipt"):
                return
            qc_name = frappe.db.get_value("Paddy QC", {"weighbridge_entry": self.name, "qc_status": "Pass"})
            qc_doc = frappe.get_doc("Paddy QC", qc_name) if qc_name else None
            self.create_purchase_receipt(qc_doc)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "paddy_procurement.WeighbridgeEntry.on_submit_error")

    def create_purchase_receipt(self, qc_doc=None):
        try:
            item_code = get_procurement_setting("default_item_code", "PADDY")
            warehouse = get_procurement_setting("default_warehouse", None)
            if not warehouse:
                frappe.throw("Default warehouse not configured in Procurement Settings.")

            qty = flt(self.net_weight or 0)
            payable_qty = qty
            unit_rate = None

            if qc_doc:
                moisture = flt(qc_doc.moisture_percent or 0)
                impurity = flt(qc_doc.impurity_percent or 0)
                rate, deduction_percent_per_point = get_rate_for(self.variety, moisture)
                moisture_threshold = flt(get_procurement_setting("moisture_threshold", 14.0))
                moisture_deduction_percent = 0.0
                if moisture > moisture_threshold and deduction_percent_per_point:
                    extra_points = moisture - moisture_threshold
                    moisture_deduction_percent = extra_points * deduction_percent_per_point
                total_deduction_percent = moisture_deduction_percent + impurity
                deduction_kg = (total_deduction_percent / 100.0) * qty
                payable_qty = max(0.0, qty - deduction_kg)
                unit_rate = rate
            else:
                unit_rate, _ = get_rate_for(self.variety, 0)

            supplier = self.supplier or (frappe.get_value("Farmer", self.farmer, "supplier_link") if self.farmer else None)

            pr_doc = frappe.get_doc({
                "doctype": "Purchase Receipt",
                "supplier": supplier or "",
                "posting_date": (self.weighbridge_timestamp.date() if getattr(self, "weighbridge_timestamp", None) else nowdate()),
                "items": [
                    {
                        "item_code": item_code,
                        "qty": payable_qty,
                        "uom": "Kg",
                        "rate": unit_rate or 0.0,
                        "warehouse": warehouse,
                        "description": f"Paddy inward from Weighbridge Entry {self.name}"
                    }
                ],
                "weighbridge_entry": self.name,
                "notes": f"Auto created from Weighbridge Entry {self.name}"
            })
            pr_doc.flags.ignore_permissions = True
            pr_doc.insert()
            frappe.db.set_value("Weighbridge Entry", self.name, "generated_purchase_receipt", pr_doc.name)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "paddy_procurement.create_purchase_receipt_error")
            frappe.throw("Failed to create Purchase Receipt. Check error log.")
