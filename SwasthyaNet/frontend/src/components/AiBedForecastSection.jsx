import React, { useState, useEffect } from 'react';
import api from '../services/api';
import {
  Bed,
  Sparkles,
  Calendar,
  AlertCircle,
  TrendingUp,
  RefreshCw,
  Layers
} from 'lucide-react';

const AiBedForecastSection = ({ centreId, wards = [], title = "AI Bed Occupancy Forecasting", lastUpdated }) => {
  const [selectedWardId, setSelectedWardId] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (wards.length > 0 && !selectedWardId) {
      setSelectedWardId(wards[0].ward_id);
    }
  }, [wards]);

  const fetchBedForecast = async (wardId) => {
    if (!centreId || !wardId) return;
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/ai/bed-forecast/${centreId}/${wardId}`);
      setForecastData(res.data);
    } catch (err) {
      console.error("AI Bed Forecast fetch error:", err);
      setError("Unable to generate bed occupancy forecasts. Please check network connection.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedWardId) {
      fetchBedForecast(selectedWardId);
    }
  }, [centreId, selectedWardId, lastUpdated]);

  const selectedWard = wards.find(w => w.ward_id === selectedWardId);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-gradient-to-tr from-violet-600 to-purple-600 rounded-lg text-white shadow-sm">
            <Bed className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-slate-800">{title}</h3>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-purple-50 text-purple-700 border border-purple-200">
                <Sparkles className="w-3 h-3" /> Multi-Horizon AI
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Proactive capacity planning with 1-day, 7-day, and 14-day surge forecasting
            </p>
          </div>
        </div>

        {/* Refresh Button */}
        <button
          onClick={() => fetchBedForecast(selectedWardId)}
          disabled={loading || !selectedWardId}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Ward Selector Tabs */}
      {wards.length > 1 && (
        <div className="flex items-center gap-2 my-4 overflow-x-auto pb-1">
          <span className="text-xs font-semibold text-slate-500 mr-1 flex items-center gap-1">
            <Layers className="w-3.5 h-3.5" /> Ward:
          </span>
          {wards.map(ward => (
            <button
              key={ward.ward_id}
              onClick={() => setSelectedWardId(ward.ward_id)}
              className={`px-3.5 py-1.5 text-xs font-medium rounded-lg transition whitespace-nowrap ${
                selectedWardId === ward.ward_id
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {ward.ward_name} Ward ({ward.total_beds} beds)
            </button>
          ))}
        </div>
      )}

      {/* Content Body */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-pulse mt-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-44 bg-slate-100 rounded-xl border border-slate-200"></div>
          ))}
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-sm flex items-center gap-2 mt-4">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      ) : !forecastData || !forecastData.forecasts ? (
        <div className="text-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-slate-500 text-sm mt-4">
          <Bed className="w-8 h-8 mx-auto text-slate-400 mb-2" />
          No prediction available for this ward.
        </div>
      ) : (
        <div className="mt-4">
          {/* Current Status Bar */}
          <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 mb-5 flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="text-xs text-slate-500 block">Monitored Ward</span>
              <span className="font-bold text-slate-800 text-sm">
                {forecastData.ward_name} Ward (Total Capacity: {forecastData.total_beds} Beds)
              </span>
            </div>

            <div className="flex items-center gap-6">
              <div>
                <span className="text-xs text-slate-500 block">Current Occupancy</span>
                <span className="font-bold text-slate-800 text-sm">
                  {forecastData.current_occupied_beds} / {forecastData.total_beds} beds{' '}
                  <span className="text-xs font-medium text-slate-500">
                    ({forecastData.current_occupancy_rate_pct}%)
                  </span>
                </span>
              </div>
              <div>
                <span className="text-xs text-slate-500 block">Available Headroom</span>
                <span className="font-bold text-emerald-600 text-sm">
                  {forecastData.current_available_beds} beds free
                </span>
              </div>
            </div>
          </div>

          {/* 3 Forecast Horizon Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              {
                key: 't_plus_1',
                title: 'Tomorrow (t+1)',
                desc: 'Immediate next-day census projection',
                data: forecastData.forecasts.t_plus_1
              },
              {
                key: 't_plus_7',
                title: '7-Day Horizon (t+7)',
                desc: 'Weekly cyclical peak forecast',
                data: forecastData.forecasts.t_plus_7
              },
              {
                key: 't_plus_14',
                title: '14-Day Horizon (t+14)',
                desc: '2-week surge & trend trajectory',
                data: forecastData.forecasts.t_plus_14
              }
            ].map(horizon => {
              const hData = horizon.data;
              if (!hData) return null;

              const isSurge = hData.predicted_occupancy_rate_pct >= 90;
              const isWarning = hData.predicted_occupancy_rate_pct >= 80 && !isSurge;

              return (
                <div
                  key={horizon.key}
                  className={`p-5 rounded-xl border transition ${
                    isSurge
                      ? 'bg-gradient-to-b from-rose-50 to-white border-rose-200 shadow-sm'
                      : isWarning
                      ? 'bg-gradient-to-b from-amber-50 to-white border-amber-200 shadow-sm'
                      : 'bg-white border-slate-200'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
                      <Calendar className="w-4 h-4 text-purple-600" />
                      <span>{horizon.title}</span>
                    </div>
                    {isSurge ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200 animate-pulse">
                        Surge Risk
                      </span>
                    ) : isWarning ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800 border border-amber-200">
                        High Load
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
                        Normal
                      </span>
                    )}
                  </div>

                  <p className="text-[11px] text-slate-500 mb-3">{horizon.desc}</p>

                  <div className="my-2">
                    <div className="flex items-baseline justify-between mb-1">
                      <span className="text-2xl font-black text-slate-900">
                        {hData.predicted_occupied_beds}
                        <span className="text-xs font-normal text-slate-500 ml-1">
                          / {forecastData.total_beds} beds
                        </span>
                      </span>
                      <span className={`text-sm font-bold ${
                        isSurge ? 'text-rose-600' : isWarning ? 'text-amber-600' : 'text-slate-700'
                      }`}>
                        {hData.predicted_occupancy_rate_pct}%
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          isSurge
                            ? 'bg-rose-500'
                            : isWarning
                            ? 'bg-amber-500'
                            : 'bg-gradient-to-r from-purple-500 to-indigo-500'
                        }`}
                        style={{ width: `${Math.min(100, hData.predicted_occupancy_rate_pct)}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                    <span>Est. Available:</span>
                    <span className="font-semibold text-slate-800">
                      {hData.predicted_available_beds} beds free
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default AiBedForecastSection;
