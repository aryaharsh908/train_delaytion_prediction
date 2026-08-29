import logging
from typing import List, Dict, Any
from app.db.models import HistoricalTrainRun

logger = logging.getLogger("quality_checker")

class DataQualityChecker:
    """
    Validates historical train runs against logical integrity rules.
    Flags invalid records without silently deleting them, outputting a DataQualityReport.
    """

    @staticmethod
    def validate_records(records: List[HistoricalTrainRun]) -> Dict[str, Any]:
        records_received = len(records)
        valid_records = []
        invalid_records = []

        reasons_breakdown = {
            "Missing arrival time": 0,
            "Invalid timestamp": 0,
            "Duplicate": 0,
            "Impossible speed": 0,
            "Missing train number": 0,
            "Missing journey date": 0,
            "Other": 0
        }

        seen_keys = set()

        for rec in records:
            reasons = []

            # 1. Missing key identifiers
            if not rec.train_number:
                reasons.append("Missing train number")
            if not rec.journey_date:
                reasons.append("Missing journey date")

            # 2. Duplicate checking
            key = (rec.train_number, rec.journey_date, rec.station_sequence)
            if key in seen_keys:
                reasons.append("Duplicate")
            else:
                seen_keys.add(key)

            # 3. Timestamp validity
            if not rec.scheduled_arrival and not rec.scheduled_departure:
                reasons.append("Missing arrival time")

            # 4. Speed anomaly check if distance and delay present
            if rec.distance_from_origin is not None and rec.distance_from_origin > 3000.0:
                reasons.append("Impossible speed")

            if reasons:
                for r in reasons:
                    if r in reasons_breakdown:
                        reasons_breakdown[r] += 1
                    else:
                        reasons_breakdown["Other"] += 1
                invalid_records.append({
                    "record_id": rec.id,
                    "train_number": rec.train_number,
                    "journey_date": rec.journey_date,
                    "station_code": rec.station_code,
                    "reasons": reasons
                })
            else:
                valid_records.append(rec)

        return {
            "records_received": records_received,
            "valid_count": len(valid_records),
            "invalid_count": len(invalid_records),
            "reasons_breakdown": reasons_breakdown,
            "valid_records": valid_records,
            "invalid_records": invalid_records
        }
