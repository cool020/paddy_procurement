import frappe
from frappe import _

@frappe.whitelist(allow_guest=False)
def receive_weighbridge(payload=None, vehicle_no=None, gross_weight=None,
                        tare_weight=None, farmer=None, supplier=None,
                        variety=None, weighbridge_timestamp=None, source_weighbridge_id=None):
    try:
        import json
        if payload:
            if isinstance(payload, str):
                payload = json.loads(payload)
        else:
            payload = {
                "vehicle_no": vehicle_no,
                "gross_weight": gross_weight,
                "tare_weight": tare_weight,
                "farmer": farmer,
                "supplier": supplier,
                "variety": variety,
                "weighbridge_timestamp": weighbridge_timestamp,
                "source_weighbridge_id": source_weighbridge_id
            }

        if payload.get("gross_weight") is None or payload.get("tare_weight") is None:
            frappe.throw(_("gross_weight and tare_weight are required"))

        wb = frappe.get_doc({
            "doctype": "Weighbridge Entry",
            "vehicle_no": payload.get("vehicle_no"),
            "gross_weight": payload.get("gross_weight"),
            "tare_weight": payload.get("tare_weight"),
            "weighbridge_timestamp": payload.get("weighbridge_timestamp"),
            "farmer": payload.get("farmer"),
            "supplier": payload.get("supplier"),
            "variety": payload.get("variety"),
            "source_weighbridge_id": payload.get("source_weighbridge_id"),
            "status": "Submitted"
        })
        wb.flags.ignore_permissions = True
        wb.insert()
        return {"status": "success", "weighbridge_entry": wb.name}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "paddy_procurement.receive_weighbridge_error")
        frappe.throw(_("Failed to receive weighbridge data."))
