import argparse
import glob
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.db.models import HistoricalTrainRun
from app.adapters.historical_data_adapter import WhereIsMyTrainHistoricalAdapter
from app.services.historical_normalizer import HistoricalNormalizer
from app.services.quality_checker import DataQualityChecker
from app.config import settings

RAW_DIR = settings.RAW_DATA_DIR if hasattr(settings, "RAW_DATA_DIR") else "../data/raw/where_is_my_train"
REAL_SOURCE = "where_is_my_train_railradar"
MOCK_SOURCE = "mock_synthetic_historical"


def audit_archive_files():
    print("\n=== ARCHIVE FILE AUDIT (data/raw/where_is_my_train) ===")
    train_dirs = sorted(glob.glob(os.path.join(RAW_DIR, "train_*")))
    if not train_dirs:
        print(f"  No archive directories found under {RAW_DIR}")
        return
    for d in train_dirs:
        train_no = os.path.basename(d).replace("train_", "")
        files = sorted(glob.glob(os.path.join(d, "*.json")))
        counts = Counter()
        for fp in files:
            try:
                with open(fp) as f:
                    src = json.load(f).get("source", "UNKNOWN")
                counts[src] += 1
            except Exception:
                counts["UNREADABLE"] += 1
        real_n = counts.get(REAL_SOURCE, 0)
        mock_n = counts.get(MOCK_SOURCE, 0)
        pct_real = (100.0 * real_n / len(files)) if files else 0.0
        print(f"  Train {train_no}: {len(files)} files | real={real_n} mock={mock_n} "
              f"other={sum(counts.values()) - real_n - mock_n} | {pct_real:.1f}% real")


def audit_database():
    print("\n=== DATABASE AUDIT (historical_train_runs) ===")
    db = SessionLocal()
    try:
        rows = db.query(HistoricalTrainRun).all()
        if not rows:
            print("  Table is empty.")
            return
        per_train = defaultdict(Counter)
        for r in rows:
            per_train[r.train_number][r.source or "UNKNOWN"] += 1
        for train_no, counts in per_train.items():
            total = sum(counts.values())
            real_n = counts.get(REAL_SOURCE, 0)
            print(f"  Train {train_no}: {total} rows | real={real_n} "
                  f"mock={counts.get(MOCK_SOURCE, 0)} | {100.0*real_n/total:.1f}% real")
        all_trains = set(rows[0].__class__.__table__.columns)  # noqa (keep simple)
        trains_present = set(per_train.keys())
        print(f"  Trains present in DB: {sorted(trains_present)}")
    finally:
        db.close()


def run_real_backfill(train_numbers, start_date, end_date, require_real, max_days=None):
    print(f"\n=== REAL BACKFILL: trains={train_numbers} {start_date}..{end_date} "
          f"(require_real={require_real}) ===")
    db = SessionLocal()
    adapter = WhereIsMyTrainHistoricalAdapter()
    try:
        for train_no in train_numbers:
            print(f"\n-- Train {train_no} --")
            from datetime import datetime, timedelta
            curr = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            written, skipped_mock, failed = 0, 0, 0
            days_done = 0
            while curr <= end:
                date_str = curr.strftime("%Y-%m-%d")
                raw = adapter.fetch_train_day(train_no, date_str)

                if raw is None:
                    failed += 1
                    curr += timedelta(days=1)
                    continue

                if raw.get("source") != REAL_SOURCE:
                    # The adapter silently fell back to synthetic. In a real-only
                    # backfill we do NOT want that written to the DB unlabeled.
                    skipped_mock += 1
                    if require_real:
                        print(f"  STOPPING at {date_str}: live API unavailable, "
                              f"adapter would have used synthetic fallback. "
                              f"{written} real days collected so far for {train_no}.")
                        break
                    curr += timedelta(days=1)
                    continue

                normalized = HistoricalNormalizer.normalize_journey(raw)
                validated = DataQualityChecker.validate_records(normalized)
                for rec in validated["valid_records"]:
                    db.add(rec)
                db.commit()
                written += len(validated["valid_records"])

                curr += timedelta(days=1)
                days_done += 1
                if max_days and days_done >= max_days:
                    break

            print(f"  Train {train_no}: wrote {written} real rows, "
                  f"skipped {skipped_mock} days (API unavailable), {failed} hard failures.")
    finally:
        db.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--audit-only", action="store_true")
    p.add_argument("--train", action="append", default=[])
    p.add_argument("--start", default="2024-01-01")
    p.add_argument("--end", default="2026-08-23")
    p.add_argument("--require-real", action="store_true",
                    help="Stop at the first non-real response instead of silently skipping/mocking.")
    p.add_argument("--max-days", type=int, default=None)
    args = p.parse_args()

    audit_archive_files()
    audit_database()

    if not args.audit_only:
        trains = args.train or ["12302", "12951"]
        run_real_backfill(trains, args.start, args.end, args.require_real, args.max_days)
        print("\nRe-run with --audit-only to confirm the new real-row counts.")
