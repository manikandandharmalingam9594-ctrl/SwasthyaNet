import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Link } from 'react-router-dom';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Building2, Stethoscope, MapPin, Activity, Filter, Eye, ChevronRight } from 'lucide-react';

// Fix Leaflet's default icon path issues in React
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

L.Icon.Default.mergeOptions({
  iconRetinaUrl,
  iconUrl,
  shadowUrl,
});

// Custom Rich Marker Icon for PHC and CHC
const createCustomMarkerIcon = (centreType, healthScore, isCurrent = false) => {
  const isChc = centreType?.toUpperCase().includes('CHC');
  const typeBg = isChc ? '#7c3aed' : '#059669'; // Purple for CHC, Emerald for PHC
  const typeText = isChc ? 'CHC' : 'PHC';
  
  let scoreBorder = '#10b981'; // Green
  let scoreBadgeBg = '#d1fae5';
  let scoreBadgeText = '#065f46';
  
  if (healthScore === 'N/A' || healthScore == null) {
    scoreBorder = '#94a3b8';
    scoreBadgeBg = '#f1f5f9';
    scoreBadgeText = '#475569';
  } else if (healthScore < 50) {
    scoreBorder = '#ef4444'; // Red
    scoreBadgeBg = '#fee2e2';
    scoreBadgeText = '#991b1b';
  } else if (healthScore < 80) {
    scoreBorder = '#f59e0b'; // Amber
    scoreBadgeBg = '#fef3c7';
    scoreBadgeText = '#92400e';
  }

  const pulseRing = isCurrent ? `
    <div style="
      position: absolute;
      top: -6px;
      left: -6px;
      right: -6px;
      bottom: -6px;
      border: 2px solid ${typeBg};
      border-radius: 16px;
      animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
      opacity: 0.75;
    "></div>
  ` : '';

  const html = `
    <div style="position: relative; display: flex; flex-direction: column; align-items: center; cursor: pointer; transform: translate(-50%, -100%);">
      ${pulseRing}
      <div style="
        background: ${typeBg};
        color: white;
        border: 2.5px solid ${scoreBorder};
        box-shadow: 0 4px 14px rgba(0,0,0,0.3);
        border-radius: 10px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.5px;
        display: flex;
        align-items: center;
        gap: 5px;
        white-space: nowrap;
      ">
        <span>${typeText}</span>
        ${healthScore !== 'N/A' && healthScore != null ? `
          <span style="background: ${scoreBadgeBg}; color: ${scoreBadgeText}; font-size: 9px; padding: 1px 4px; border-radius: 4px; font-weight: 700;">
            ${healthScore}
          </span>
        ` : ''}
      </div>
      <div style="
        width: 0; 
        height: 0; 
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-top: 8px solid ${scoreBorder};
        margin-top: -1px;
      "></div>
      <div style="
        width: 6px;
        height: 6px;
        background: ${scoreBorder};
        border-radius: 50%;
        margin-top: -2px;
      "></div>
    </div>
  `;

  return L.divIcon({
    html: html,
    className: 'custom-facility-marker',
    iconSize: [0, 0],
    iconAnchor: [0, 0],
    popupAnchor: [0, -32]
  });
};

// Auto Bounds & Center Controller Component
function MapBoundsController({ centres }) {
  const map = useMap();

  useEffect(() => {
    if (!centres || centres.length === 0) return;
    const valid = centres.filter(c => c.latitude && c.longitude);
    if (valid.length === 0) return;

    if (valid.length === 1) {
      map.setView([valid[0].latitude, valid[0].longitude], 13);
    } else {
      const bounds = L.latLngBounds(valid.map(c => [c.latitude, c.longitude]));
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 });
    }
  }, [centres, map]);

  return null;
}

