import React, { useState, useEffect } from 'react';
import api from '../services/api';
import {
  Sparkles,
  AlertTriangle,
  Bed,
  Package,
  Building2,
  TrendingDown,
  RefreshCw,
  Search,
  Filter,
  ArrowRight,
  ShieldCheck,
  Calendar
} from 'lucide-react';
import AiStockoutPredictionSection from './AiStockoutPredictionSection';
import AiBedForecastSection from './AiBedForecastSection';

const AiAggregatedInsightsSection = ({ centres = [], title = "AI Predictive Insights & Forecasts", isSuperAdmin = false }) => {
  const [activeSubTab, setActiveSubTab] = useState('summary'); // 'summary' | 'facility_drilldown'
  const [selectedCentreId, setSelectedCentreId] = useState(centres.length > 0 ? centres[0].centre_id : null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [criticalStockouts, setCriticalStockouts] = useState([]);
  const [wardSurgeAlerts, setWardSurgeAlerts] = useState([]);
  const [medicinesList, setMedicinesList] = useState([]);
  const [selectedFacilityData, setSelectedFacilityData] = useState({
    inventory: [],
    wards: []
  });

  useEffect(() => {
    if (centres.length > 0 && !selectedCentreId) {
      setSelectedCentreId(centres[0].centre_id);
    }
  }, [centres]);

  const fetchAggregatedData = async () => {
    if (centres.length === 0) return;
    try {
      setLoading(true);
      setError(null);

      // 1. Fetch medicines catalog
      const medsRes = await api.get('/medicines');
      const meds = medsRes.data || [];
      setMedicinesList(meds);

      // 2. Sample top high-demand medicines across authorized centres for stock-out screening
      const highDemandMedIds = [1, 2, 3, 4, 7, 10, 14, 16]; // Paracetamol, Ibuprofen, Amox, Azithro, Cetirizine, ORS, Amlodipine, Metformin
      const stockRequests = [];

      centres.forEach(c => {
        highDemandMedIds.forEach(medId => {
          stockRequests.push(
            api.get(`/ai/stockout/${c.centre_id}/${medId}`)
              .then(res => res.data)
              .catch(() => null)
          );
        });
      });

      // 3. Sample wards across authorized centres for bed surge screening
      const bedRequests = [];
      const wardsByCentrePromises = centres.map(c =>
        api.get(`/centres/${c.centre_id}/wards`)
          .then(res => ({ centre_id: c.centre_id, wards: res.data || [] }))
          .catch(() => ({ centre_id: c.centre_id, wards: [] }))
      );

      const wardsByCentre = await Promise.all(wardsByCentrePromises);

      wardsByCentre.forEach(({ centre_id, wards }) => {
        wards.forEach(w => {
          bedRequests.push(
            api.get(`/ai/bed-forecast/${centre_id}/${w.ward_id}`)
              .then(res => res.data)
              .catch(() => null)
          );
        });
      });

      // Execute all screening requests concurrently
      const [stockResults, bedResults] = await Promise.all([
        Promise.all(stockRequests),
        Promise.all(bedRequests)
      ]);

      // Filter critical and high stockout risks
      const validStockRisks = stockResults.filter(
        item => item && (item.risk_level === 'CRITICAL' || item.risk_level === 'HIGH' || item.risk_level === 'STOCK_OUT')
      );
      validStockRisks.sort((a, b) => (a.predicted_days_until_stockout ?? 99) - (b.predicted_days_until_stockout ?? 99));
      setCriticalStockouts(validStockRisks);

      // Filter ward surge forecasts (occupancy >= 80% on t+1, t+7 or t+14)
      const surges = [];
      bedResults.forEach(item => {
        if (!item || !item.forecasts) return;
        const f1 = item.forecasts.t_plus_1;
        const f7 = item.forecasts.t_plus_7;
        const f14 = item.forecasts.t_plus_14;

        const maxRate = Math.max(
          f1?.predicted_occupancy_rate_pct || 0,
          f7?.predicted_occupancy_rate_pct || 0,
          f14?.predicted_occupancy_rate_pct || 0
        );

        if (maxRate >= 75) {
          surges.push({
            ...item,
            peak_rate: maxRate
          });
        }
      });

      surges.sort((a, b) => b.peak_rate - a.peak_rate);
      setWardSurgeAlerts(surges);

    } catch (err) {
      console.error("AI Aggregated fetch error:", err);
      setError("Unable to load aggregated AI insights.");
    } finally {
      setLoading(false);
    }
  };

  // Fetch drilldown facility inventory and wards when facility changes
  const fetchDrilldownFacility = async (cId) => {
    if (!cId) return;
    try {
      const [invRes, wardsRes] = await Promise.all([
        api.get(`/centres/${cId}/inventory`).catch(() => ({ data: [] })),
        api.get(`/centres/${cId}/wards`).catch(() => ({ data: [] }))
      ]);
      setSelectedFacilityData({
        inventory: invRes.data || [],
        wards: wardsRes.data || []
      });
    } catch (err) {
      console.error("Facility drilldown fetch error:", err);
    }
  };

  useEffect(() => {
    fetchAggregatedData();
  }, [centres.length]);

  useEffect(() => {
    if (selectedCentreId) {
      fetchDrilldownFacility(selectedCentreId);
    }
  }, [selectedCentreId]);

  const selectedCentreObj = centres.find(c => c.centre_id === Number(selectedCentreId));

  return (
    <div className="space-y-6">
      {/* Top Header & Tab Navigation */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 rounded-xl text-white shadow-md">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-extrabold text-slate-800">{title}</h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                  {isSuperAdmin ? 'State-Wide ML System' : 'District AI Radar'}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Machine learning early-warning for stockouts and multi-horizon bed surge forecasts across {centres.length} authorized health centres
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchAggregatedData}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Re-scan Insights
            </button>
          </div>
        </div>

        {/* Sub Navigation */}
        <div className="flex items-center gap-2 mt-4">
          <button
            onClick={() => setActiveSubTab('summary')}
            className={`px-4 py-2 text-xs font-bold rounded-lg transition ${
              activeSubTab === 'summary'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Regional Risk Radar & Summary
          </button>
          <button
            onClick={() => setActiveSubTab('facility_drilldown')}
            className={`px-4 py-2 text-xs font-bold rounded-lg transition ${
              activeSubTab === 'facility_drilldown'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Facility AI Drilldown Explorer
          </button>
        </div>
      </div>

      {/* VIEW A: SUMMARY & RISK RADAR */}
      {activeSubTab === 'summary' && (
        <div className="space-y-6">
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-pulse">
              <div className="h-72 bg-slate-100 rounded-xl border border-slate-200"></div>
              <div className="h-72 bg-slate-100 rounded-xl border border-slate-200"></div>
            </div>
          ) : error ? (
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-sm flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              <span>{error}</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Card 1: Critical Stockout Warnings */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-rose-100 text-rose-700 rounded-lg">
                      <AlertTriangle className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-800">Critical Stock-Out Warnings</h4>
                      <p className="text-[11px] text-slate-500">Medicines predicted to deplete within ≤14 days</p>
                    </div>
                  </div>
                  <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800">
                    {criticalStockouts.length} Alert{criticalStockouts.length === 1 ? '' : 's'}
                  </span>
                </div>

                {criticalStockouts.length === 0 ? (
                  <div className="text-center py-12 text-slate-500 text-xs flex-1 flex flex-col items-center justify-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
                    <ShieldCheck className="w-8 h-8 text-emerald-500 mb-2" />
                    No critical stockout risks detected across screened medicines.
                  </div>
                ) : (
                  <div className="space-y-2.5 overflow-y-auto max-h-96 pr-1">
                    {criticalStockouts.map((item, idx) => (
                      <div
                        key={`${item.centre_id}-${item.medicine_id}-${idx}`}
                        className="p-3.5 rounded-xl bg-gradient-to-r from-rose-50/70 via-white to-white border border-rose-200 flex items-center justify-between gap-3 text-xs hover:shadow-sm transition"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900">{item.medicine_name}</span>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              item.risk_level === 'CRITICAL' || item.risk_level === 'STOCK_OUT'
                                ? 'bg-rose-100 text-rose-700 border border-rose-300'
                                : 'bg-amber-100 text-amber-700 border border-amber-300'
                            }`}>
                              {item.risk_level}
                            </span>
                          </div>
                          <span className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                            <Building2 className="w-3 h-3 text-slate-400" />
                            {item.centre_name} ({item.centre_type})
                          </span>
                        </div>

                        <div className="text-right">
                          <span className="text-rose-600 font-extrabold text-sm block">
                            {item.predicted_days_until_stockout !== null
                              ? `${item.predicted_days_until_stockout} days left`
                              : 'Depleting Soon'}
                          </span>
                          <span className="text-[10px] text-slate-500">
                            Stock: {item.current_stock} / Min: {item.minimum_stock}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Card 2: Bed Surge & Capacity Warnings */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-purple-100 text-purple-700 rounded-lg">
                      <Bed className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-800">Bed Capacity & Surge Forecasts</h4>
                      <p className="text-[11px] text-slate-500">Wards projected to reach high utilization (≥75%)</p>
                    </div>
                  </div>
                  <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-purple-100 text-purple-800">
                    {wardSurgeAlerts.length} Ward{wardSurgeAlerts.length === 1 ? '' : 's'}
                  </span>
                </div>

                {wardSurgeAlerts.length === 0 ? (
                  <div className="text-center py-12 text-slate-500 text-xs flex-1 flex flex-col items-center justify-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
                    <ShieldCheck className="w-8 h-8 text-emerald-500 mb-2" />
                    All wards operating within safe capacity limits across all forecast horizons.
                  </div>
                ) : (
                  <div className="space-y-2.5 overflow-y-auto max-h-96 pr-1">
                    {wardSurgeAlerts.map((item, idx) => (
                      <div
                        key={`${item.centre_id}-${item.ward_id}-${idx}`}
                        className="p-3.5 rounded-xl bg-gradient-to-r from-purple-50/60 via-white to-white border border-purple-200 flex items-center justify-between gap-3 text-xs hover:shadow-sm transition"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900">{item.ward_name} Ward</span>
                            <span className="text-[11px] text-slate-500">({item.total_beds} beds total)</span>
                          </div>
                          <span className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                            <Building2 className="w-3 h-3 text-slate-400" />
                            {item.centre_name} ({item.centre_type})
                          </span>
                        </div>

                        <div className="text-right">
                          <div className="flex items-center gap-2">
                            <div className="text-right">
                              <span className="text-[10px] text-slate-400 block">7d Forecast</span>
                              <span className="font-bold text-purple-700 text-sm">
                                {item.forecasts?.t_plus_7?.predicted_occupancy_rate_pct}%
                              </span>
                            </div>
                            <div className="text-right pl-2 border-l border-slate-200">
                              <span className="text-[10px] text-slate-400 block">14d Forecast</span>
                              <span className="font-bold text-purple-900 text-sm">
                                {item.forecasts?.t_plus_14?.predicted_occupancy_rate_pct}%
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* VIEW B: FACILITY DRILLDOWN EXPLORER */}
      {activeSubTab === 'facility_drilldown' && (
        <div className="space-y-6">
          {/* Facility Selector Bar */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Building2 className="w-4 h-4 text-slate-500" />
              <label className="text-xs font-bold text-slate-700">Select Facility for AI Drilldown:</label>
            </div>

            <select
              value={selectedCentreId || ''}
              onChange={(e) => setSelectedCentreId(Number(e.target.value))}
              className="w-full sm:w-80 px-3 py-2 text-xs font-medium bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white"
            >
              {centres.map(c => (
                <option key={c.centre_id} value={c.centre_id}>
                  {c.centre_name} ({c.centre_type}) - District #{c.district_id}
                </option>
              ))}
            </select>
          </div>

          {selectedCentreObj && (
            <div className="space-y-6">
              {/* Detailed Stockout Prediction for Selected Facility */}
              <AiStockoutPredictionSection
                centreId={selectedCentreObj.centre_id}
                inventory={selectedFacilityData.inventory}
                medicines={medicinesList}
                title={`AI Stock-Out Predictions — ${selectedCentreObj.centre_name}`}
              />

              {/* Detailed Bed Forecast for Selected Facility */}
              <AiBedForecastSection
                centreId={selectedCentreObj.centre_id}
                wards={selectedFacilityData.wards}
                title={`AI Bed Occupancy Forecasting — ${selectedCentreObj.centre_name}`}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AiAggregatedInsightsSection;
