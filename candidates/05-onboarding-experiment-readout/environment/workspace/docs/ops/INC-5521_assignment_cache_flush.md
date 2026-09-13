# INC-5521 - assignment cache flush

Experimentation Platform, 2026-07-30. Severity 3.

On 2026-07-29 at 14:00 UTC a cache flush during a Redis failover made the assignment service treat workspaces
assigned in the previous 20 days as unassigned when their owners next loaded the app. The service wrote new
assignment rows for about 6% of those workspaces, re-hashed with a different salt. Clients kept serving the variant
from their session cache.

Impact: extra rows in `xp_assignments` for XP-231 between 14:00 and 15:00 UTC; roughly half carry the other variant.
No data was deleted. Follow-up: XPP-51 (salt pinning).
