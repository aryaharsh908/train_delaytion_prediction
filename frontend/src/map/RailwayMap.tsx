import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle } from 'react-leaflet';
import L from 'leaflet';
import { TrainState, SimulationState } from '../types';

interface RailwayMapProps {
  simulationState: SimulationState | null;
  networkState: { stations: any[]; sections: any[] } | null;
  onSelectTrain: (train: TrainState) => void;
  selectedTrainId?: string;
}

// Custom Leaflet DivIcon for Moving Trains
const createTrainIcon = (train: TrainState, isSelected: boolean) => {
  const color =
    train.status === 'ON_TIME'
      ? '#10b981'
      : train.status === 'SLIGHT_DELAY'
      ? '#f59e0b'
      : train.status === 'CRITICAL_DELAY'
      ? '#ef4444'
      : '#a855f7';

  const glow = isSelected ? '0 0 20px #38bdf8' : `0 0 10px ${color}`;

  return L.divIcon({
    className: 'custom-train-marker',
    html: `
      <div style="
        background: ${color};
        color: #ffffff;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 800;
        font-family: sans-serif;
        box-shadow: ${glow};
        border: 2px solid ${isSelected ? '#38bdf8' : '#ffffff'};
        display: flex;
        align-items: center;
        gap: 4px;
        white-space: nowrap;
        transform: translate(-50%, -50%);
        cursor: pointer;
      ">
        <span>🚆 ${train.train_number}</span>
        <span style="background: rgba(0,0,0,0.3); padding: 1px 4px; border-radius: 10px; font-size: 9px;">${train.speed_kmh} km/h</span>
      </div>
    `,
    iconSize: [80, 24],
    iconAnchor: [40, 12]
  });
};

// Custom Leaflet DivIcon for Stations
const createStationIcon = (station: any) => {
  return L.divIcon({
    className: 'custom-station-marker',
    html: `
      <div style="
        background: #0f172a;
        border: 2px solid #38bdf8;
        color: #f8fafc;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        box-shadow: 0 0 10px #38bdf8;
        transform: translate(-50%, -50%);
      "></div>
    `,
    iconSize: [14, 14],
    iconAnchor: [7, 7]
  });
};

export const RailwayMap: React.FC<RailwayMapProps> = ({
  simulationState,
  networkState,
  onSelectTrain,
  selectedTrainId
}) => {
  const defaultCenter: [number, number] = [26.0, 78.0]; // Centered on North-Central India trunk corridor

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <MapContainer
        center={defaultCenter}
        zoom={7}
        scrollWheelZoom={true}
        style={{ width: '100%', height: '100%' }}
      >
        {/* Dark Map Tiles */}
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* Render Railway Sections (Polylines) */}
        {networkState?.sections.map((sec) => {
          const coords: [number, number][] = sec.coords || [];
          if (coords.length < 2) return null;

          const isBlocked = sec.is_blocked;
          const isFog = sec.weather === 'FOG';
          const isRain = sec.weather === 'HEAVY_RAIN';
          const isCongested = sec.congestion > 0.5;

          const strokeColor = isBlocked
            ? '#ef4444'
            : isFog
            ? '#f59e0b'
            : isRain
            ? '#38bdf8'
            : isCongested
            ? '#a855f7'
            : '#10b981';

          return (
            <React.Fragment key={sec.id}>
              <Polyline
                positions={coords}
                pathOptions={{
                  color: strokeColor,
                  weight: isBlocked || isFog || isCongested ? 5 : 3,
                  dashArray: isBlocked ? '8, 8' : undefined,
                  opacity: 0.85
                }}
              >
                <Popup>
                  <div style={{ fontSize: '0.8rem', color: '#f8fafc' }}>
                    <strong>Section: {sec.id}</strong><br />
                    Distance: {sec.dist} km<br />
                    Max Speed (MPS): {sec.mps} km/h<br />
                    Condition: <span style={{ color: strokeColor, fontWeight: 700 }}>{sec.weather || 'CLEAR'}</span>
                  </div>
                </Popup>
              </Polyline>

              {/* Fog Zone Overlay Circle */}
              {isFog && (
                <Circle
                  center={[(coords[0][0] + coords[1][0]) / 2, (coords[0][1] + coords[1][1]) / 2]}
                  radius={35000}
                  pathOptions={{
                    color: '#f59e0b',
                    fillColor: '#f59e0b',
                    fillOpacity: 0.25,
                    dashArray: '4, 4'
                  }}
                />
              )}
            </React.Fragment>
          );
        })}

        {/* Render Stations (Markers) */}
        {networkState?.stations.map((st) => (
          <Marker
            key={st.id}
            position={[st.lat, st.lng]}
            icon={createStationIcon(st)}
          >
            <Popup>
              <div style={{ fontSize: '0.8rem', color: '#f8fafc' }}>
                <strong>{st.name} ({st.code})</strong><br />
                Platforms: {st.platforms}<br />
                Scheduled Dwell: {st.dwell} mins
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Render Active Trains (Moving Markers) */}
        {simulationState?.trains.map((train) => (
          <Marker
            key={train.train_id}
            position={[train.latitude, train.longitude]}
            icon={createTrainIcon(train, train.train_id === selectedTrainId)}
            eventHandlers={{
              click: () => onSelectTrain(train)
            }}
          >
            <Popup>
              <div style={{ fontSize: '0.8rem', color: '#f8fafc' }}>
                <strong>{train.train_number} - {train.train_name}</strong><br />
                Speed: {train.speed_kmh} km/h<br />
                Delay: +{Math.round(train.current_delay_minutes)} mins<br />
                Next Station: {train.next_station_name}
              </div>
            </Popup>
          </Marker>
        ))}

      </MapContainer>
    </div>
  );
};
