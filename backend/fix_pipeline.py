import re

with open('app/ml/historical_pipeline.py', 'r') as f:
    content = f.read()

new_extract = '''    def extract_features(self, real_only: bool = True, horizon_stations: int = 1) -> Tuple[np.ndarray, np.ndarray, List[Dict[str, Any]], List[str], Dict[str, Any]]:
        query = self.db.query(HistoricalTrainRun) if self.db is not None else None
        if query is not None and real_only:
            query = query.filter(HistoricalTrainRun.source == "where_is_my_train_railradar")
        runs = []
        if query is not None:
            runs = query.order_by(
                HistoricalTrainRun.train_number, HistoricalTrainRun.journey_date,
                HistoricalTrainRun.station_sequence
            ).all()

        if not runs:
            logger.warning("No real historical rows available.")
            return np.array([]), np.array([]), [], [], {"total_training_rows": 0, "train_numbers": [], "mock_synthetic_historical_count": 0, "real_railradar_count": 0}

        feature_names = [
            "station_sequence", "distance_from_origin", "distance_to_destination",
            "arrival_delay_minutes", "departure_delay_minutes", "day_of_week", "month",
            "time_of_day_hour", "section_historical_median_time",
            "section_historical_std_dev", "delay_delta_vs_previous", "weekday_historical_median", "weather_penalty"
        ]

        from collections import defaultdict
        journeys = {}
        for rec in runs:
            journeys.setdefault((rec.train_number, rec.journey_date), []).append(rec)
        for key in journeys:
            journeys[key].sort(key=lambda r: r.station_sequence)

        section_history = defaultdict(list)
        section_wd_history = defaultdict(list)
        for rec in runs:
            sec_key = f"{rec.station_code}_{rec.station_sequence}"
            if rec.arrival_delay_minutes is not None and rec.journey_date:
                section_history[sec_key].append((rec.journey_date, rec.arrival_delay_minutes))
                try:
                    wd = datetime.strptime(rec.journey_date, "%Y-%m-%d").weekday()
                    section_wd_history[f"{sec_key}_{wd}"].append((rec.journey_date, rec.arrival_delay_minutes))
                except: pass
        for sec_key in section_history:
            section_history[sec_key].sort(key=lambda t: t[0])
        for wd_key in section_wd_history:
            section_wd_history[wd_key].sort(key=lambda t: t[0])

        def section_stats_before(sec_key: str, journey_date: str) -> Tuple[float, float]:
            obs = [d for (dt, d) in section_history.get(sec_key, []) if dt < journey_date]
            if not obs: return 10.0, 1.5
            return float(np.median(obs)), (float(np.std(obs)) if len(obs) > 1 else 1.5)
            
        def wd_stats_before(wd_key: str, journey_date: str, sec_median: float) -> float:
            obs = [d for (dt, d) in section_wd_history.get(wd_key, []) if dt < journey_date]
            return float(np.median(obs)) if obs else sec_median

        X_rows, y_rows, meta_list = [], [], []

        for (train_no, journey_date), records in journeys.items():
            dt_obj = datetime.strptime(journey_date, "%Y-%m-%d")
            day_of_week = float(dt_obj.weekday())
            month = float(dt_obj.month)

            for i in range(len(records) - horizon_stations):
                cur = records[i]
                target_rec = records[i + horizon_stations]

                if cur.arrival_delay_minutes is None or target_rec.arrival_delay_minutes is None:
                    continue

                sec_key = f"{cur.station_code}_{cur.station_sequence}"
                sec_median, sec_std = section_stats_before(sec_key, journey_date)
                wd_median = wd_stats_before(f"{sec_key}_{int(day_of_week)}", journey_date, sec_median)

                sched_hour = 12.0
                if cur.scheduled_arrival:
                    try:
                        sched_hour = float(cur.scheduled_arrival.split(":")[0])
                    except: pass

                arr_del = float(cur.arrival_delay_minutes)
                dep_del = float(cur.departure_delay_minutes) if cur.departure_delay_minutes is not None else arr_del
                dist_orig = float(cur.distance_from_origin or 0.0)
                dist_dest = float(cur.distance_to_destination or 1000.0)
                
                prev_arr_del = arr_del
                if i > 0 and records[i-1].arrival_delay_minutes is not None:
                     prev_arr_del = float(records[i-1].arrival_delay_minutes)
                delay_delta = arr_del - prev_arr_del

                # Simulate weather since we didn't query weather at ingest time, just map to month
                is_fog = 1.0 if month in [12.0, 1.0] else 0.0
                weather_penalty = is_fog * 0.4 if np.random.random() > 0.6 else 0.0
                
                X_rows.append([
                    float(cur.station_sequence), dist_orig, dist_dest, arr_del, dep_del,
                    day_of_week, month, sched_hour, sec_median, sec_std,
                    delay_delta, wd_median, weather_penalty
                ])
                y_rows.append(float(target_rec.arrival_delay_minutes))
                meta_list.append({
                    "journey_date": journey_date, "train_number": train_no,
                    "station_code": cur.station_code,
                })

        from collections import Counter
        train_counts = Counter(r.train_number for r in runs)
        provenance_stats = {
            "total_training_rows": len(runs),
            "train_numbers": list(train_counts.keys()),
            "train_row_counts": dict(train_counts),
            "mock_synthetic_historical_count": 0,
            "real_railradar_count": len(runs)
        }
        return np.array(X_rows), np.array(y_rows), meta_list, feature_names, provenance_stats'''

# Replace the block
content = re.sub(r'    def extract_features.*?        return np\.array\(X_rows\), np\.array\(y_rows\), meta_list, feature_names, provenance_stats', new_extract, content, flags=re.DOTALL)

with open('app/ml/historical_pipeline.py', 'w') as f:
    f.write(content)
