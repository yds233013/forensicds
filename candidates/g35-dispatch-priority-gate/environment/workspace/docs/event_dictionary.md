# Extract dictionary - priority-dispatch pilot

| table | column | meaning |
|---|---|---|
| `merchants` | `merchant_id`, `city_id`, `merchant_name`, `cuisine` | merchant master |
| `block_assignment` | `block_id` | one dispatch pool: a city on a service date |
| | `city_id`, `service_date` | which pool |
| | `assigned_saturation` | the target share of that pool's merchants drawn for priority, decided the night before |
| | `assigned_at` | when the draw was written |
| `merchant_assignment` | `block_id`, `merchant_id`, `assigned_priority` | 1 if that merchant was drawn for priority in that pool |
| `priority_activation` | `block_id`, `merchant_id`, `activated` | 1 if the merchant actually turned the flag on. Rows exist only for merchants that were assigned priority |
| `merchant_day_orders` | `block_id`, `merchant_id`, `orders_requested` | orders customers placed |
| | `orders_delivered` | orders completed by a courier |
| `extract_meta` | `key`, `value` | window, outcome definition, randomisation description |

**Fulfilment rate** = `orders_delivered / orders_requested`.

Every merchant in a city appears on every service date in the window.
