# Product warehouse - data dictionary (`data/product.db`)

All timestamps UTC.

| Table | Grain | Columns |
|-------|-------|---------|
| `workspaces` | one row per workspace | `workspace_id`, `created_at`, `plan`, `signup_channel` (self_serve / sales_assisted), `size_band`, `region`, `is_internal` (1 = internal test workspace) |
| `users` | one row per user | `user_id`, `created_at` |
| `memberships` | one row per (user, workspace) | `user_id`, `workspace_id`, `joined_at`, `role` (owner / member). A user can belong to several workspaces (agencies, consultants). |
| `experiments` | one row per experiment | `experiment_id`, `name`, `unit_type` (workspace / user), `started_on`, `status` |
| `xp_assignments` | one row per assignment write | `assignment_id`, `experiment_id`, `unit_type`, `unit_id` (workspace_id or user_id), `variant` (control / treatment), `stratum`, `assigned_at` |
| `exposure_events` | one row per logged exposure | `exposure_id`, `experiment_id`, `user_id`, `workspace_id` (workspace in context; null for user experiments outside a workspace), `variant` (as rendered by the SDK), `exposed_at` |
| `product_events` | one row per product event | `event_id`, `user_id`, `workspace_id`, `event_type`, `event_at` |
