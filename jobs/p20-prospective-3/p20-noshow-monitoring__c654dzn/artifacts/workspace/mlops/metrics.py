"""Discrimination and rate helpers."""


def auc(scores, labels):
    pairs = sorted(zip(scores, labels))
    n = len(pairs)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        r = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = r
        i = j + 1
    pos = sum(1 for _, y in pairs if y == 1)
    neg = n - pos
    if pos == 0 or neg == 0:
        return None
    s = sum(r for r, (_, y) in zip(ranks, pairs) if y == 1)
    return (s - pos * (pos + 1) / 2.0) / (pos * neg)


def no_show_rate_pct(rows):
    return 100.0 * sum(r["no_show"] for r in rows) / len(rows) if rows else None
