# LEAN-26 working-capital programme

Owner: Finance Transformation, with Supply Planning.

- **Goal:** reduce store inventory by about 25% without material sales loss.
- **Change:** the replenishment multiplier drops from 1.8 to 1.25 in the programme stores (12 of 16 in the current estate). At the same go-live, those
  stores switch from forecast v3 to v4.
- **Go-live:** see `programme_assignment.go_live_date`.
- **Holdout design:** four stores keep the previous multiplier and v3, to measure programme impact. Holdout stores
  were drawn at random within delivery slot (`programme_assignment.randomisation_block`) before go-live.
- **Readout plan:** week-8 readout on sales and inventory value; extension to the holdout stores to be decided after
  the Q3 review.
