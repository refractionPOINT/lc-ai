# get_billing_details

Retrieve billing and subscription information for an organization.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "plan": "enterprise",
  "status": "active",
  "billing_email": "billing@example.com",
  "payment_method": "card",
  "last_four": "4242",
  "next_billing_date": 1640995200,
  "auto_renew": true
}
```

## Example

```
lc_call_tool(tool_name="get_billing_details", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Notes

- Requires admin/owner permissions
- Sensitive payment info (full card numbers) is never returned
- Payment method updates must be done through web console
- This is a read-only operation - no billing changes made
- Always verify billing contact email for important notifications

## Currency and Amount Handling

**CRITICAL: All monetary amounts are returned in CENTS (smallest currency unit), not dollars.**

The LimaCharlie billing API uses Stripe, which returns amounts in the smallest currency unit:
- For USD: amounts are in **cents** (1/100 of a dollar)
- For EUR: amounts are in **cents** (1/100 of a euro)

### Conversion Examples

| API Returns | Actual Value |
|-------------|--------------|
| `100` | $1.00 |
| `250` | $2.50 |
| `5000` | $50.00 |
| `25342` | $253.42 |
| `364000` | $3,640.00 |

### Fields Affected

The following fields return amounts in cents:
- `amount` / `amount_cents` - Line item amounts
- `unit_amount` / `unit_amount_cents` - Per-unit prices
- `total` / `subtotal` - Invoice totals
- `balance` - Account balance
- `tax` - Tax amounts

### Correct Interpretation

When processing billing responses:

```python
# WRONG - treats cents as dollars
total_cost = response['amount']  # 25342 interpreted as $25,342

# CORRECT - convert cents to dollars
total_cost = response['amount'] / 100  # 25342 / 100 = $253.42
```

### Description vs Amount Discrepancy

Line item descriptions may show human-readable prices like:
```
"10 × LCIO-CANADA-GENERAL-V2 (at $2.50 / month)"
```

But the `amount` field will be in cents:
```json
{
  "description": "10 × LCIO-CANADA-GENERAL-V2 (at $2.50 / month)",
  "amount": 2500,  // This is $25.00, NOT $2,500
  "quantity": 10
}
```

**Always divide amount fields by 100 to get the dollar value.**

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../CALLING_API.md).

For the Go SDK implementation, check: `go-limacharlie/limacharlie/billing.go` (GetBillingOrgDetails function)
For the MCP tool implementation, check: `lc-mcp-server/internal/tools/admin/admin.go` (RegisterGetBillingDetails)
