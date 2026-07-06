# Journal

## 2026-07-05 — Health Report + tariff engine

Shipped the "diagnose the home, not the bill" pivot: `/properties/{id}/report`
built on two new services.

Decisions worth remembering:

- **Tariff slabs are encoded as declarative constants** in `services/tariff.py`
  (APSR residential: 14/18/32 bz at 4,000/6,000 kWh monthly, plus the summer-2026
  relief discounts). We treat thresholds as *monthly* — the relief program's
  per-month discount structure implies it, but this hasn't been verified against
  a real printed bill yet. If a real bill disagrees, fix the constants, not the
  engine.
- **Savings are priced at the marginal slab rate** (exact `cost(actual) - cost(baseline)`),
  not a blended average. This is the whole point of the tariff engine — for a
  heavy user the same saved kWh is worth ~2.3× the blended figure.
- **Headline waste = sum of timeline excess costs** (spikes vs trailing baseline).
  Rejected alternative: "efficient-self benchmark" (gap to best-3-months mean) —
  for AC-dominated electricity it compares summer to winter and wildly overstates
  waste. Same reason the timeline knowingly over-flags spring/summer ramp months:
  the trailing baseline is season-blind. The proper fix is weather normalization
  (cooling-degree-days from Open-Meteo), deliberately deferred — it changes the
  *baseline*, not the report structure, so it slots in later without rework.
- **Floor-rise leak detection** (recent 6-period min vs prior min, ≥1.3×) is the
  water headline feature — a continuous leak raises the *floor*, not the peaks.
  Its rec carries an honest annualized figure; recs whose savings can't be
  derived from data carry 0.0 (same doctrine as analysis.py: never invent money).
- Salalah seed intentionally stays at 5 bills to exercise the 422
  "needs more history" path end-to-end.

Ops gotcha (Windows): killing the uvicorn `--reload` parent leaves the
multiprocessing worker orphaned, still serving stale code on the inherited
socket — netstat shows the dead parent's PID as owner. Find the child via
`spawn_main(parent_pid=...)` in its command line and kill that.
