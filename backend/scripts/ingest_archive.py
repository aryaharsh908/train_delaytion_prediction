import os
import sys
import glob
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal, engine
from app.db.models import Base, HistoricalTrainRun
from app.services.historical_normalizer import HistoricalNormalizer
from app.services.quality_checker import DataQualityChecker
from app.config import settings

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    print("--- Purging Existing Data ---")
    db.query(HistoricalTrainRun).delete()
    db.commit()
    print("Database purged. It is now 100% clean.")
    
    raw_dir = settings.RAW_DATA_DIR
    print(f"--- Scanning Offline Archive: {raw_dir} ---")
    
    search_path = os.path.join(raw_dir, "train_*", "*.json")
    files = glob.glob(search_path)
    
    print(f"Found {len(files)} total JSON files. Filtering for 'where_is_my_train_railradar'...")
    
    real_files_count = 0
    records_inserted = 0
    
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_json = json.load(f)
                
            if raw_json.get("source") == "where_is_my_train_railradar":
                real_files_count += 1
                
                normalized = HistoricalNormalizer.normalize_journey(raw_json)
                validated = DataQualityChecker.validate_records(normalized)
                
                if validated["valid_records"]:
                    for rec in validated["valid_records"]:
                        db.add(rec)
                    db.commit()
                    records_inserted += len(validated["valid_records"])
        except Exception as e:
            # Safely skip unreadable or malformed files
            pass
            
    print(f"\n--- Ingestion Complete ---")
    print(f"Real API JSON Files Processed: {real_files_count}")
    print(f"Total Genuine Real Rows Inserted: {records_inserted}")
    
    if records_inserted > 0:
        print("\nDB now solely contains genuine historical data.")
    else:
        print("\n[!] WARNING: Zero genuine data found in archive. DB is empty.")

if __name__ == "__main__":
    main()
