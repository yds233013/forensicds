# Home-row engagement metric

Owner: Personalisation Analytics.

- **Metric: home-row clicks per slate decision.** The number of the row's five slots that the member clicked,
  averaged over slate decisions. Slots the member never looked at count as zero, not as missing.
- **Slate decision:** one ranking choice for a member. The service makes the choice once and then keeps returning it
  for that member's session on that surface until the stored response expires; a later request that gets a fresh
  ranking is a new decision.
- **Serve:** one response returned to a client. A decision can be served more than once.
- **Click:** a click on a title in the row. A member can click more than one slot of a decision; a slot counts once.

This metric is the one the launch policy refers to. Click-through rate per response and click-through rate per
rendered impression are reporting conveniences and are not the launch metric: both depend on how often clients
re-request the row, which itself depends on what was served.
