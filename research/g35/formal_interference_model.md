# G35 formal interference model

Written before the incident text, so the notation constrains the generator rather than decorating it.

## Units and indices

- **Block** `b = (c, t)`: one city `c` on one calendar day `t`.  A block is the operational **dispatch
  pool**: couriers signed on in city `c` on day `t` serve orders from merchants in city `c` on day `t`,
  and no others.  This is a fact of the dispatch system, not a modelling choice.
- **Merchant** `i in b`: a store in that block.  It is both the **experimental unit** and the
  **outcome unit**.
- **Interference group** of merchant `i` = every other merchant in the same block `b`.  Exactly the
  block; no partial or graded neighbourhood.

## Treatment and assignment

Two-stage randomisation.

1. Each block is assigned a **saturation** `pi_b` drawn uniformly from `{0, .25, .5, .75, 1}`,
   independently of everything else.
2. Within block `b`, exactly `round(pi_b * n_b)` of the `n_b` merchants are drawn without replacement
   to be **assigned** the dispatch-priority flag.  `Z_i = 1` for those merchants.

`A_i in {0,1}` denotes **adoption**: an assigned merchant that actually switches the feature on.
`P(A_i = 1 | Z_i = 1)` rises with merchant size.  Adoption is an outcome of assignment, never an input
to it.

## Exposure mapping

Merchant `i`'s outcome depends on its own assignment and on the block's treated load, and on nothing
else about who else was treated:

```
G_i(Z_-i)  =  ( sum_{j != i} d_j * A_j ) / ( sum_{j in b} d_j )
```

the demand-weighted share of the block running the new algorithm.  `d_j` is merchant `j`'s order
demand.  The mapping is **demand-weighted, not count-weighted**, because couriers are consumed by
orders rather than by stores - this is what makes count-weighted analyses wrong (W14).

## Potential outcome

```
Y_i ( Z_i , G_i(Z_-i) )
```

realised as the fraction of merchant `i`'s demand that is fulfilled.  Concretely the block rations a
capacity `S_b` across merchants in proportion to `d_j * w_j`, where the dispatch weight is

```
w_j = lambda   if merchant j is running the feature      (lambda > 1)
      1        otherwise
```

and the capacity itself responds to how much of the block runs the new routing logic:

```
S_b(G) = S_b^0 * ( 1 + delta * G )
```

`delta` is the **only** genuine efficiency in the system.  Everything the priority weight `lambda`
does is redistribution.

## Why interference is exact rather than approximate here

At `G = 1` every merchant has weight `lambda`, so the rationing shares `d_j*lambda / sum_k d_k*lambda`
are identical to the shares at `G = 0`.  Therefore

```
Y_i(1, 1)  -  Y_i(0, 0)   depends on delta ONLY.
```

The priority weight cancels exactly in the full-rollout contrast.  This is not a tuned property; it
follows from proportional rationing.  It is the reason the naive treated-minus-control comparison and
the deployment effect are different objects rather than differently-noisy estimates of one object.

## SUTVA, stated precisely

SUTVA fails in its **no-interference** component: `Y_i` depends on `Z_-i` through `G_i`.  It holds in
its **consistency** component: there is one version of the treatment.  The task is therefore not
"remember SUTVA" but "the experiment identifies several different estimands and you must produce the
one the deployment decision is written on".
