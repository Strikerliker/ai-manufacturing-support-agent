# Inventory and Barcode Support

## Scanner or barcode transaction failure

When a scanner cannot post an inventory transaction, confirm the device is connected, the barcode is readable, the user is signed into the correct site or warehouse, and the ERP transaction is valid for the item and location. Capture the exact transaction and error message before retrying.

Do not repeatedly submit a transaction if duplicate inventory movement could result. Verify whether the original transaction posted before attempting it again.

## Inventory discrepancy escalation

If system quantity and physical quantity differ, do not correct the database directly. Follow the approved cycle-count, adjustment, or inventory-control process and document the item, lot or serial number when applicable, location, observed quantity, system quantity, and timestamp.

## Traceability and regulated records

For serialized, lot-controlled, quality-controlled, or regulated material, preserve traceability. Escalate uncertainty about genealogy, lot status, disposition, or quality holds to the responsible inventory or quality owner before changing records.