const DistrictMap = ({ centres = [], title = "Healthcare Network Map", currentCentreId = null, height = "420px" }) => {
  const [filterType, setFilterType] = useState('ALL'); // 'ALL' | 'PHC' | 'CHC'

  const validCentres = centres.filter(c => c.latitude && c.longitude);
  
  const filteredCentres = validCentres.filter(c => {
    if (filterType === 'PHC') return c.centre_type === 'PHC';
    if (filterType === 'CHC') return c.centre_type === 'CHC';
    return true;
  });

  const phcCount = validCentres.filter(c => c.centre_type === 'PHC').length;
  const chcCount = validCentres.filter(c => c.centre_type === 'CHC').length;

  // Initial center fallback
  let initialLat = 11.0168;
  let initialLng = 76.9558;
  if (validCentres.length > 0) {
    initialLat = validCentres[0].latitude;
    initialLng = validCentres[0].longitude;
  }

  return (
    <div className="bg-white shadow-sm rounded-xl border border-slate-200 overflow-hidden mb-8">
      {/* Map Header & Filter Controls */}
      <div className="px-5 py-3.5 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 bg-slate-50">
        <div className="flex items-center space-x-2">
          <MapPin className="h-5 w-5 text-indigo-600" />
          <h3 className="font-bold text-slate-800 text-sm sm:text-base">{title}</h3>
          <span className="text-xs bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full font-medium">
            {filteredCentres.length} {filteredCentres.length === 1 ? 'facility' : 'facilities'}
          </span>
        </div>

        {/* PHC / CHC Type Filter Pills */}
        <div className="flex items-center space-x-1.5 bg-white p-1 rounded-lg border border-slate-200 shadow-sm text-xs font-medium">
          <button
            onClick={() => setFilterType('ALL')}
            className={`px-2.5 py-1 rounded-md transition ${
              filterType === 'ALL'
                ? 'bg-indigo-600 text-white font-semibold shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            All ({validCentres.length})
          </button>
          <button
            onClick={() => setFilterType('PHC')}
            className={`px-2.5 py-1 rounded-md transition flex items-center ${
              filterType === 'PHC'
                ? 'bg-emerald-600 text-white font-semibold shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400 mr-1.5 inline-block"></span>
            PHC ({phcCount})
          </button>
          <button
            onClick={() => setFilterType('CHC')}
            className={`px-2.5 py-1 rounded-md transition flex items-center ${
              filterType === 'CHC'
                ? 'bg-purple-600 text-white font-semibold shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-purple-400 mr-1.5 inline-block"></span>
            CHC ({chcCount})
          </button>
        </div>
      </div>

      {/* Leaflet Map */}
      <div style={{ height }} className="w-full relative">
        <MapContainer 
          center={[initialLat, initialLng]} 
          zoom={11} 
          scrollWheelZoom={true} 
          className="h-full w-full z-0"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          <MapBoundsController centres={filteredCentres} />

          {filteredCentres.map((centre) => {
            const isCurrent = currentCentreId && centre.centre_id === currentCentreId;
            return (
              <Marker 
                key={centre.centre_id} 
                position={[centre.latitude, centre.longitude]}
                icon={createCustomMarkerIcon(centre.centre_type, centre.healthScore, isCurrent)}
              >
                <Popup>
                  <div className="p-1 min-w-[200px]">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        centre.centre_type === 'CHC' ? 'bg-purple-100 text-purple-800' : 'bg-emerald-100 text-emerald-800'
                      }`}>
                        {centre.centre_type}
                      </span>
                      {centre.healthScore !== 'N/A' && centre.healthScore != null && (
                        <span className={`text-xs font-extrabold ${
                          centre.healthScore >= 80 ? 'text-emerald-600' :
                          centre.healthScore >= 50 ? 'text-amber-500' : 'text-rose-600'
                        }`}>
                          Score: {centre.healthScore}/100
                        </span>
                      )}
                    </div>

                    <h3 className="font-bold text-slate-900 text-sm leading-snug">{centre.centre_name}</h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {centre.districtName ? `${centre.districtName} District` : ''} 
                      {centre.block ? ` • ${centre.block}` : ''}
                    </p>

                    <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
                      <span>Status: <strong className="text-slate-800">{centre.status || 'Active'}</strong></span>
                      {centre.total_beds ? (
                        <span>Beds: <strong className="text-slate-800">{centre.total_beds}</strong></span>
                      ) : null}
                    </div>

                    <Link 
                      to={`/centres/${centre.centre_id}`}
                      className="mt-3 flex items-center justify-center w-full bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold py-1.5 px-3 rounded-lg shadow-sm transition text-center"
                    >
                      <span>View Centre Details</span>
                      <ChevronRight className="h-3.5 w-3.5 ml-1" />
                    </Link>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>

        {/* Floating Legend */}
        <div className="absolute bottom-3 left-3 bg-white/95 backdrop-blur-xs p-2.5 rounded-lg border border-slate-200 shadow-md z-1000 text-[11px] space-y-1.5 pointer-events-auto">
          <div className="font-bold text-slate-700 text-[10px] uppercase tracking-wider mb-1">Legend</div>
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-xs bg-emerald-600 inline-block"></span>
              <span className="text-slate-600 font-medium">PHC</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-xs bg-purple-600 inline-block"></span>
              <span className="text-slate-600 font-medium">CHC</span>
            </div>
          </div>
          <div className="flex items-center space-x-2 pt-1 border-t border-slate-100 text-[10px] text-slate-500">
            <span className="flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1"></span>&gt;80</span>
            <span className="flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1"></span>50-80</span>
            <span className="flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-rose-500 mr-1"></span>&lt;50</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DistrictMap;
