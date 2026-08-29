import networkx as nx
from typing import List, Dict, Any, Optional

class RailwayNetworkGraph:
    """
    Dynamic Railway Graph representation using NetworkX.
    Nodes = Stations, Junctions
    Edges = Railway Sections (with dynamic MPS, TSR, weather, occupancy, capacity)
    """
    def __init__(self):
        self.graph = nx.DiGraph()
        self.stations_dict = {}
        self.sections_dict = {}
        self._initialize_default_corridor()

    def _initialize_default_corridor(self):
        """Build nationwide multi-corridor network connecting 10 real Indian Railways trains."""
        stations_data = [
            # Delhi Hub
            {"id": "NDLS", "code": "NDLS", "name": "New Delhi", "lat": 28.6139, "lng": 77.2090, "platforms": 16, "dwell": 5.0, "seq": 0},
            {"id": "DEC", "code": "DEC", "name": "Delhi Cantt", "lat": 28.5892, "lng": 77.1309, "platforms": 4, "dwell": 2.0, "seq": 1},
            
            # Central Trunk
            {"id": "MTJ", "code": "MTJ", "name": "Mathura Junction", "lat": 27.4924, "lng": 77.6737, "platforms": 10, "dwell": 3.0, "seq": 1},
            {"id": "AGC", "code": "AGC", "name": "Agra Cantt", "lat": 27.1577, "lng": 78.0081, "platforms": 6, "dwell": 5.0, "seq": 2},
            {"id": "GWL", "code": "GWL", "name": "Gwalior Junction", "lat": 26.2183, "lng": 78.1828, "platforms": 5, "dwell": 3.0, "seq": 3},
            {"id": "VGLJ", "code": "VGLJ", "name": "VGL Jhansi Junction", "lat": 25.4484, "lng": 78.5685, "platforms": 8, "dwell": 8.0, "seq": 4},
            {"id": "BINA", "code": "BINA", "name": "Bina Junction", "lat": 24.1704, "lng": 78.1856, "platforms": 6, "dwell": 4.0, "seq": 5},
            {"id": "BPL", "code": "BPL", "name": "Bhopal Junction", "lat": 23.2599, "lng": 77.4126, "platforms": 6, "dwell": 5.0, "seq": 6},
            {"id": "RKMP", "code": "RKMP", "name": "Rani Kamlapati", "lat": 23.2057, "lng": 77.4379, "platforms": 5, "dwell": 5.0, "seq": 7},

            # Western Line (Mumbai Rajdhani)
            {"id": "KOTA", "code": "KOTA", "name": "Kota Junction", "lat": 25.2138, "lng": 75.8648, "platforms": 6, "dwell": 10.0, "seq": 2},
            {"id": "RTM", "code": "RTM", "name": "Ratlam Junction", "lat": 23.3344, "lng": 75.0370, "platforms": 7, "dwell": 5.0, "seq": 3},
            {"id": "BRC", "code": "BRC", "name": "Vadodara Junction", "lat": 22.3107, "lng": 73.1812, "platforms": 7, "dwell": 10.0, "seq": 4},
            {"id": "ST", "code": "ST", "name": "Surat", "lat": 21.2048, "lng": 72.8406, "platforms": 4, "dwell": 5.0, "seq": 5},
            {"id": "MMCT", "code": "MMCT", "name": "Mumbai Central", "lat": 18.9696, "lng": 72.8193, "platforms": 9, "dwell": 0.0, "seq": 6},

            # Eastern Line (Howrah / Sealdah / Dibrugarh)
            {"id": "CNB", "code": "CNB", "name": "Kanpur Central", "lat": 26.4547, "lng": 80.3507, "platforms": 10, "dwell": 5.0, "seq": 1},
            {"id": "PRYJ", "code": "PRYJ", "name": "Prayagraj Junction", "lat": 25.4402, "lng": 81.8315, "platforms": 10, "dwell": 5.0, "seq": 2},
            {"id": "DDU", "code": "DDU", "name": "Pt. Deen Dayal Upadhyaya", "lat": 25.2818, "lng": 83.1209, "platforms": 8, "dwell": 10.0, "seq": 3},
            {"id": "GAYA", "code": "GAYA", "name": "Gaya Junction", "lat": 24.7964, "lng": 84.9994, "platforms": 9, "dwell": 3.0, "seq": 4},
            {"id": "DHN", "code": "DHN", "name": "Dhanbad Junction", "lat": 23.7957, "lng": 86.4304, "platforms": 7, "dwell": 5.0, "seq": 5},
            {"id": "HWH", "code": "HWH", "name": "Howrah Junction", "lat": 22.5839, "lng": 88.3426, "platforms": 23, "dwell": 0.0, "seq": 6},
            {"id": "SDAH", "code": "SDAH", "name": "Sealdah", "lat": 22.5675, "lng": 88.3712, "platforms": 21, "dwell": 0.0, "seq": 6},
            {"id": "PPTA", "code": "PPTA", "name": "Patliputra Junction", "lat": 25.6179, "lng": 85.0862, "platforms": 5, "dwell": 10.0, "seq": 4},
            {"id": "KIR", "code": "KIR", "name": "Katihar Junction", "lat": 25.5542, "lng": 87.5704, "platforms": 8, "dwell": 10.0, "seq": 5},
            {"id": "GHY", "code": "GHY", "name": "Guwahati", "lat": 26.1806, "lng": 91.7539, "platforms": 7, "dwell": 15.0, "seq": 6},
            {"id": "DBRG", "code": "DBRG", "name": "Dibrugarh", "lat": 27.4728, "lng": 94.9120, "platforms": 4, "dwell": 0.0, "seq": 7},

            # Rajasthan Line (Swarna Jayanti Rajdhani)
            {"id": "JP", "code": "JP", "name": "Jaipur Junction", "lat": 26.9196, "lng": 75.7878, "platforms": 7, "dwell": 10.0, "seq": 2},
            {"id": "AII", "code": "AII", "name": "Ajmer Junction", "lat": 26.4499, "lng": 74.6399, "platforms": 6, "dwell": 5.0, "seq": 3},
            {"id": "ABR", "code": "ABR", "name": "Abu Road", "lat": 24.4819, "lng": 72.7818, "platforms": 3, "dwell": 5.0, "seq": 4},
            {"id": "PNU", "code": "PNU", "name": "Palanpur Junction", "lat": 24.1724, "lng": 72.4346, "platforms": 3, "dwell": 2.0, "seq": 5},
            {"id": "ADI", "code": "ADI", "name": "Ahmedabad Junction", "lat": 23.0225, "lng": 72.5714, "platforms": 12, "dwell": 0.0, "seq": 6},

            # Northern Line (Jammu Rajdhani)
            {"id": "PNP", "code": "PNP", "name": "Panipat Junction", "lat": 29.3909, "lng": 76.9635, "platforms": 5, "dwell": 2.0, "seq": 1},
            {"id": "UMB", "code": "UMB", "name": "Ambala Cantt", "lat": 30.3346, "lng": 76.8398, "platforms": 8, "dwell": 8.0, "seq": 2},
            {"id": "LDH", "code": "LDH", "name": "Ludhiana Junction", "lat": 30.9010, "lng": 75.8573, "platforms": 7, "dwell": 8.0, "seq": 3},
            {"id": "JRC", "code": "JRC", "name": "Jalandhar Cantt", "lat": 31.3006, "lng": 75.6179, "platforms": 3, "dwell": 2.0, "seq": 4},
            {"id": "PTKC", "code": "PTKC", "name": "Pathankot Cantt", "lat": 32.2536, "lng": 75.6698, "platforms": 3, "dwell": 5.0, "seq": 5},
            {"id": "JAT", "code": "JAT", "name": "Jammu Tawi", "lat": 32.7060, "lng": 74.8797, "platforms": 7, "dwell": 0.0, "seq": 6},

            # Southern Line (Kerala, Tamil Nadu, Telangana)
            {"id": "NGP", "code": "NGP", "name": "Nagpur Junction", "lat": 21.1458, "lng": 79.0882, "platforms": 8, "dwell": 10.0, "seq": 7},
            {"id": "BPQ", "code": "BPQ", "name": "Balharshah Junction", "lat": 19.8510, "lng": 79.3512, "platforms": 5, "dwell": 5.0, "seq": 8},
            {"id": "SKZR", "code": "SKZR", "name": "Sirpur Kaghaznagar", "lat": 19.3315, "lng": 79.6019, "platforms": 3, "dwell": 2.0, "seq": 8},
            {"id": "KZJ", "code": "KZJ", "name": "Kazipet Junction", "lat": 17.9784, "lng": 79.5019, "platforms": 3, "dwell": 2.0, "seq": 9},
            {"id": "SC", "code": "SC", "name": "Secunderabad Junction", "lat": 17.4339, "lng": 78.5016, "platforms": 10, "dwell": 10.0, "seq": 10},
            {"id": "HYB", "code": "HYB", "name": "Hyderabad Deccan", "lat": 17.3930, "lng": 78.4687, "platforms": 6, "dwell": 0.0, "seq": 11},
            {"id": "BZA", "code": "BZA", "name": "Vijayawada Junction", "lat": 16.5062, "lng": 80.6480, "platforms": 10, "dwell": 10.0, "seq": 9},
            {"id": "MAS", "code": "MAS", "name": "MGR Chennai Central", "lat": 13.0827, "lng": 80.2707, "platforms": 12, "dwell": 0.0, "seq": 10},
            {"id": "PER", "code": "PER", "name": "Perambur", "lat": 13.1096, "lng": 80.2372, "platforms": 4, "dwell": 2.0, "seq": 10},
            {"id": "ERS", "code": "ERS", "name": "Ernakulam Junction", "lat": 9.9674, "lng": 76.2898, "platforms": 6, "dwell": 5.0, "seq": 11},
            {"id": "TVC", "code": "TVC", "name": "Trivandrum Central", "lat": 8.4875, "lng": 76.9526, "platforms": 5, "dwell": 0.0, "seq": 12}
        ]

        sections_data = [
            # Central Trunk
            {"id": "NDLS-MTJ", "from": "NDLS", "to": "MTJ", "dist": 141.0, "mps": 130.0, "coords": [[28.6139, 77.2090], [27.4924, 77.6737]]},
            {"id": "MTJ-AGC", "from": "MTJ", "to": "AGC", "dist": 54.0, "mps": 130.0, "coords": [[27.4924, 77.6737], [27.1577, 78.0081]]},
            {"id": "AGC-GWL", "from": "AGC", "to": "GWL", "dist": 118.0, "mps": 110.0, "coords": [[27.1577, 78.0081], [26.2183, 78.1828]]},
            {"id": "GWL-VGLJ", "from": "GWL", "to": "VGLJ", "dist": 97.0, "mps": 110.0, "coords": [[26.2183, 78.1828], [25.4484, 78.5685]]},
            {"id": "VGLJ-BINA", "from": "VGLJ", "to": "BINA", "dist": 153.0, "mps": 110.0, "coords": [[25.4484, 78.5685], [24.1704, 78.1856]]},
            {"id": "BINA-BPL", "from": "BINA", "to": "BPL", "dist": 139.0, "mps": 120.0, "coords": [[24.1704, 78.1856], [23.2599, 77.4126]]},
            {"id": "BPL-RKMP", "from": "BPL", "to": "RKMP", "dist": 6.0, "mps": 60.0, "coords": [[23.2599, 77.4126], [23.2057, 77.4379]]},

            # Western Corridor
            {"id": "MTJ-KOTA", "from": "MTJ", "to": "KOTA", "dist": 324.0, "mps": 130.0, "coords": [[27.4924, 77.6737], [25.2138, 75.8648]]},
            {"id": "KOTA-RTM", "from": "KOTA", "to": "RTM", "dist": 266.0, "mps": 130.0, "coords": [[25.2138, 75.8648], [23.3344, 75.0370]]},
            {"id": "RTM-BRC", "from": "RTM", "to": "BRC", "dist": 261.0, "mps": 130.0, "coords": [[23.3344, 75.0370], [22.3107, 73.1812]]},
            {"id": "BRC-ST", "from": "BRC", "to": "ST", "dist": 130.0, "mps": 130.0, "coords": [[22.3107, 73.1812], [21.2048, 72.8406]]},
            {"id": "ST-MMCT", "from": "ST", "to": "MMCT", "dist": 263.0, "mps": 130.0, "coords": [[21.2048, 72.8406], [18.9696, 72.8193]]},

            # Eastern Corridor
            {"id": "NDLS-CNB", "from": "NDLS", "to": "CNB", "dist": 440.0, "mps": 130.0, "coords": [[28.6139, 77.2090], [26.4547, 80.3507]]},
            {"id": "CNB-PRYJ", "from": "CNB", "to": "PRYJ", "dist": 194.0, "mps": 130.0, "coords": [[26.4547, 80.3507], [25.4402, 81.8315]]},
            {"id": "PRYJ-DDU", "from": "PRYJ", "to": "DDU", "dist": 153.0, "mps": 130.0, "coords": [[25.4402, 81.8315], [25.2818, 83.1209]]},
            {"id": "DDU-GAYA", "from": "DDU", "to": "GAYA", "dist": 205.0, "mps": 120.0, "coords": [[25.2818, 83.1209], [24.7964, 84.9994]]},
            {"id": "GAYA-DHN", "from": "GAYA", "to": "DHN", "dist": 201.0, "mps": 120.0, "coords": [[24.7964, 84.9994], [23.7957, 86.4304]]},
            {"id": "DHN-HWH", "from": "DHN", "to": "HWH", "dist": 254.0, "mps": 130.0, "coords": [[23.7957, 86.4304], [22.5839, 88.3426]]},
            {"id": "DHN-SDAH", "from": "DHN", "to": "SDAH", "dist": 259.0, "mps": 130.0, "coords": [[23.7957, 86.4304], [22.5675, 88.3712]]},
            {"id": "DDU-PPTA", "from": "DDU", "to": "PPTA", "dist": 212.0, "mps": 110.0, "coords": [[25.2818, 83.1209], [25.6179, 85.0862]]},
            {"id": "PPTA-KIR", "from": "PPTA", "to": "KIR", "dist": 289.0, "mps": 100.0, "coords": [[25.6179, 85.0862], [25.5542, 87.5704]]},
            {"id": "KIR-GHY", "from": "KIR", "to": "GHY", "dist": 605.0, "mps": 110.0, "coords": [[25.5542, 87.5704], [26.1806, 91.7539]]},
            {"id": "GHY-DBRG", "from": "GHY", "to": "DBRG", "dist": 544.0, "mps": 100.0, "coords": [[26.1806, 91.7539], [27.4728, 94.9120]]},

            # Rajasthan Line
            {"id": "NDLS-DEC", "from": "NDLS", "to": "DEC", "dist": 16.0, "mps": 90.0, "coords": [[28.6139, 77.2090], [28.5892, 77.1309]]},
            {"id": "DEC-JP", "from": "DEC", "to": "JP", "dist": 288.0, "mps": 110.0, "coords": [[28.5892, 77.1309], [26.9196, 75.7878]]},
            {"id": "JP-AII", "from": "JP", "to": "AII", "dist": 135.0, "mps": 110.0, "coords": [[26.9196, 75.7878], [26.4499, 74.6399]]},
            {"id": "AII-ABR", "from": "AII", "to": "ABR", "dist": 305.0, "mps": 110.0, "coords": [[26.4499, 74.6399], [24.4819, 72.7818]]},
            {"id": "ABR-PNU", "from": "ABR", "to": "PNU", "dist": 52.0, "mps": 110.0, "coords": [[24.4819, 72.7818], [24.1724, 72.4346]]},
            {"id": "PNU-ADI", "from": "PNU", "to": "ADI", "dist": 138.0, "mps": 110.0, "coords": [[24.1724, 72.4346], [23.0225, 72.5714]]},

            # Northern Line
            {"id": "NDLS-PNP", "from": "NDLS", "to": "PNP", "dist": 89.0, "mps": 110.0, "coords": [[28.6139, 77.2090], [29.3909, 76.9635]]},
            {"id": "PNP-UMB", "from": "PNP", "to": "UMB", "dist": 110.0, "mps": 130.0, "coords": [[29.3909, 76.9635], [30.3346, 76.8398]]},
            {"id": "UMB-LDH", "from": "UMB", "to": "LDH", "dist": 114.0, "mps": 130.0, "coords": [[30.3346, 76.8398], [30.9010, 75.8573]]},
            {"id": "LDH-JRC", "from": "LDH", "to": "JRC", "dist": 52.0, "mps": 110.0, "coords": [[30.9010, 75.8573], [31.3006, 75.6179]]},
            {"id": "JRC-PTKC", "from": "JRC", "to": "PTKC", "dist": 113.0, "mps": 110.0, "coords": [[31.3006, 75.6179], [32.2536, 75.6698]]},
            {"id": "PTKC-JAT", "from": "PTKC", "to": "JAT", "dist": 99.0, "mps": 110.0, "coords": [[32.2536, 75.6698], [32.7060, 74.8797]]},

            # Southern Lines
            {"id": "BPL-NGP", "from": "BPL", "to": "NGP", "dist": 390.0, "mps": 120.0, "coords": [[23.2599, 77.4126], [21.1458, 79.0882]]},
            {"id": "NGP-BPQ", "from": "NGP", "to": "BPQ", "dist": 208.0, "mps": 110.0, "coords": [[21.1458, 79.0882], [19.8510, 79.3512]]},
            {"id": "BPQ-SKZR", "from": "BPQ", "to": "SKZR", "dist": 70.0, "mps": 110.0, "coords": [[19.8510, 79.3512], [19.3315, 79.6019]]},
            {"id": "SKZR-KZJ", "from": "SKZR", "to": "KZJ", "dist": 165.0, "mps": 110.0, "coords": [[19.3315, 79.6019], [17.9784, 79.5019]]},
            {"id": "KZJ-SC", "from": "KZJ", "to": "SC", "dist": 132.0, "mps": 110.0, "coords": [[17.9784, 79.5019], [17.4339, 78.5016]]},
            {"id": "SC-HYB", "from": "SC", "to": "HYB", "dist": 9.0, "mps": 60.0, "coords": [[17.4339, 78.5016], [17.3930, 78.4687]]},
            {"id": "BPQ-BZA", "from": "BPQ", "to": "BZA", "dist": 451.0, "mps": 120.0, "coords": [[19.8510, 79.3512], [16.5062, 80.6480]]},
            {"id": "BZA-MAS", "from": "BZA", "to": "MAS", "dist": 431.0, "mps": 130.0, "coords": [[16.5062, 80.6480], [13.0827, 80.2707]]},
            {"id": "BZA-PER", "from": "BZA", "to": "PER", "dist": 425.0, "mps": 130.0, "coords": [[16.5062, 80.6480], [13.1096, 80.2372]]},
            {"id": "PER-ERS", "from": "PER", "to": "ERS", "dist": 687.0, "mps": 110.0, "coords": [[13.1096, 80.2372], [9.9674, 76.2898]]},
            {"id": "ERS-TVC", "from": "ERS", "to": "TVC", "dist": 206.0, "mps": 100.0, "coords": [[9.9674, 76.2898], [8.4875, 76.9526]]}
        ]

        for st in stations_data:
            self.stations_dict[st["id"]] = st
            self.graph.add_node(st["id"], **st)

        for sec in sections_data:
            self.sections_dict[sec["id"]] = {
                **sec,
                "current_speed_limit": sec["mps"],
                "is_blocked": False,
                "weather": "CLEAR",
                "occupied_by": None,
                "congestion": 0.0
            }
            # Add bidirectional edges for railway tracks
            self.graph.add_edge(sec["from"], sec["to"], **self.sections_dict[sec["id"]])
            self.graph.add_edge(sec["to"], sec["from"], **self.sections_dict[sec["id"]])

    def update_section_state(self, section_id: str, **kwargs):
        if section_id in self.sections_dict:
            self.sections_dict[section_id].update(kwargs)
            sec = self.sections_dict[section_id]
            u, v = sec["from"], sec["to"]
            if self.graph.has_edge(u, v):
                self.graph[u][v].update(kwargs)
            if self.graph.has_edge(v, u):
                self.graph[v][u].update(kwargs)

    def get_section_travel_time(self, section_id: str, train_speed_kmh: float) -> float:
        sec = self.sections_dict.get(section_id)
        if not sec:
            return 30.0
        
        if sec.get("is_blocked"):
            return 999.0  # Blocked section
            
        effective_speed = min(sec.get("current_speed_limit", 110.0), train_speed_kmh)
        
        # Weather penalty
        if sec.get("weather") == "FOG":
            effective_speed = min(effective_speed, 45.0)  # Max 45 km/h in fog
        elif sec.get("weather") == "HEAVY_RAIN":
            effective_speed = min(effective_speed, 65.0)
            
        if effective_speed <= 5.0:
            effective_speed = 5.0
            
        travel_time_hours = sec["dist"] / effective_speed
        return travel_time_hours * 60.0  # return minutes

    def get_downstream_stations(self, current_station_id: str, destination_station_id: str) -> List[str]:
        try:
            path = nx.shortest_path(self.graph, source=current_station_id, target=destination_station_id)
            return path[1:]  # Exclude current station
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_downstream_sections(self, current_station_id: str, destination_station_id: str) -> List[str]:
        stations = [current_station_id] + self.get_downstream_stations(current_station_id, destination_station_id)
        sections = []
        for i in range(len(stations) - 1):
            sec_id = f"{stations[i]}-{stations[i+1]}"
            if sec_id not in self.sections_dict:
                sec_id = f"{stations[i+1]}-{stations[i]}"
            sections.append(sec_id)
        return sections
