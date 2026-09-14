import random, datetime as dt
from zoneinfo import ZoneInfo
CHI = ZoneInfo("America/Chicago"); UTC = dt.timezone.utc
random.seed(0)
def rand_local(day0):
    d = day0 + dt.timedelta(days=random.randrange(0, 360))
    if random.random() < 0.41: h = random.uniform(0, 6)
    else: h = random.uniform(6, 24)
    return dt.datetime(d.year, d.month, d.day, tzinfo=CHI) + dt.timedelta(hours=h)
res = {k: 0 for k in ["n","fwd_ok_local","fwd_elapsed24_naiveutc","fwd_caldate_utc_naive","back_n","back_gap_neg_naive","back_gap_neg_true","back_cal_utc_naive_in01","back_cal_local_in01"]}
day0 = dt.datetime(2026,1,1)
for i in range(20000):
    # forward H6 -> H1 : H6 discharge local, H1 admit 0.5-3h later
    dis = rand_local(day0); adm = dis + dt.timedelta(hours=random.uniform(0.5,3))
    dis_naive_as_utc = dis.replace(tzinfo=None).replace(tzinfo=UTC)     # faulty parse
    adm_utc = adm.astimezone(UTC)
    res["n"] += 1
    res["fwd_ok_local"] += (adm.astimezone(CHI).date() - dis.date()).days in (0,1)
    g = (adm_utc - dis_naive_as_utc).total_seconds()/3600
    res["fwd_elapsed24_naiveutc"] += 0 <= g <= 24
    res["fwd_caldate_utc_naive"] += (adm_utc.date() - dis_naive_as_utc.date()).days in (0,1)
    # back transfer H1 -> H6: H6 registration 0.5-3h BEFORE H1 discharge documented
    h1dis = rand_local(day0); h6adm = h1dis - dt.timedelta(hours=random.uniform(0.5,3))
    h6adm_naive_as_utc = h6adm.replace(tzinfo=None).replace(tzinfo=UTC)
    h1dis_utc = h1dis.astimezone(UTC)
    res["back_n"] += 1
    res["back_gap_neg_naive"] += (h6adm_naive_as_utc - h1dis_utc).total_seconds() < 0
    res["back_gap_neg_true"] += (h6adm - h1dis).total_seconds() < 0
    dd = (h6adm_naive_as_utc.date() - h1dis_utc.date()).days
    res["back_cal_utc_naive_in01"] += dd in (0,1)
    res["back_cal_local_in01"] += (h6adm.date() - h1dis.date()).days in (0,1) or h6adm < h1dis
print({k: (v if k in ("n","back_n") else round(v/ (res['n'] if not k.startswith('back') else res['back_n']),4)) for k,v in res.items()})
