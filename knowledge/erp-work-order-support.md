# ERP Work Order Support

## Work order release troubleshooting

When a user cannot release a work order, first confirm the user is in the correct plant and company context, the work order status is eligible for release, required material and routing records exist, and no validation message is being ignored. Record the exact error text before making any change.

If the issue appears to be role or permission related, compare the user's assigned ERP role with an approved peer role. Do not grant administrator access or copy broad permissions as a workaround. Access changes must follow the organization's approved access-request process.

## Production impact escalation

If the work order issue is stopping a production line or blocking shipment-critical work, capture the work order number, plant, affected operation, error message, start time, and business impact. Escalate to the ERP application owner and production operations lead using the high-priority support path.

## Data correction

Do not directly modify ERP database records to bypass application validation. Data corrections must be performed through an approved ERP transaction, controlled utility, or vendor-supported method with change documentation.