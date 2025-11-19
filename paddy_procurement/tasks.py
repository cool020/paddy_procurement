import frappe

def hourly_weighbridge_sync():
    try:
        auto_create = False
        try:
            auto_create = frappe.get_single("Procurement Settings").auto_create_purchase_receipt_on_submit or False
        except Exception:
            pass
        if not auto_create:
            return

        wbs = frappe.get_all("Weighbridge Entry",
                            filters=[["status","=","Submitted"],["generated_purchase_receipt","=",""]],
                            limit_page_length=200)
        for w in wbs:
            try:
                wb = frappe.get_doc("Weighbridge Entry", w.name)
                wb.create_purchase_receipt()
            except Exception:
                frappe.log_error(frappe.get_traceback(), f"paddy_procurement.tasks.process_wb_{w.name}")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "paddy_procurement.tasks.hourly_weighbridge_sync_error")
