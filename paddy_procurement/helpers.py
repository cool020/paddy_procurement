import frappe
from frappe.utils import flt

def calculate_net_weight(gross, tare):
    return flt(gross) - flt(tare)

def get_default_rate(variety):
    try:
        v = frappe.get_doc("Paddy Variety", variety)
        return flt(v.default_rate or 0)
    except Exception:
        return 0.0

def get_rate_for(variety, moisture):
    try:
        rules = frappe.get_all(
            "Paddy Rate Rule",
            filters=[["variety","=",variety],["moisture_from","<=",moisture],["moisture_to",">=",moisture]],
            order_by="effective_from desc",
            limit_page_length=1
        )
        if rules:
            doc = frappe.get_doc("Paddy Rate Rule", rules[0].name)
            rate = flt(doc.fixed_rate_override) if flt(doc.fixed_rate_override) else get_default_rate(variety)
            deduction_percent_per_point = flt(doc.deduction_percent_per_point or 0)
            return rate, deduction_percent_per_point
    except Exception:
        frappe.log_error(frappe.get_traceback(), "paddy_procurement.get_rate_for_error")
    return get_default_rate(variety), 0.0

def get_procurement_setting(key, default=None):
    try:
        s = frappe.get_single("Procurement Settings")
        return getattr(s, key, default)
    except Exception:
        return default
