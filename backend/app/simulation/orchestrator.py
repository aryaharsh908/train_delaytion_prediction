import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from app.graph.railway_graph import RailwayNetworkGraph
from app.ml.predictor import ETAPredictor
from app.ml.online_updater import OnlineSectionUpdater
from app.filters.kalman_filter import TrainTelemetryFilter
from app.filters.changepoint_detector import CUSUMChangePointDetector
from app.filters.anomaly_detector import AnomalyDetector
from app.propagation.delay_propagator import DelayPropagationEngine, CascadingDelayEngine
from app.monte_carlo.simulator import MonteCarloETASimulator
from app.explainability.explainer import ETAExplainer
from app.simulation.rtis_simulator import RTISSimulator
from app.simulation.coa_simulator import COASimulator
from app.simulation.event_simulator import IncidentEventSimulator
from app.schemas.schemas import ETAPredictionSchema, TrainStateSchema, SimulationStateSchema



# Comprehensive Route Catalog for ALL 10 Iconic Train Corridors
route_catalogs = {
    "12951": [
        {"code": "NDLS", "name": "New Delhi", "dist": 0.0, "sched_arr": "16:55", "sched_dep": "16:55", "platform": "16"},
        {"code": "MTJ", "name": "Mathura Junction", "dist": 141.0, "sched_arr": "18:24", "sched_dep": "18:26", "platform": "3"},
        {"code": "KOTA", "name": "Kota Junction", "dist": 465.0, "sched_arr": "21:40", "sched_dep": "21:50", "platform": "1"},
        {"code": "RTM", "name": "Ratlam Junction", "dist": 731.0, "sched_arr": "00:45", "sched_dep": "00:50", "platform": "4"},
        {"code": "BRC", "name": "Vadodara Junction", "dist": 992.0, "sched_arr": "03:48", "sched_dep": "03:58", "platform": "1"},
        {"code": "ST", "name": "Surat", "dist": 1122.0, "sched_arr": "05:33", "sched_dep": "05:38", "platform": "1"},
        {"code": "BVI", "name": "Borivali", "dist": 1355.0, "sched_arr": "07:55", "sched_dep": "07:57", "platform": "7"},
        {"code": "MMCT", "name": "Mumbai Central", "dist": 1385.0, "sched_arr": "08:35", "sched_dep": "08:35", "platform": "5"}
    ],
    "12302": [
        {"code": "NDLS", "name": "New Delhi", "dist": 0.0, "sched_arr": "16:50", "sched_dep": "16:50", "platform": "9"},
        {"code": "CNB", "name": "Kanpur Central", "dist": 440.0, "sched_arr": "21:32", "sched_dep": "21:37", "platform": "5"},
        {"code": "PRYJ", "name": "Prayagraj Junction", "dist": 634.0, "sched_arr": "23:43", "sched_dep": "23:45", "platform": "4"},
        {"code": "DDU", "name": "Pt. Deen Dayal Upadhyaya", "dist": 787.0, "sched_arr": "01:47", "sched_dep": "01:57", "platform": "2"},
        {"code": "GAYA", "name": "Gaya Junction", "dist": 992.0, "sched_arr": "04:10", "sched_dep": "04:13", "platform": "1"},
        {"code": "DHN", "name": "Dhanbad Junction", "dist": 1193.0, "sched_arr": "06:55", "sched_dep": "07:00", "platform": "2"},
        {"code": "ASN", "name": "Asansol Junction", "dist": 1251.0, "sched_arr": "07:50", "sched_dep": "07:52", "platform": "5"},
        {"code": "HWH", "name": "Howrah Junction", "dist": 1449.0, "sched_arr": "09:55", "sched_dep": "09:55", "platform": "9"}
    ],
    "12626": [
        {"code": "NDLS", "name": "New Delhi", "dist": 0.0, "sched_arr": "20:10", "sched_dep": "20:10", "platform": "3"},
        {"code": "MTJ", "name": "Mathura Junction", "dist": 141.0, "sched_arr": "21:40", "sched_dep": "21:42", "platform": "2"},
        {"code": "AGC", "name": "Agra Cantt", "dist": 195.0, "sched_arr": "22:35", "sched_dep": "22:40", "platform": "1"},
        {"code": "DHO", "name": "Dholpur Junction", "dist": 248.0, "sched_arr": "23:23", "sched_dep": "23:25", "platform": "1"},
        {"code": "MRA", "name": "Morena", "dist": 275.0, "sched_arr": "23:43", "sched_dep": "23:45", "platform": "1"},
        {"code": "GWL", "name": "Gwalior Junction", "dist": 313.0, "sched_arr": "00:08", "sched_dep": "00:10", "platform": "1"},
        {"code": "VGLJ", "name": "VGL Jhansi", "dist": 411.0, "sched_arr": "01:30", "sched_dep": "01:38", "platform": "2"},
        {"code": "LAR", "name": "Lalitpur Junction", "dist": 501.0, "sched_arr": "02:40", "sched_dep": "02:42", "platform": "2"},
        {"code": "BINA", "name": "Bina Junction", "dist": 564.0, "sched_arr": "03:45", "sched_dep": "03:50", "platform": "3"},
        {"code": "BPL", "name": "Bhopal Junction", "dist": 702.0, "sched_arr": "05:20", "sched_dep": "05:25", "platform": "1"},
        {"code": "RKMP", "name": "Rani Kamlapati", "dist": 708.0, "sched_arr": "05:35", "sched_dep": "05:37", "platform": "4"},
        {"code": "ET", "name": "Itarsi Junction", "dist": 794.0, "sched_arr": "07:10", "sched_dep": "07:20", "platform": "2"},
        {"code": "GDYA", "name": "Ghoradongri", "dist": 864.0, "sched_arr": "08:24", "sched_dep": "08:25", "platform": "2"},
        {"code": "BZU", "name": "Betul", "dist": 901.0, "sched_arr": "09:03", "sched_dep": "09:05", "platform": "1"},
        {"code": "AMLA", "name": "Amla Junction", "dist": 924.0, "sched_arr": "09:26", "sched_dep": "09:28", "platform": "2"},
        {"code": "MTY", "name": "Multai", "dist": 951.0, "sched_arr": "09:47", "sched_dep": "09:48", "platform": "1"},
        {"code": "PAR", "name": "Pandhurna", "dist": 992.0, "sched_arr": "10:24", "sched_dep": "10:25", "platform": "1"},
        {"code": "NRKR", "name": "Narkher Junction", "dist": 1010.0, "sched_arr": "10:41", "sched_dep": "10:42", "platform": "1"},
        {"code": "NGP", "name": "Nagpur Junction", "dist": 1092.0, "sched_arr": "11:45", "sched_dep": "11:50", "platform": "2"},
        {"code": "SEGM", "name": "Sevagram Junction", "dist": 1168.0, "sched_arr": "12:53", "sched_dep": "12:55", "platform": "4"},
        {"code": "HGT", "name": "Hinganghat", "dist": 1195.0, "sched_arr": "13:18", "sched_dep": "13:20", "platform": "1"},
        {"code": "CD", "name": "Chandrapur", "dist": 1271.0, "sched_arr": "14:18", "sched_dep": "14:20", "platform": "1"},
        {"code": "BPQ", "name": "Balharshah", "dist": 1285.0, "sched_arr": "15:20", "sched_dep": "15:25", "platform": "1"},
        {"code": "SKZR", "name": "Sirpur Kaghaznagar", "dist": 1355.0, "sched_arr": "16:14", "sched_dep": "16:15", "platform": "2"},
        {"code": "RDM", "name": "Ramagundam", "dist": 1427.0, "sched_arr": "17:09", "sched_dep": "17:10", "platform": "2"},
        {"code": "PDPL", "name": "Peddapalli Junction", "dist": 1445.0, "sched_arr": "17:24", "sched_dep": "17:25", "platform": "2"},
        {"code": "WL", "name": "Warangal", "dist": 1528.0, "sched_arr": "18:38", "sched_dep": "18:40", "platform": "1"},
        {"code": "KMT", "name": "Khammam", "dist": 1636.0, "sched_arr": "20:08", "sched_dep": "20:10", "platform": "1"},
        {"code": "BZA", "name": "Vijayawada Junction", "dist": 1735.0, "sched_arr": "21:30", "sched_dep": "21:40", "platform": "6"},
        {"code": "NLR", "name": "Nellore", "dist": 1990.0, "sched_arr": "01:03", "sched_dep": "01:05", "platform": "3"},
        {"code": "GDR", "name": "Gudur Junction", "dist": 2029.0, "sched_arr": "02:08", "sched_dep": "02:10", "platform": "1"},
        {"code": "RU", "name": "Renigunta Junction", "dist": 2112.0, "sched_arr": "03:30", "sched_dep": "03:35", "platform": "3"},
        {"code": "TPTY", "name": "Tirupati", "dist": 2122.0, "sched_arr": "04:00", "sched_dep": "04:05", "platform": "1"},
        {"code": "CTO", "name": "Chittoor", "dist": 2194.0, "sched_arr": "05:14", "sched_dep": "05:15", "platform": "1"},
        {"code": "KPD", "name": "Katpadi Junction", "dist": 2227.0, "sched_arr": "06:10", "sched_dep": "06:15", "platform": "3"},
        {"code": "JTJ", "name": "Jolarpettai Junction", "dist": 2311.0, "sched_arr": "07:43", "sched_dep": "07:45", "platform": "1"},
        {"code": "SA", "name": "Salem Junction", "dist": 2432.0, "sched_arr": "09:22", "sched_dep": "09:25", "platform": "4"},
        {"code": "ED", "name": "Erode Junction", "dist": 2491.0, "sched_arr": "10:30", "sched_dep": "10:35", "platform": "2"},
        {"code": "TUP", "name": "Tiruppur", "dist": 2542.0, "sched_arr": "11:23", "sched_dep": "11:25", "platform": "1"},
        {"code": "CBE", "name": "Coimbatore Junction", "dist": 2592.0, "sched_arr": "12:22", "sched_dep": "12:25", "platform": "2"},
        {"code": "PGT", "name": "Palakkad Junction", "dist": 2648.0, "sched_arr": "13:42", "sched_dep": "13:45", "platform": "1"},
        {"code": "TCR", "name": "Thrissur", "dist": 2723.0, "sched_arr": "14:57", "sched_dep": "15:00", "platform": "1"},
        {"code": "AWY", "name": "Aluva", "dist": 2778.0, "sched_arr": "15:48", "sched_dep": "15:50", "platform": "1"},
        {"code": "ERN", "name": "Ernakulam Town", "dist": 2795.0, "sched_arr": "16:20", "sched_dep": "16:25", "platform": "2"},
        {"code": "KTYM", "name": "Kottayam", "dist": 2855.0, "sched_arr": "17:32", "sched_dep": "17:35", "platform": "1"},
        {"code": "CNGR", "name": "Chengannur", "dist": 2890.0, "sched_arr": "18:11", "sched_dep": "18:13", "platform": "1"},
        {"code": "QLN", "name": "Kollam Junction", "dist": 2951.0, "sched_arr": "19:12", "sched_dep": "19:15", "platform": "1"},
        {"code": "TVC", "name": "Trivandrum Central", "dist": 3016.0, "sched_arr": "21:00", "sched_dep": "21:00", "platform": "1"}
    ],
    "12952": [
        {"code": "MMCT", "name": "Mumbai Central", "dist": 0.0, "sched_arr": "17:00", "sched_dep": "17:00", "platform": "5"},
        {"code": "BVI", "name": "Borivali", "dist": 30.0, "sched_arr": "17:33", "sched_dep": "17:35", "platform": "6"},
        {"code": "ST", "name": "Surat", "dist": 263.0, "sched_arr": "19:43", "sched_dep": "19:48", "platform": "1"},
        {"code": "BRC", "name": "Vadodara Junction", "dist": 393.0, "sched_arr": "21:16", "sched_dep": "21:26", "platform": "2"},
        {"code": "RTM", "name": "Ratlam Junction", "dist": 654.0, "sched_arr": "00:30", "sched_dep": "00:35", "platform": "5"},
        {"code": "KOTA", "name": "Kota Junction", "dist": 920.0, "sched_arr": "03:15", "sched_dep": "03:25", "platform": "1"},
        {"code": "MTJ", "name": "Mathura Junction", "dist": 1244.0, "sched_arr": "06:43", "sched_dep": "06:45", "platform": "3"},
        {"code": "NDLS", "name": "New Delhi", "dist": 1385.0, "sched_arr": "08:32", "sched_dep": "08:32", "platform": "3"}
    ],
    "12002": [
        {"code": "NDLS", "name": "New Delhi", "dist": 0.0, "sched_arr": "06:00", "sched_dep": "06:00", "platform": "1"},
        {"code": "MTJ", "name": "Mathura Junction", "dist": 141.0, "sched_arr": "07:19", "sched_dep": "07:20", "platform": "1"},
        {"code": "AGC", "name": "Agra Cantt", "dist": 195.0, "sched_arr": "07:50", "sched_dep": "07:55", "platform": "1"},
        {"code": "GWL", "name": "Gwalior Junction", "dist": 313.0, "sched_arr": "09:23", "sched_dep": "09:25", "platform": "1"},
        {"code": "VGLJ", "name": "VGL Jhansi", "dist": 411.0, "sched_arr": "10:45", "sched_dep": "10:50", "platform": "2"},
        {"code": "LAR", "name": "Lalitpur Junction", "dist": 501.0, "sched_arr": "11:42", "sched_dep": "11:43", "platform": "2"},
        {"code": "BINA", "name": "Bina Junction", "dist": 564.0, "sched_arr": "12:38", "sched_dep": "12:40", "platform": "3"},
        {"code": "BPL", "name": "Bhopal Junction", "dist": 702.0, "sched_arr": "14:12", "sched_dep": "14:15", "platform": "1"},
        {"code": "RKMP", "name": "Rani Kamlapati", "dist": 708.0, "sched_arr": "14:40", "sched_dep": "14:40", "platform": "5"}
    ],
    "12424": [
        {"code": "NDLS", "name": "New Delhi", "dist": 0.0, "sched_arr": "16:20", "sched_dep": "16:20", "platform": "16"},
        {"code": "CNB", "name": "Kanpur Central", "dist": 440.0, "sched_arr": "21:02", "sched_dep": "21:07", "platform": "5"},
        {"code": "PRYJ", "name": "Prayagraj Junction", "dist": 634.0, "sched_arr": "23:08", "sched_dep": "23:10", "platform": "4"},
        {"code": "DDU", "name": "Pt. Deen Dayal Upadhyaya", "dist": 787.0, "sched_arr": "01:05", "sched_dep": "01:15", "platform": "2"},
        {"code": "PPTA", "name": "Patliputra Junction", "dist": 995.0, "sched_arr": "03:50", "sched_dep": "04:00", "platform": "2"},
        {"code": "BJU", "name": "Barauni Junction", "dist": 1103.0, "sched_arr": "06:35", "sched_dep": "06:45", "platform": "4"},
        {"code": "NJP", "name": "New Jalpaiguri", "dist": 1475.0, "sched_arr": "13:05", "sched_dep": "13:15", "platform": "1"},
        {"code": "GHY", "name": "Guwahati", "dist": 1882.0, "sched_arr": "20:00", "sched_dep": "20:15", "platform": "1"},
        {"code": "DBRG", "name": "Dibrugarh", "dist": 2445.0, "sched_arr": "07:00", "sched_dep": "07:00", "platform": "1"}
    ],
    "12958": [
        {"code": "NDLS", "name": "New Delhi", "dist": 0.0, "sched_arr": "19:55", "sched_dep": "19:55", "platform": "1"},
        {"code": "DEC", "name": "Delhi Cantt", "dist": 15.0, "sched_arr": "20:25", "sched_dep": "20:27", "platform": "1"},
        {"code": "GGN", "name": "Gurgaon", "dist": 32.0, "sched_arr": "20:43", "sched_dep": "20:45", "platform": "1"},
        {"code": "JP", "name": "Jaipur Junction", "dist": 308.0, "sched_arr": "23:45", "sched_dep": "23:55", "platform": "1"},
        {"code": "AII", "name": "Ajmer Junction", "dist": 443.0, "sched_arr": "01:50", "sched_dep": "01:55", "platform": "2"},
        {"code": "ABR", "name": "Abu Road", "dist": 748.0, "sched_arr": "05:55", "sched_dep": "06:05", "platform": "1"},
        {"code": "ADI", "name": "Ahmedabad Junction", "dist": 934.0, "sched_arr": "09:30", "sched_dep": "09:30", "platform": "1"}
    ],
    "12425": [
        {"code": "NDLS", "name": "New Delhi", "dist": 0.0, "sched_arr": "20:40", "sched_dep": "20:40", "platform": "15"},
        {"code": "UMB", "name": "Ambala Cantt", "dist": 199.0, "sched_arr": "23:00", "sched_dep": "23:02", "platform": "7"},
        {"code": "LDH", "name": "Ludhiana Junction", "dist": 313.0, "sched_arr": "00:28", "sched_dep": "00:38", "platform": "2"},
        {"code": "JRC", "name": "Jalandhar Cantt", "dist": 365.0, "sched_arr": "01:23", "sched_dep": "01:25", "platform": "1"},
        {"code": "PTKC", "name": "Pathankot Cantt", "dist": 478.0, "sched_arr": "03:08", "sched_dep": "03:10", "platform": "2"},
        {"code": "JAT", "name": "Jammu Tawi", "dist": 577.0, "sched_arr": "05:00", "sched_dep": "05:00", "platform": "3"}
    ],
    "12622": [
        {"code": "NDLS", "name": "New Delhi", "dist": 0.0, "sched_arr": "21:05", "sched_dep": "21:05", "platform": "3"},
        {"code": "AGC", "name": "Agra Cantt", "dist": 195.0, "sched_arr": "23:28", "sched_dep": "23:30", "platform": "1"},
        {"code": "GWL", "name": "Gwalior Junction", "dist": 313.0, "sched_arr": "01:13", "sched_dep": "01:15", "platform": "1"},
        {"code": "VGLJ", "name": "VGL Jhansi", "dist": 411.0, "sched_arr": "02:35", "sched_dep": "02:43", "platform": "2"},
        {"code": "BPL", "name": "Bhopal Junction", "dist": 702.0, "sched_arr": "06:45", "sched_dep": "06:50", "platform": "1"},
        {"code": "NGP", "name": "Nagpur Junction", "dist": 1092.0, "sched_arr": "13:05", "sched_dep": "13:10", "platform": "2"},
        {"code": "BPQ", "name": "Balharshah", "dist": 1285.0, "sched_arr": "16:25", "sched_dep": "16:30", "platform": "1"},
        {"code": "WL", "name": "Warangal", "dist": 1528.0, "sched_arr": "19:43", "sched_dep": "19:45", "platform": "1"},
        {"code": "BZA", "name": "Vijayawada Junction", "dist": 1735.0, "sched_arr": "23:15", "sched_dep": "23:25", "platform": "1"},
        {"code": "MAS", "name": "MGR Chennai Central", "dist": 2167.0, "sched_arr": "06:15", "sched_dep": "06:15", "platform": "4"}
    ],
    "12724": [
        {"code": "NDLS", "name": "New Delhi", "dist": 0.0, "sched_arr": "16:00", "sched_dep": "16:00", "platform": "7"},
        {"code": "AGC", "name": "Agra Cantt", "dist": 195.0, "sched_arr": "18:05", "sched_dep": "18:07", "platform": "1"},
        {"code": "GWL", "name": "Gwalior Junction", "dist": 313.0, "sched_arr": "19:28", "sched_dep": "19:30", "platform": "1"},
        {"code": "VGLJ", "name": "VGL Jhansi", "dist": 411.0, "sched_arr": "21:03", "sched_dep": "21:11", "platform": "2"},
        {"code": "BPL", "name": "Bhopal Junction", "dist": 702.0, "sched_arr": "01:00", "sched_dep": "01:05", "platform": "1"},
        {"code": "NGP", "name": "Nagpur Junction", "dist": 1092.0, "sched_arr": "07:10", "sched_dep": "07:15", "platform": "2"},
        {"code": "SKZR", "name": "Sirpur Kaghaznagar", "dist": 1355.0, "sched_arr": "11:14", "sched_dep": "11:15", "platform": "2"},
        {"code": "RDM", "name": "Ramagundam", "dist": 1427.0, "sched_arr": "12:09", "sched_dep": "12:10", "platform": "2"},
        {"code": "WL", "name": "Warangal", "dist": 1528.0, "sched_arr": "13:38", "sched_dep": "13:40", "platform": "1"},
        {"code": "KZJ", "name": "Kazipet Junction", "dist": 1538.0, "sched_arr": "13:58", "sched_dep": "14:00", "platform": "3"},
        {"code": "SC", "name": "Secunderabad Junction", "dist": 1670.0, "sched_arr": "16:25", "sched_dep": "16:30", "platform": "10"},
        {"code": "HYB", "name": "Hyderabad Deccan", "dist": 1679.0, "sched_arr": "17:10", "sched_dep": "17:10", "platform": "5"}
    ],
    "12260": [
        {"code": "NDLS", "name": "New Delhi", "dist": 0.0, "sched_arr": "19:45", "sched_dep": "19:45", "platform": "12"},
        {"code": "CNB", "name": "Kanpur Central", "dist": 440.0, "sched_arr": "00:05", "sched_dep": "00:10", "platform": "5"},
        {"code": "PRYJ", "name": "Prayagraj Junction", "dist": 634.0, "sched_arr": "02:20", "sched_dep": "02:25", "platform": "4"},
        {"code": "DDU", "name": "Pt. Deen Dayal Upadhyaya", "dist": 787.0, "sched_arr": "04:30", "sched_dep": "04:40", "platform": "2"},
        {"code": "DHN", "name": "Dhanbad Junction", "dist": 1193.0, "sched_arr": "09:10", "sched_dep": "09:15", "platform": "3"},
        {"code": "ASN", "name": "Asansol Junction", "dist": 1251.0, "sched_arr": "10:15", "sched_dep": "10:20", "platform": "5"},
        {"code": "SDAH", "name": "Sealdah (Kolkata)", "dist": 1458.0, "sched_arr": "12:45", "sched_dep": "12:45", "platform": "9"}
    ]
}

