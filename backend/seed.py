"""Seed a demo account with sample bills so the analysis has something to chew on.

Runs against the live API (server must be up). Idempotent: if the demo user
already has properties, it does nothing.

    python seed.py            # uses http://127.0.0.1:8000
    BASEERAH_API=http://... python seed.py
"""

import os
import sys

import httpx

API = os.environ.get("BASEERAH_API", "http://127.0.0.1:8000")
EMAIL = "demo@baseerah.om"
PASSWORD = "demo12345"

# (name, type, region, [(utility, [(period_start, period_end, consumption, cost)])])
PROPERTIES = [
    (
        "Muscat Villa",
        "villa",
        "Muscat",
        {
            # water at 2.5 OMR/m3: stable floor (~11 m3) through 2025, then a
            # slow leak from Jan 2026 lifts the *floor* to ~15 -> floor-rise leak
            "water": [
                ("2025-01-01", "2025-01-31", 12, 30.0),
                ("2025-02-01", "2025-02-28", 11, 27.5),
                ("2025-03-01", "2025-03-31", 13, 32.5),
                ("2025-04-01", "2025-04-30", 12, 30.0),
                ("2025-05-01", "2025-05-31", 12, 30.0),
                ("2025-06-01", "2025-06-30", 14, 35.0),
                ("2025-07-01", "2025-07-31", 15, 37.5),
                ("2025-08-01", "2025-08-31", 14, 35.0),
                ("2025-09-01", "2025-09-30", 13, 32.5),
                ("2025-10-01", "2025-10-31", 12, 30.0),
                ("2025-11-01", "2025-11-30", 11, 27.5),
                ("2025-12-01", "2025-12-31", 12, 30.0),
                ("2026-01-01", "2026-01-31", 15, 37.5),
                ("2026-02-01", "2026-02-28", 16, 40.0),
                ("2026-03-01", "2026-03-31", 15, 37.5),
                ("2026-04-01", "2026-04-30", 17, 42.5),
                ("2026-05-01", "2026-05-31", 16, 40.0),
                ("2026-06-01", "2026-06-30", 15, 37.5),
            ],
            # electricity: AC-driven seasonal swing, costs from APSR slab rates
            # (14 bz <= 4000 kWh, 18 bz above; May-Aug 2026 summer relief applied).
            # June 2026 lands 340 kWh below the 4000 slab threshold.
            "electricity": [
                ("2025-01-01", "2025-01-31", 1500, 21.0),
                ("2025-02-01", "2025-02-28", 1450, 20.3),
                ("2025-03-01", "2025-03-31", 1600, 22.4),
                ("2025-04-01", "2025-04-30", 2100, 29.4),
                ("2025-05-01", "2025-05-31", 2900, 40.6),
                ("2025-06-01", "2025-06-30", 3800, 53.2),
                ("2025-07-01", "2025-07-31", 4200, 59.6),
                ("2025-08-01", "2025-08-31", 4100, 57.8),
                ("2025-09-01", "2025-09-30", 3300, 46.2),
                ("2025-10-01", "2025-10-31", 2400, 33.6),
                ("2025-11-01", "2025-11-30", 1700, 23.8),
                ("2025-12-01", "2025-12-31", 1500, 21.0),
                ("2026-01-01", "2026-01-31", 1480, 20.72),
                ("2026-02-01", "2026-02-28", 1520, 21.28),
                ("2026-03-01", "2026-03-31", 1650, 23.1),
                ("2026-04-01", "2026-04-30", 2200, 30.8),
                ("2026-05-01", "2026-05-31", 3000, 35.7),
                ("2026-06-01", "2026-06-30", 3660, 40.99),
            ],
        },
    ),
    (
        "Salalah Apartment",
        "apartment",
        "Salalah",
        {
            # normal, no anomaly
            "water": [
                ("2026-01-01", "2026-01-31", 8, 20.0),
                ("2026-02-01", "2026-02-28", 9, 22.5),
                ("2026-03-01", "2026-03-31", 8, 20.0),
                ("2026-04-01", "2026-04-30", 9, 22.5),
                ("2026-05-01", "2026-05-31", 8, 20.0),
            ],
            "electricity": [
                ("2026-01-01", "2026-01-31", 300, 7.5),
                ("2026-02-01", "2026-02-28", 310, 7.75),
                ("2026-03-01", "2026-03-31", 305, 7.6),
                ("2026-04-01", "2026-04-30", 320, 8.0),
                ("2026-05-01", "2026-05-31", 310, 7.75),
            ],
        },
    ),
]


def main() -> None:
    with httpx.Client(base_url=API, timeout=10) as c:
        # register (ignore if already exists), then log in
        c.post("/auth/register", json={"email": EMAIL, "name": "Demo User", "password": PASSWORD})
        r = c.post("/auth/login", data={"username": EMAIL, "password": PASSWORD})
        r.raise_for_status()
        token = r.json()["access_token"]
        c.headers["Authorization"] = f"Bearer {token}"

        existing = c.get("/properties").json()
        if existing:
            print(f"Demo user already has {len(existing)} properties — nothing to seed.")
            _print_login()
            return

        for name, ptype, region, utilities in PROPERTIES:
            prop = c.post(
                "/properties",
                json={"name": name, "type": ptype, "region": region},
            ).json()
            pid = prop["id"]
            count = 0
            for utility, bills in utilities.items():
                for start, end, cons, cost in bills:
                    resp = c.post(
                        f"/properties/{pid}/bills",
                        json={
                            "utility_type": utility,
                            "period_start": start,
                            "period_end": end,
                            "consumption": cons,
                            "cost": cost,
                        },
                    )
                    resp.raise_for_status()
                    count += 1
            print(f"Created '{name}' with {count} bills.")

        _print_login()


def _print_login() -> None:
    print("\nLog in at the frontend with:")
    print(f"  email:    {EMAIL}")
    print(f"  password: {PASSWORD}")
    print("\nThen open a property and click Analyze:")
    print("  - Muscat Villa / water  -> floor-rise leak (from Jan 2026)")
    print("  - Muscat Villa / electricity -> seasonal history, near slab threshold")
    print("  - Salalah Apartment -> normal; too little history for a health report")


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as e:
        print(f"Seeding failed: {e}", file=sys.stderr)
        print("Is the backend running at", API, "?", file=sys.stderr)
        sys.exit(1)
