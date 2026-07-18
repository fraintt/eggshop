# Home Assistant integration

The app exposes a single read-only JSON endpoint, token-protected, meant to
be polled by Home Assistant's built-in RESTful sensor integration.

## Endpoint

```
GET http://<your-server>:8000/api/ha/summary/
Authorization: Token <HA_API_TOKEN from your .env>
```

Example response:

```json
{
  "new_orders": 2,
  "orders_awaiting_invoice": 5,
  "open_invoices": 3,
  "total_unpaid_eur": 45.0,
  "total_paid_this_month_eur": 120.0,
  "total_paid_all_time_eur": 860.0,
  "generated_at": "2026-07-12T10:15:00+02:00"
}
```

- `new_orders` - orders that are `pending` or `confirmed` (i.e. need your attention)
- `orders_awaiting_invoice` - `completed` orders not yet on an invoice
- `open_invoices` - invoices created but not yet marked paid
- `total_unpaid_eur` - sum of all open invoices
- `total_paid_this_month_eur` / `total_paid_all_time_eur` - income totals

If the token is missing or wrong, it responds `401` with no data.

## Home Assistant `configuration.yaml`

```yaml
sensor:
  - platform: rest
    name: Egg Shop Summary
    resource: http://<your-server>:8000/api/ha/summary/
    method: GET
    headers:
      Authorization: !secret eggshop_api_token
    scan_interval: 300
    value_template: "{{ value_json.new_orders }}"
    json_attributes:
      - new_orders
      - orders_awaiting_invoice
      - open_invoices
      - total_unpaid_eur
      - total_paid_this_month_eur
      - total_paid_all_time_eur

  - platform: template
    sensors:
      egg_shop_new_orders:
        friendly_name: "Egg Shop - New Orders"
        value_template: "{{ state_attr('sensor.egg_shop_summary', 'new_orders') }}"
      egg_shop_unpaid_total:
        friendly_name: "Egg Shop - Unpaid Total"
        unit_of_measurement: "EUR"
        value_template: "{{ state_attr('sensor.egg_shop_summary', 'total_unpaid_eur') }}"
      egg_shop_paid_this_month:
        friendly_name: "Egg Shop - Paid This Month"
        unit_of_measurement: "EUR"
        value_template: "{{ state_attr('sensor.egg_shop_summary', 'total_paid_this_month_eur') }}"
```

Add the token to `secrets.yaml`:

```yaml
eggshop_api_token: "the same value as HA_API_TOKEN in your .env, prefixed with 'Token '"
```

Note the header value must be the literal string `Token <your-token>` -
e.g. if `HA_API_TOKEN=abc123` in `.env`, the secret should be `Token abc123`.

## Example automation: notify on new order

```yaml
automation:
  - alias: "Notify on new egg order"
    trigger:
      - platform: numeric_state
        entity_id: sensor.egg_shop_new_orders
        above: 0
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "New egg order waiting to be confirmed 🥚"
```

## Going further (not included, but easy to add later)

If you want instant push updates instead of polling every few minutes, the
app could publish to an MQTT broker on every order/invoice change and rely
on Home Assistant's MQTT discovery instead of the REST sensor above. Given
the scale of this shop, polling every 5 minutes is simpler and plenty fast.