class SimulationOrchestrator:

    """
    Central Simulation & Dynamic ETA Orchestrator.
    Manages active trains, processes real-time telemetry, runs Kalman filtering, change-point & anomaly detection,
    evaluates network delay propagation, executes Monte Carlo simulations, and computes explainable ETAs.
    """
    def __init__(self):
        self.is_running = True
        self.speed_multiplier = 5  # 1 sec = 5 sim mins
        self.current_sim_time = datetime.now()
        
        # Engines
        self.graph = RailwayNetworkGraph()
        self.predictor = ETAPredictor()
        self.eta_predictor = self.predictor
        self.online_updater = OnlineSectionUpdater()
        self.kalman = TrainTelemetryFilter()
        self.changepoint_detectors = {}
        self.anomaly_detector = AnomalyDetector()
        self.propagator = DelayPropagationEngine(self.graph)
        self.monte_carlo = MonteCarloETASimulator(num_samples=100)
        
        # Simulators
        self.rtis_sim = RTISSimulator(self.graph)
        self.coa_sim = COASimulator()
        self.incident_sim = IncidentEventSimulator()
        
        # Smoothed Delay Cache for ETA Stabilization (EMA filter)
        self.smoothed_delays: Dict[str, float] = {}
        self.auto_incidents_enabled: bool = False
        self.tick_count: int = 0
        
        # Active state
        self.active_trains: Dict[str, Dict[str, Any]] = {}
        self._initialize_default_trains()
        
        # Demo Step Tracker
        self.demo_step = 0

    def _initialize_default_trains(self):
        """Seed 10 real iconic Indian Railways trains with authentic routes and schedules."""
        trains_data = [
            {
                "train_id": "TRAIN_12951",
                "train_number": "12951",
                "train_name": "Mumbai Rajdhani Express",
                "train_type": "RAJDHANI",
                "priority": 1,
                "origin_station_id": "NDLS",
                "origin_station_name": "New Delhi",
                "destination_station_id": "MMCT",
                "destination_station_name": "Mumbai Central",
                "current_section_id": "NDLS-MTJ",
                "next_station_id": "MTJ",
                "next_station_name": "Mathura Junction",
                "last_station_id": "NDLS",
                "lat": 28.3000,
                "lng": 77.4000,
                "speed_kmh": 110.0,
                "current_delay_minutes": 5.0,
                "status": "ON_TIME",
                "last_event_description": "Departed New Delhi on schedule"
            },
            {
                "train_id": "TRAIN_12302",
                "train_number": "12302",
                "train_name": "Howrah Rajdhani Express",
                "train_type": "RAJDHANI",
                "priority": 1,
                "origin_station_id": "NDLS",
                "origin_station_name": "New Delhi",
                "destination_station_id": "HWH",
                "destination_station_name": "Howrah Junction",
                "current_section_id": "NDLS-CNB",
                "next_station_id": "CNB",
                "next_station_name": "Kanpur Central",
                "last_station_id": "NDLS",
                "lat": 27.8000,
                "lng": 78.8000,
                "speed_kmh": 120.0,
                "current_delay_minutes": 0.0,
                "status": "ON_TIME",
                "last_event_description": "Cruising NDLS-CNB section at 120 km/h"
            },
            {
                "train_id": "TRAIN_12626",
                "train_number": "12626",
                "train_name": "Kerala Express",
                "train_type": "SUPERFAST",
                "priority": 2,
                "origin_station_id": "NDLS",
                "origin_station_name": "New Delhi",
                "destination_station_id": "TVC",
                "destination_station_name": "Trivandrum Central",
                "current_section_id": "AGC-GWL",
                "next_station_id": "GWL",
                "next_station_name": "Gwalior Junction",
                "last_station_id": "AGC",
                "lat": 26.8000,
                "lng": 78.1000,
                "speed_kmh": 75.0,
                "current_delay_minutes": 14.0,
                "status": "SLIGHT_DELAY",
                "last_event_description": "Delayed at Agra Cantt due to platform congestion"
            },
            {
                "train_id": "TRAIN_12002",
                "train_number": "12002",
                "train_name": "Rani Kamlapati Shatabdi",
                "train_type": "SHATABDI",
                "priority": 1,
                "origin_station_id": "NDLS",
                "origin_station_name": "New Delhi",
                "destination_station_id": "RKMP",
                "destination_station_name": "Rani Kamlapati (Bhopal)",
                "current_section_id": "VGLJ-BINA",
                "next_station_id": "BINA",
                "next_station_name": "Bina Junction",
                "last_station_id": "VGLJ",
                "lat": 24.8000,
                "lng": 78.3000,
                "speed_kmh": 105.0,
                "current_delay_minutes": 2.0,
                "status": "ON_TIME",
                "last_event_description": "Passed VGL Jhansi on schedule"
            },
            {
                "train_id": "TRAIN_12424",
                "train_number": "12424",
                "train_name": "Dibrugarh Rajdhani Express",
                "train_type": "RAJDHANI",
                "priority": 1,
                "origin_station_id": "NDLS",
                "origin_station_name": "New Delhi",
                "destination_station_id": "DBRG",
                "destination_station_name": "Dibrugarh",
                "current_section_id": "PRYJ-DDU",
                "next_station_id": "DDU",
                "next_station_name": "Pt. Deen Dayal Upadhyaya",
                "last_station_id": "PRYJ",
                "lat": 25.3500,
                "lng": 82.5000,
                "speed_kmh": 115.0,
                "current_delay_minutes": 8.0,
                "status": "ON_TIME",
                "last_event_description": "Crossed Prayagraj Junction (+8m)"
            },
            {
                "train_id": "TRAIN_12958",
                "train_number": "12958",
                "train_name": "Swarna Jayanti Rajdhani",
                "train_type": "RAJDHANI",
                "priority": 1,
                "origin_station_id": "NDLS",
                "origin_station_name": "New Delhi",
                "destination_station_id": "ADI",
                "destination_station_name": "Ahmedabad Junction",
                "current_section_id": "DEC-JP",
                "next_station_id": "JP",
                "next_station_name": "Jaipur Junction",
                "last_station_id": "DEC",
                "lat": 27.5000,
                "lng": 76.5000,
                "speed_kmh": 100.0,
                "current_delay_minutes": 0.0,
                "status": "ON_TIME",
                "last_event_description": "En-route to Jaipur Junction on schedule"
            },
            {
                "train_id": "TRAIN_12425",
                "train_number": "12425",
                "train_name": "Jammu Rajdhani Express",
                "train_type": "RAJDHANI",
                "priority": 1,
                "origin_station_id": "NDLS",
                "origin_station_name": "New Delhi",
                "destination_station_id": "JAT",
                "destination_station_name": "Jammu Tawi",
                "current_section_id": "UMB-LDH",
                "next_station_id": "LDH",
                "next_station_name": "Ludhiana Junction",
                "last_station_id": "UMB",
                "lat": 30.6000,
                "lng": 76.3000,
                "speed_kmh": 110.0,
                "current_delay_minutes": 3.0,
                "status": "ON_TIME",
                "last_event_description": "Passed Ambala Cantt (+3m)"
            },
            {
                "train_id": "TRAIN_12622",
                "train_number": "12622",
                "train_name": "Tamil Nadu Express",
                "train_type": "SUPERFAST",
                "priority": 2,
                "origin_station_id": "NDLS",
                "origin_station_name": "New Delhi",
                "destination_station_id": "MAS",
                "destination_station_name": "MGR Chennai Central",
                "current_section_id": "BPL-NGP",
                "next_station_id": "NGP",
                "next_station_name": "Nagpur Junction",
                "last_station_id": "BPL",
                "lat": 22.2000,
                "lng": 78.2000,
                "speed_kmh": 90.0,
                "current_delay_minutes": 18.0,
                "status": "SLIGHT_DELAY",
                "last_event_description": "Crossed Bhopal Junction (+18m)"
            },
            {
                "train_id": "TRAIN_12724",
                "train_number": "12724",
                "train_name": "Telangana Express",
                "train_type": "SUPERFAST",
                "priority": 2,
                "origin_station_id": "NDLS",
                "origin_station_name": "New Delhi",
                "destination_station_id": "HYB",
                "destination_station_name": "Hyderabad Deccan",
                "current_section_id": "KZJ-SC",
                "next_station_id": "SC",
                "next_station_name": "Secunderabad Junction",
                "last_station_id": "KZJ",
                "lat": 17.7000,
                "lng": 79.0000,
                "speed_kmh": 85.0,
                "current_delay_minutes": 10.0,
                "status": "SLIGHT_DELAY",
                "last_event_description": "Approaching Secunderabad Junction"
            },
            {
                "train_id": "TRAIN_12260",
                "train_number": "12260",
                "train_name": "Sealdah Duronto Express",
                "train_type": "SUPERFAST",
                "priority": 1,
                "origin_station_id": "NDLS",
                "origin_station_name": "New Delhi",
                "destination_station_id": "SDAH",
                "destination_station_name": "Sealdah (Kolkata)",
                "current_section_id": "DDU-DHN",
                "next_station_id": "DHN",
                "next_station_name": "Dhanbad Junction",
                "last_station_id": "DDU",
                "lat": 24.5000,
                "lng": 85.5000,
                "speed_kmh": 110.0,
                "current_delay_minutes": 0.0,
                "status": "ON_TIME",
                "last_event_description": "High-speed non-stop run on DDU-DHN section"
            }
        ]
        
        for t in trains_data:
            self.active_trains[t["train_id"]] = t
            self.changepoint_detectors[t["train_id"]] = CUSUMChangePointDetector()


    def get_current_timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S") + " IST"

    def tick_simulation(self, delta_real_seconds: float = 1.0):
        """Advances the simulation by (delta_real_seconds * speed_multiplier) minutes."""
        if not self.is_running:
            return

        sim_delta_seconds = delta_real_seconds * (self.speed_multiplier * 60.0)
        self.current_sim_time += timedelta(seconds=sim_delta_seconds)
        self.kalman.set_speed_multiplier(self.speed_multiplier)

        # 1. Evaluate network delay propagation
        prop_delays = self.propagator.compute_network_propagation(self.active_trains)

        # 2. Advance train telemetry
        for t_id, train in self.active_trains.items():
            if train.get("status") == "ARRIVED":
                continue
                
            # Apply Kalman Filter to raw position/speed
            filt_lat, filt_lng, filt_speed = self.kalman.filter_telemetry(
                t_id, train["lat"], train["lng"], train["speed_kmh"]
            )
            train["filtered_lat"] = filt_lat
            train["filtered_lng"] = filt_lng
            train["filtered_speed"] = filt_speed

            # Record telemetry run in online section updater
            curr_sec = train.get("current_section_id", "NDLS-MTJ")
            running_time = max(1.0, (train.get("section_progress_km", 1.0) / max(10.0, train.get("speed_kmh", 80.0))) * 60.0)
            self.online_updater.record_section_run(
                section_id=curr_sec,
                actual_running_time_min=running_time,
                meta={"train_id": t_id, "speed": train["speed_kmh"]}
            )

            # Advance train position along section
            train = self.rtis_sim.step_train_movement(train, sim_delta_seconds)
            
            # Check Change-Point Detection on speed drop
            cp_result = self.changepoint_detectors[t_id].add_data_point(train["speed_kmh"])
            if cp_result["change_detected"] and cp_result["direction"] == "SPEED_DROP":
                self.coa_sim.log_event(
                    event_type="UNSCHEDULED_SPEED_DROP",
                    description=f"Sudden speed drop detected on {train['train_name']} ({train['speed_kmh']} km/h)",
                    train_id=t_id,
                    section_id=train["current_section_id"],
                    severity="HIGH"
                )

            # Apply propagated delay addition
            p_delay = prop_delays.get(t_id, 0.0)
            if p_delay > 0:
                train["current_delay_minutes"] += p_delay * 0.05  # Gradually accumulate
                train["status"] = "SLIGHT_DELAY" if train["current_delay_minutes"] < 20 else "CRITICAL_DELAY"

    def compute_dynamic_eta(self, train_id: str) -> Optional[ETAPredictionSchema]:
        train = self.active_trains.get(train_id)
        if not train:
            return None

        dest_id = train["destination_station_id"]
        dest_name = train["destination_station_name"]
        
        train_num_str = str(train.get("train_number", "12951"))
        catalog = route_catalogs.get(train_num_str, route_catalogs.get("12951", []))
        dest_sched_arr_str = catalog[-1]["sched_arr"] if catalog else "12:00"

        # Parse dest_sched_arr_str (e.g. "08:35") into actual scheduled datetime matching current IST date
        now_dt = datetime.now()
        try:
            sh, sm = map(int, dest_sched_arr_str.split(":"))
            base_sched_arr = now_dt.replace(hour=sh, minute=sm, second=0, microsecond=0)
            if base_sched_arr < now_dt - timedelta(hours=12):
                base_sched_arr += timedelta(days=1)
        except Exception:
            base_sched_arr = self.current_sim_time + timedelta(minutes=90)

        timetable_eta_str = base_sched_arr.strftime("%H:%M IST")

        # Get downstream sections
        curr_sec_id = train["current_section_id"]
        downstream_sections = self.graph.get_downstream_sections(train["last_station_id"], dest_id)
        if not downstream_sections:
            downstream_sections = [curr_sec_id]

        # 1. Base ML predictions for section travel times
        total_ml_travel_min = 0.0
        sec_list_mc = []
        
        for idx, sec_id in enumerate(downstream_sections):
            sec_info = self.graph.sections_dict.get(sec_id, {"dist": 80.0, "mps": 110.0})
            sched_min = (sec_info["dist"] / sec_info["mps"]) * 60.0
            
            # A3: Feed live online section stats into prediction
            online_stats = None
            if hasattr(self.online_updater, 'get_online_section_stats'):
                sec_med, sec_std = self.online_updater.get_online_section_stats(sec_id)
                online_stats = {"median": sec_med, "std": sec_std}
            
            ml_pred_min = self.predictor.predict_section_travel_time(
                train_priority=train.get("priority", 3),
                train_type=train.get("train_type", "EXPRESS"),
                day_of_week=self.current_sim_time.weekday(),
                is_fog_season=1 if self.current_sim_time.month in [12, 1] else 0,
                distance_from_origin=train.get("section_progress_km", 0.0),
                route_sequence=idx + 1,
                arrival_delay=train.get("current_delay_minutes", 0.0),
                sched_section_travel_min=sched_min,
                online_section_stats=online_stats
            )
            total_ml_travel_min += ml_pred_min
            sec_list_mc.append({"section_id": sec_id, "scheduled_travel_min": sched_min})

        ml_eta_dt = now_dt + timedelta(minutes=total_ml_travel_min)
        ml_base_eta_str = ml_eta_dt.strftime("%H:%M IST")

        # 2. Dynamic Real-Time Factors with Train Priority Precedence Pattern
        curr_delay = train.get("current_delay_minutes", 0.0)
        priority = train.get("priority", 2)
        
        # Priority multipliers: Priority 1 (Rajdhani/Shatabdi) gets precedence, Priority 3 (Express) yields
        priority_mult = 0.7 if priority == 1 else (1.0 if priority == 2 else 1.5)

        # Weather impact
        weather_delay = 0.0
        sec_obj = self.graph.sections_dict.get(curr_sec_id, {})
        weather_cond = sec_obj.get("weather", "CLEAR")
        if weather_cond == "FOG":
            weather_delay = 12.0 * priority_mult
        elif weather_cond == "HEAVY_RAIN":
            weather_delay = 7.0 * priority_mult

        # Incidents impact
        incidents = self.incident_sim.get_incidents_for_section(curr_sec_id)
        if incidents:
            inc = incidents[0]
            if inc.event_type == "SIGNAL_FAILURE":
                curr_delay += 10.0 * priority_mult
            elif inc.event_type == "TRACK_FAILURE":
                curr_delay += 25.0 * priority_mult
            elif inc.event_type == "ACCIDENT":
                curr_delay += 45.0 * priority_mult

        # Junction congestion / precedence hold
        junction_delay = 0.0
        if sec_obj.get("congestion", 0.0) > 0.5:
            junction_delay = 8.0 * priority_mult

        platform_hold = 0.0
        if train.get("status") == "PLATFORM_HOLD":
            platform_hold = 5.0

        # Recovery calculation (high priority trains recover lost time faster)
        recovery = 0.0
        if priority == 1 and curr_delay > 10.0 and weather_delay == 0:
            recovery = min(curr_delay * 0.35, 10.0)

        # Raw Total Delay
        raw_total_delay = max(0.0, curr_delay + weather_delay + junction_delay + platform_hold - recovery)
        
        # 3. EMA Smoothing Filter to Eliminate Artificial ETA Fluctuation
        t_id = train["train_id"]
        if t_id not in self.smoothed_delays:
            self.smoothed_delays[t_id] = raw_total_delay
        else:
            # Alpha = 0.15 for rock-solid stability without random jumps
            self.smoothed_delays[t_id] = round(0.15 * raw_total_delay + 0.85 * self.smoothed_delays[t_id], 1)

        dynamic_total_delay = self.smoothed_delays[t_id]
        dynamic_eta_dt = base_sched_arr + timedelta(minutes=dynamic_total_delay)
        dynamic_forecast_eta_str = dynamic_eta_dt.strftime("%H:%M IST")

        # 4. Monte Carlo Simulation for Confidence Intervals
        mc_result = self.monte_carlo.simulate_future_eta(
            train_info=train,
            remaining_sections=sec_list_mc,
            current_delay_min=dynamic_total_delay,
            active_weather_penalty=weather_delay,
            junction_congestion_min=junction_delay
        )

        conf_80_min_dt = base_sched_arr + timedelta(minutes=mc_result["ci_80_min_delay"])
        conf_80_max_dt = base_sched_arr + timedelta(minutes=mc_result["ci_80_max_delay"])
        conf_95_min_dt = base_sched_arr + timedelta(minutes=mc_result["ci_95_min_delay"])
        conf_95_max_dt = base_sched_arr + timedelta(minutes=mc_result["ci_95_max_delay"])

        # 5. Explainability Breakdown
        factors = ETAExplainer.generate_explanation(
            current_delay_min=curr_delay,
            weather_delay_min=weather_delay,
            junction_congestion_min=junction_delay,
            platform_hold_min=platform_hold,
            recovery_min=recovery,
            weather_condition=weather_cond
        )

        p10_dt = base_sched_arr + timedelta(minutes=mc_result["ci_80_min_delay"])
        p50_dt = base_sched_arr + timedelta(minutes=dynamic_total_delay)
        p90_dt = base_sched_arr + timedelta(minutes=mc_result["ci_80_max_delay"])

        # A7: Use real CRPS score from model metadata, not hardcoded 0.85
        real_crps = getattr(self.predictor, 'crps_score', 0.0)
        real_arch = self.predictor.metadata.get('model_architecture', 'HYBRID_TGNN_GBDT') if hasattr(self.predictor, 'metadata') else 'HYBRID_TGNN_GBDT'

        # A7: Compute real formatted confidence margin from MC spread
        mc_spread_min = round((mc_result['ci_80_max_delay'] - mc_result['ci_80_min_delay']) / 2.0, 0)
        mc_spread_min = max(1, int(mc_spread_min))

        return ETAPredictionSchema(
            train_id=train["train_id"],
            train_number=train["train_number"],
            target_station_id=dest_id,
            target_station_name=dest_name,
            scheduled_arrival=base_sched_arr.strftime("%H:%M IST"),
            timetable_baseline_eta=timetable_eta_str,
            ml_base_eta=ml_base_eta_str,
            dynamic_forecast_eta=dynamic_forecast_eta_str,
            eta_p10=p10_dt.strftime("%H:%M IST"),
            eta_p50=p50_dt.strftime("%H:%M IST"),
            eta_p90=p90_dt.strftime("%H:%M IST"),
            confidence_score=round(max(60.0, min(99.0, 100.0 - (dynamic_total_delay * 0.3))), 1),
            crps_score=real_crps,
            model_architecture=real_arch,
            formatted_confidence_eta=f"{dynamic_forecast_eta_str} ± {mc_spread_min} min",
            total_predicted_delay_minutes=round(dynamic_total_delay, 1),
            confidence_80_min=conf_80_min_dt.strftime("%H:%M"),
            confidence_80_max=conf_80_max_dt.strftime("%H:%M"),
            confidence_95_min=conf_95_min_dt.strftime("%H:%M"),
            confidence_95_max=conf_95_max_dt.strftime("%H:%M"),
            on_time_probability=mc_result["on_time_probability"],
            explainability_factors=factors,
            monte_carlo_samples=mc_result.get("samples", []),
            last_updated=datetime.now().strftime("%H:%M:%S IST")
        )






    def trigger_sih_demo_step(self) -> Dict[str, Any]:
        """
        Executes the step-by-step SIH Predefined Demonstration Scenario.
        Visually demonstrates dynamic ETA recalculation across sequential events:
        Initial 22:41 -> Signal Hold (+10m) -> Fog Entry (+9m) -> Precedence Hold (+7m) -> Clearance (-5m) -> Final ETA
        """
        self.demo_step += 1
        train = self.active_trains.get("TRAIN_12951")
        if not train:
            return {"step": self.demo_step, "description": "No active train"}

        desc = ""
        if self.demo_step == 1:
            desc = "STEP 1: Initial State. Train 12951 running on schedule. Baseline Timetable ETA = 22:41."
            train["current_delay_minutes"] = 0.0
            train["status"] = "ON_TIME"
        elif self.demo_step == 2:
            desc = "STEP 2: Signal Halt Injected. Train 12951 stopped at signal outside Mathura. Delay +10m -> Dynamic ETA = 22:51."
            train["current_delay_minutes"] = 10.0
            train["speed_kmh"] = 0.0
            train["status"] = "SIGNAL_HALT"
            self.coa_sim.log_event("SIGNAL_HALT", "Signal halt outside MTJ for track clearance (+10m)", "TRAIN_12951", "MTJ", severity="HIGH")
        elif self.demo_step == 3:
            desc = "STEP 3: Fog Zone Entry. En-route section MTJ-AGC affected by dense fog (Visibility 180m). Speed restricted to 45 km/h (+9m penalty) -> Dynamic ETA = 23:00."
            train["current_delay_minutes"] = 19.0
            train["status"] = "INCIDENT_AFFECTED"
            self.graph.update_section_state("MTJ-AGC", weather="FOG")
            self.incident_sim.inject_incident("FOG", "MTJ-AGC", severity="HIGH", visibility_m=180.0)
            self.coa_sim.log_event("WEATHER_ALERT", "Dense fog reported on section MTJ-AGC. MPS reduced to 45 km/h", "TRAIN_12951", section_id="MTJ-AGC", severity="HIGH")
        elif self.demo_step == 4:
            desc = "STEP 4: Junction Precedence Hold. Preceding freight train holding Agra Cantt junction. Delayed Train 12626 crossing (+7m delay propagation) -> Dynamic ETA = 23:07."
            train["current_delay_minutes"] = 26.0
            train["status"] = "CRITICAL_DELAY"
            self.graph.update_section_state("MTJ-AGC", congestion=0.8)
            self.coa_sim.log_event("PRECEDENCE", "Junction route conflict at AGC. Held for crossing train (+7m)", "TRAIN_12951", station_id="AGC", severity="HIGH")
        elif self.demo_step == 5:
            desc = "STEP 5: Fog Clears & High-Speed Recovery. Weather cleared, MPS restored to 130 km/h. High priority Rajdhani recovers 5 mins -> Final Dynamic Forecasted ETA = 23:02."
            train["current_delay_minutes"] = 21.0
            train["speed_kmh"] = 120.0
            train["status"] = "SLIGHT_DELAY"
            self.graph.update_section_state("MTJ-AGC", weather="CLEAR", congestion=0.0)
            self.incident_sim.clear_all_incidents()
            self.coa_sim.log_event("WEATHER_CLEARED", "Fog cleared on MTJ-AGC section. Track clear for high speed running", "TRAIN_12951", section_id="MTJ-AGC", severity="LOW")
        else:
            self.demo_step = 0
            return self.trigger_sih_demo_step()

        eta_schema = self.compute_dynamic_eta("TRAIN_12951")
        return {
            "demo_step": self.demo_step,
            "description": desc,
            "train_state": train,
            "updated_eta": eta_schema.dict() if eta_schema else None
        }

    def _build_delay_reasons_for_section(self, section_id: str, train_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        A7: Builds explainable delay_reasons from active incidents, weather, and congestion
        on the given section. Returns list of ETABreakdownFactor-compatible dicts.
        """
        reasons = []
        
        # Check active incidents on this section
        incidents = self.incident_sim.get_incidents_for_section(section_id)
        for inc in incidents:
            impact_map = {
                "SIGNAL_FAILURE": 15.0,
                "TRACK_FAILURE": 30.0,
                "ACCIDENT": 45.0,
                "FOG": 12.0,
                "HEAVY_RAIN": 8.0,
                "CHAIN_PULLING": 12.0,
                "MAINTENANCE_BLOCK": 25.0,
                "PLATFORM_OCCUPIED": 12.0,
                "JUNCTION_CONGESTION": 10.0,
            }
            impact = impact_map.get(inc.event_type, 10.0)
            reasons.append({
                "factor_name": inc.event_type.replace("_", " ").title(),
                "impact_minutes": impact,
                "description": f"Active {inc.event_type.lower().replace('_', ' ')} on section {section_id} (severity: {inc.severity})"
            })

        # Check weather on section
        sec_obj = self.graph.sections_dict.get(section_id, {})
        weather = sec_obj.get("weather", "CLEAR")
        if weather == "FOG":
            reasons.append({
                "factor_name": "Dense Fog",
                "impact_minutes": 12.0,
                "description": f"Fog speed restriction active on {section_id} (visibility < 200m)"
            })
        elif weather == "HEAVY_RAIN":
            reasons.append({
                "factor_name": "Heavy Monsoon Rain",
                "impact_minutes": 7.0,
                "description": f"Rain-induced speed restriction on {section_id}"
            })

        # Check congestion
        congestion = sec_obj.get("congestion", 0.0)
        if congestion > 0.5:
            reasons.append({
                "factor_name": "Junction Congestion",
                "impact_minutes": round(congestion * 10.0, 1),
                "description": f"Route conflict / precedence hold at {section_id} (congestion: {congestion:.0%})"
            })

        # Check train-specific status
        train_status = train_dict.get("status", "ON_TIME") if isinstance(train_dict, dict) else getattr(train_dict, "status", "ON_TIME")
        if train_status == "PLATFORM_HOLD":
            reasons.append({
                "factor_name": "Platform Hold",
                "impact_minutes": 5.0,
                "description": "Train held at platform awaiting route clearance"
            })
        elif train_status == "SIGNAL_HALT":
            reasons.append({
                "factor_name": "Signal Halt",
                "impact_minutes": 10.0,
                "description": "Train stopped at signal for track clearance"
            })

        # Check priority-based recovery (negative = time recovered)
        priority = train_dict.get("priority", 3) if isinstance(train_dict, dict) else getattr(train_dict, "priority", 3)
        curr_delay = train_dict.get("current_delay_minutes", 0.0) if isinstance(train_dict, dict) else getattr(train_dict, "current_delay_minutes", 0.0)
        if priority == 1 and curr_delay > 10.0 and weather == "CLEAR":
            recovery = min(curr_delay * 0.35, 10.0)
            reasons.append({
                "factor_name": "High Priority Recovery",
                "impact_minutes": -round(recovery, 1),
                "description": "Rajdhani/Shatabdi priority precedence — recovering lost time at MPS"
            })

        return reasons

    def reset_simulation(self):
        self.is_running = True
        self.demo_step = 0
        self.incident_sim.clear_all_incidents()
        self._initialize_default_trains()
        self.graph._initialize_default_corridor()

    def get_full_simulation_state(self) -> SimulationStateSchema:
        train_schemas = []
        for t_id, train in self.active_trains.items():
            eta_data = self.compute_dynamic_eta(t_id)
            train_schemas.append(TrainStateSchema(
                train_id=train["train_id"],
                train_number=train["train_number"],
                train_name=train["train_name"],
                train_type=train["train_type"],
                priority=train["priority"],
                origin_station_name=train["origin_station_name"],
                destination_station_name=train["destination_station_name"],
                current_section_id=train["current_section_id"],
                next_station_id=train["next_station_id"],
                next_station_name=train["next_station_name"],
                latitude=train["lat"],
                longitude=train["lng"],
                speed_kmh=train["speed_kmh"],
                current_delay_minutes=train["current_delay_minutes"],
                status=train["status"],
                last_event_description=train["last_event_description"],
                current_eta=eta_data
            ))

        weather_zones = []
        for sec_id, sec in self.graph.sections_dict.items():
            if sec.get("weather") != "CLEAR":
                coords = sec.get("coords", [[0, 0], [0, 0]])
                weather_zones.append({
                    "section_id": sec_id,
                    "condition": sec.get("weather"),
                    "center_lat": (coords[0][0] + coords[1][0]) / 2.0,
                    "center_lng": (coords[0][1] + coords[1][1]) / 2.0,
                    "radius_km": 30.0
                })

        return SimulationStateSchema(
            timestamp=self.get_current_timestamp(),
            is_running=self.is_running,
            speed_multiplier=self.speed_multiplier,
            active_events_count=len(self.incident_sim.active_incidents),
            trains=train_schemas,
            weather_zones=weather_zones,
            incidents=self.incident_sim.active_incidents
        )

    def sync_live_telemetry(self, train_number: str) -> float:
        """
        Synchronizes live telemetry from RailRadar / RTIS API adapter.
        Updates active train state with actual real-time delay (e.g. +20 min) if available.
        """
        try:
            from app.adapters.historical_data_adapter import WhereIsMyTrainHistoricalAdapter
            adapter = WhereIsMyTrainHistoricalAdapter()
            live_status = adapter.fetch_live_train_status(train_number)
            if live_status and "delay_minutes" in live_status:
                live_delay = float(live_status["delay_minutes"])
                normalized_id = f"TRAIN_{train_number}"
                trains_list = list(self.active_trains.values()) if isinstance(self.active_trains, dict) else self.active_trains
                for t in trains_list:
                    t_num = getattr(t, "train_number", None) or (t.get("train_number") if isinstance(t, dict) else None)
                    if t_num == train_number or getattr(t, "train_id", None) == normalized_id:
                        st_val = "HEAVY_DELAY" if live_delay >= 15 else ("SLIGHT_DELAY" if live_delay >= 5 else "ON_TIME")
                        cur_st_code = live_status.get("current_station_code")
                        cur_st_name = live_status.get("current_station_name")
                        st_delays = live_status.get("station_delays", {})
                        st_dep_delays = live_status.get("station_dep_delays", {})
                        st_arr_delays = live_status.get("station_arr_delays", {})

                        if isinstance(t, dict):
                            t["current_delay_minutes"] = live_delay
                            t["status"] = st_val
                            t["station_delays"] = st_delays
                            t["station_dep_delays"] = st_dep_delays
                            t["station_arr_delays"] = st_arr_delays
                            if cur_st_code:
                                t["current_station_code"] = cur_st_code
                                t["next_station_id"] = cur_st_code
                            if cur_st_name:
                                t["current_station_name"] = cur_st_name
                                t["next_station_name"] = cur_st_name
                        else:
                            try:
                                setattr(t, "current_delay_minutes", live_delay)
                                setattr(t, "status", st_val)
                                setattr(t, "station_delays", st_delays)
                                setattr(t, "station_dep_delays", st_dep_delays)
                                setattr(t, "station_arr_delays", st_arr_delays)
                                if cur_st_code:
                                    setattr(t, "next_station_id", cur_st_code)
                                if cur_st_name:
                                    setattr(t, "next_station_name", cur_st_name)
                            except Exception:
                                pass
                return live_delay

        except Exception as e:
            print(f"[ORCHESTRATOR] Could not sync live RTIS telemetry for train {train_number}: {e}")
        return 0.0

    def get_train_route_timeline(self, train_id: str, journey_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Returns the full station-by-station route timeline for a train."""
        normalized_id = train_id if train_id.startswith("TRAIN_") else f"TRAIN_{train_id}"
        clean_train_num = train_id.replace("TRAIN_", "")

        # Automatically sync live telemetry
        live_telemetry_synced_delay = self.sync_live_telemetry(clean_train_num)

        found_train = None
        
        trains_list = list(self.active_trains.values()) if isinstance(self.active_trains, dict) else self.active_trains
        for t in trains_list:
            t_id = getattr(t, "train_id", None) or (t.get("train_id") if isinstance(t, dict) else None)
            t_num = getattr(t, "train_number", None) or (t.get("train_number") if isinstance(t, dict) else None)
            if t_id == normalized_id or t_num == train_id:
                found_train = t
                break

        if not found_train:
            state = self.get_full_simulation_state()
            for t in state.trains:
                if t.train_id == normalized_id or t.train_number == train_id:
                    found_train = {
                        "train_id": t.train_id,
                        "train_number": t.train_number,
                        "train_name": t.train_name,
                        "origin_station_name": t.origin_station_name,
                        "destination_station_name": t.destination_station_name,
                        "next_station_id": t.next_station_id,
                        "next_station_name": t.next_station_name,
                        "current_delay_minutes": t.current_delay_minutes
                    }
                    break

        if not found_train:
            return None

        # Helper extract function
        def get_val(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        train_id_val = get_val(found_train, "train_id", normalized_id)
        train_num_val = get_val(found_train, "train_number", clean_train_num)
        train_name_val = get_val(found_train, "train_name", f"Train {clean_train_num}")
        origin_val = get_val(found_train, "origin_station_name", "Origin")
        dest_val = get_val(found_train, "destination_station_name", "Destination")
        current_delay = get_val(found_train, "current_delay_minutes", live_telemetry_synced_delay)
        next_st_id = get_val(found_train, "next_station_id", "ST1")
        next_st_name = get_val(found_train, "next_station_name", "Upcoming Station")
        st_delays_map = get_val(found_train, "station_delays", {})
        st_dep_delays_map = get_val(found_train, "station_dep_delays", {})
        st_arr_delays_map = get_val(found_train, "station_arr_delays", {})

        stations_def = route_catalogs.get(str(train_num_val), route_catalogs["12951"])

        # Determine current active station index in schedule
        cur_st_name_val = get_val(found_train, "current_station_name", "")
        cur_st_name_val_upper = str(cur_st_name_val).upper() if cur_st_name_val else ""
        cur_st_code_val = get_val(found_train, "current_station_code", "")

        current_idx = -1
        # 1. Direct code/name match or fuzzy match
        for idx, st in enumerate(stations_def):
            st_c = st["code"].upper()
            st_n = st["name"].upper()
            nxt_id_u = str(next_st_id).upper() if next_st_id else ""
            nxt_nm_u = str(next_st_name).upper() if next_st_name else ""

            if (nxt_id_u and st_c == nxt_id_u) or \
               (cur_st_code_val and st_c == str(cur_st_code_val).upper()) or \
               (nxt_nm_u and (nxt_nm_u in st_n or st_n in nxt_nm_u)) or \
               (cur_st_name_val_upper and (cur_st_name_val_upper in st_n or st_n in cur_st_name_val_upper)):
                current_idx = idx
                break

        # 2. Check station_dep_delays_map or station_delays_map for highest passed station index
        if current_idx == -1 and (st_dep_delays_map or st_delays_map):
            for idx, st in enumerate(stations_def):
                if st["code"] in st_dep_delays_map or st["code"] in st_delays_map:
                    current_idx = idx

        if current_idx == -1 or current_idx >= len(stations_def):
            current_idx = 1

        route_items = []
        passed_current = False
        accumulated_ml_delay = max(0.0, current_delay)
        active_section_id = get_val(found_train, "current_section_id", "NDLS-MTJ")

        # Known major junction keywords for congestion / shunting delay additions
        junction_keywords = ["JN", "JUNCTION", "CENTRAL", "TERMINUS", "CANTT", "DDU", "CNB", "PRYJ", "RTM", "BRC", "BPL", "NGP", "BPQ", "BZA", "KPD", "TVC"]

        for idx, st in enumerate(stations_def):
            st_code = st["code"]
            st_name = st["name"].upper()
            
            # If train is moving between prev_st and current_st, insert In-Between section item
            if idx == current_idx and current_idx > 0:
                prev_st = stations_def[idx - 1]
                st_A_name = prev_st["name"]
                st_B_name = st["name"]
                dist_into = get_val(found_train, "distance_into_section_km", 25.0)
                sec_dist = max(10.0, st["dist"] - prev_st["dist"])
                progress_pct = min(0.95, max(0.05, dist_into / sec_dist))
                in_between_dist = round(prev_st["dist"] + (sec_dist * progress_pct), 1)
                speed_val = get_val(found_train, "speed_kmh", 110.0)
                
                route_items.append({
                    "station_id": f"INBETWEEN_{prev_st['code']}_{st['code']}",
                    "station_code": f"ENROUTE_{prev_st['code']}_{st['code']}",
                    "station_name": f"En Route: {st_A_name} ➔ {st_B_name}",
                    "distance_km": in_between_dist,
                    "platform_number": "TRACK",
                    "scheduled_arrival": "--:--",
                    "scheduled_departure": "--:--",
                    "forecasted_arrival": "LIVE NOW",
                    "forecasted_departure": "LIVE NOW",
                    "arrival_delay_minutes": current_delay,
                    "departure_delay_minutes": current_delay,
                    "ml_forecasted_arrival": "LIVE NOW",
                    "live_telemetry_delay_minutes": current_delay,
                    "ml_predicted_delay_minutes": current_delay,
                    "delay_difference_minutes": 0.0,
                    "status": "CURRENT",
                    "is_current_position": True,
                    "is_in_between": True,
                    "in_between_from_station": st_A_name,
                    "in_between_to_station": st_B_name,
                    "in_between_progress_pct": round(progress_pct * 100, 1),
                    "speed_kmh": speed_val,
                    "delay_reasons": self._build_delay_reasons_for_section(active_section_id, found_train)
                })
                passed_current = True
                is_current = False
                status_str = "UPCOMING"
            elif idx < current_idx and not passed_current:
                is_current = False
                status_str = "PASSED"
            else:
                is_current = False
                status_str = "UPCOMING"

            # Parse scheduled time
            arr_h, arr_m = map(int, st["sched_arr"].split(":"))
            dep_h, dep_m = map(int, st["sched_dep"].split(":"))

            # Station-specific departure delay vs arrival delay from live telemetry
            specific_arr_del = st_arr_delays_map.get(st_code, st_delays_map.get(st_code))
            specific_dep_del = st_dep_delays_map.get(st_code, st_delays_map.get(st_code))

            # Determine Live Delay for station
            if status_str in ("PASSED", "CURRENT"):
                st_live_arr_del = specific_arr_del if specific_arr_del is not None else current_delay
                st_live_dep_del = specific_dep_del if specific_dep_del is not None else st_live_arr_del
                st_live_delay = st_live_dep_del
                st_ml_delay = st_live_delay
                accumulated_ml_delay = st_live_delay
                ml_status_flag = "LIVE"
            else:
                # UPCOMING Station: Dynamic ML Delay Progression using historical station arrival delay records
                prev_st = stations_def[idx - 1]
                section_dist = max(10.0, st["dist"] - prev_st["dist"])
                is_junction = any(jk in st_name or jk in st_code for jk in junction_keywords)

                # Calculate station-to-station historical median delay delta
                total_route_km = float(stations_def[-1]["dist"]) if stations_def else 1000.0
                curr_km = float(stations_def[current_idx]["dist"]) if current_idx < len(stations_def) else 0.0
                rem_km = max(1.0, total_route_km - curr_km)
                station_dist_from_curr = max(0.0, float(st["dist"]) - curr_km)
                
                # Compound historical bottleneck delay factor
                hist_bottleneck_factor = 1.35 if is_junction else 1.05
                hist_accumulated_delta = (station_dist_from_curr / rem_km) * (43.4 if "12626" in str(train_num_val) else 18.5) * hist_bottleneck_factor

                _now = datetime.now()
                if hasattr(self, "predictor") and self.predictor is not None:
                    try:
                        _, gbr_pred, _, _, _ = self.predictor.predict_multi_quantile_delays(
                            current_delay_min=current_delay + hist_accumulated_delta,
                            station_sequence=idx + 1,
                            distance_from_origin=float(st["dist"]),
                            total_distance=total_route_km,
                            day_of_week=float(_now.weekday()),
                            month=float(_now.month),
                            hour=float(_now.hour) + _now.minute / 60.0
                        )
                        st_ml_delay = round(max(current_delay, gbr_pred), 1)
                        ml_status_flag = "ONLINE"
                    except Exception as e:
                        import logging
                        logging.getLogger("orchestrator").error(f"Model prediction failed: {e}")
                        st_ml_delay = round(current_delay + hist_accumulated_delta, 1)
                        ml_status_flag = "UNAVAILABLE_SCHEDULE_ESTIMATE"
                else:
                    st_ml_delay = round(current_delay + hist_accumulated_delta, 1)
                    ml_status_flag = "UNAVAILABLE_SCHEDULE_ESTIMATE"

                st_live_arr_del = current_delay
                st_live_dep_del = current_delay
                st_live_delay = current_delay

            # Format Live Telemetry forecasted arrival & departure using station-specific delays
            live_arr_m = (arr_m + int(st_live_arr_del)) % 60
            live_arr_h = (arr_h + (arr_m + int(st_live_arr_del)) // 60) % 24

            live_dep_m = (dep_m + int(st_live_dep_del)) % 60
            live_dep_h = (dep_h + (dep_m + int(st_live_dep_del)) // 60) % 24

            # Format ML Model Predicted forecasted arrival
            ml_arr_m = (arr_m + int(st_ml_delay)) % 60
            ml_arr_h = (arr_h + (arr_m + int(st_ml_delay)) // 60) % 24

            if status_str == "CURRENT":
                now_time_str = datetime.now().strftime("%H:%M IST")
                forecasted_arr_str = f"LIVE NOW ({now_time_str})"
                forecasted_dep_str = f"LIVE NOW ({now_time_str})"
                ml_forecasted_arr_str = f"LIVE NOW ({now_time_str})"
            else:
                forecasted_arr_str = f"{live_arr_h:02d}:{live_arr_m:02d}"
                forecasted_dep_str = f"{live_dep_h:02d}:{live_dep_m:02d}"
                ml_forecasted_arr_str = f"{ml_arr_h:02d}:{ml_arr_m:02d}"

            diff_delay = round(st_ml_delay - st_live_delay, 1)

            # Calculate Quantiles P10, P50, P90 and confidence bounds for route item
            _now = datetime.now()
            p10_del, p50_del, p90_del, conf_score, crps_val = self.predictor.predict_multi_quantile_delays(
                current_delay_min=st_ml_delay,
                station_sequence=idx + 1,
                distance_from_origin=float(st["dist"]),
                total_distance=float(stations_def[-1]["dist"]) if stations_def else 1000.0,
                day_of_week=float(_now.weekday()),
                month=float(_now.month),
                hour=float(_now.hour) + _now.minute / 60.0
            )

            p10_m = (arr_m + int(p10_del)) % 60
            p10_h = (arr_h + (arr_m + int(p10_del)) // 60) % 24

            p50_m = (arr_m + int(p50_del)) % 60
            p50_h = (arr_h + (arr_m + int(p50_del)) // 60) % 24

            p90_m = (arr_m + int(p90_del)) % 60
            p90_h = (arr_h + (arr_m + int(p90_del)) // 60) % 24

            eta_p10_str = f"{p10_h:02d}:{p10_m:02d}"
            eta_p50_str = f"{p50_h:02d}:{p50_m:02d}"
            eta_p90_str = f"{p90_h:02d}:{p90_m:02d}"
            conf_margin = round((p90_del - p10_del) / 2.0, 1)

            route_items.append({
                "station_id": st["code"],
                "station_code": st["code"],
                "station_name": st["name"],
                "distance_km": st["dist"],
                "platform_number": st["platform"],
                "scheduled_arrival": st["sched_arr"],
                "scheduled_departure": st["sched_dep"],
                "forecasted_arrival": forecasted_arr_str,
                "forecasted_departure": forecasted_dep_str,
                "arrival_delay_minutes": round(st_live_arr_del, 1),
                "departure_delay_minutes": round(st_live_dep_del, 1),
                "ml_forecasted_arrival": ml_forecasted_arr_str,
                "eta_p10": eta_p10_str,
                "eta_p50": eta_p50_str,
                "eta_p90": eta_p90_str,
                "confidence_margin_minutes": conf_margin,
                "live_telemetry_delay_minutes": round(st_live_dep_del, 1),
                "ml_predicted_delay_minutes": st_ml_delay,
                "delay_difference_minutes": diff_delay,
                "status": status_str,
                "is_current_position": is_current,
                "ml_status_flag": ml_status_flag,
                "delay_reasons": self._build_delay_reasons_for_section(active_section_id, found_train) if status_str != "PASSED" else []
            })



        # Determine active event description or fallback
        last_event_desc = get_val(found_train, "last_event_description", "")
        if last_event_desc:
            status_msg = f"{last_event_desc} (Current delay: {current_delay:.0f} mins)"
        else:
            status_msg = f"Running {current_delay:.0f} min late near {next_st_name}" if current_delay > 5 else "Running On Time"

        eta_prediction = self.compute_dynamic_eta(train_id_val)
        formatted_eta = eta_prediction.formatted_confidence_eta if eta_prediction else f"{current_delay:.0f} min late"

        return {
            "train_id": train_id_val,
            "train_number": train_num_val,
            "train_name": train_name_val,
            "origin_station_name": origin_val,
            "destination_station_name": dest_val,
            "current_station_name": get_val(found_train, "current_station_name", next_st_name),
            "next_station_name": next_st_name,
            "total_delay_minutes": current_delay,
            "status_message": status_msg,
            "last_updated": self.get_current_timestamp(),
            "formatted_confidence_eta": formatted_eta,
            "route_items": route_items
        }

