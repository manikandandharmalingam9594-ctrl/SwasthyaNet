import React, { useState, useEffect } from 'react';
import api from '../services/api';
import {
  Sparkles,
  AlertTriangle,
  ShieldCheck,
  Clock,
  Package,
  TrendingDown,
  RefreshCw,
  Search,
  Filter
} from 'lucide-react';

const AiStockoutPredictionSection = ({ centreId, inventory = [], medicines = [], title = "AI Medicine Stock-Out Predictions" }) => {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [riskFilter, setRiskFilter] = useState('ALL'); // 'ALL' | 'CRITICAL' | 'HIGH' | 'LOW'
  const [searchTerm, setSearchTerm] = useState('');

  // Map medicine_id to Medicine details
  const medMap = {};
  medicines.forEach(m => {
    medMap[m.medicine_id] = m;
  });

  const fetchStockoutPredictions = async () => {
    if (!centreId) return;
    try {
      setLoading(true);
      setError(null);

      // Determine medicine IDs from inventory or default top medicines
      const medIdsToFetch = inventory.length > 0
        ? inventory.map(item => item.medicine_id)
        : medicines.map(m => m.medicine_id);

      if (medIdsToFetch.length === 0) {
        setPredictions([]);
        setLoading(false);
        return;
      }

      // Fetch predictions concurrently for all medicines in this centre
      const results = await Promise.allSettled(
        medIdsToFetch.map(medId => api.get(`/ai/stockout/${centreId}/${medId}`))
      );

      const validPreds = [];
      results.forEach((res, idx) => {
        if (res.status === 'fulfilled' && res.value.data) {
          validPreds.push(res.value.data);
        } else {
          // Fallback if individual endpoint fails
          const medId = medIdsToFetch[idx];
          const m = medMap[medId];
          const invItem = inventory.find(i => i.medicine_id === medId);
          if (m && invItem) {
            validPreds.push({
              centre_id: centreId,
              medicine_id: medId,
              medicine_name: m.medicine_name,
              medicine_category: m.category,
              current_stock: invItem.current_stock,
              minimum_stock: invItem.minimum_stock,
              predicted_days_until_stockout: null,
              risk_level: 'UNAVAILABLE',
              estimated_daily_consumption: null
            });
          }
        }
      });

      // Sort by urgency: CRITICAL first, then HIGH, then MEDIUM, then LOW
      const riskOrder = { 'STOCK_OUT': 0, 'CRITICAL': 1, 'HIGH': 2, 'MEDIUM': 3, 'LOW': 4, 'UNAVAILABLE': 5 };
      validPreds.sort((a, b) => {
        const orderA = riskOrder[a.risk_level] ?? 99;
        const orderB = riskOrder[b.risk_level] ?? 99;
        if (orderA !== orderB) return orderA - orderB;
        return (a.predicted_days_until_stockout ?? 999) - (b.predicted_days_until_stockout ?? 999);
      });

      setPredictions(validPreds);
    } catch (err) {
      console.error("AI Stockout fetch error:", err);
      setError("Unable to generate AI stock-out predictions. Please check network connection.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStockoutPredictions();
  }, [centreId, inventory.length, medicines.length]);

  const filteredPredictions = predictions.filter(item => {
    const matchesSearch = (item.medicine_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                          (item.medicine_category || '').toLowerCase().includes(searchTerm.toLowerCase());
    if (!matchesSearch) return false;

    if (riskFilter === 'ALL') return true;
    if (riskFilter === 'CRITICAL') return item.risk_level === 'CRITICAL' || item.risk_level === 'STOCK_OUT';
    if (riskFilter === 'HIGH') return item.risk_level === 'HIGH';
    if (riskFilter === 'LOW') return item.risk_level === 'LOW' || item.risk_level === 'SAFE';
    return true;
  });

  const getRiskBadge = (level, days) => {
    switch (level) {
      case 'STOCK_OUT':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-red-600 text-white shadow-sm animate-pulse">
            <AlertTriangle className="w-3.5 h-3.5" /> Depleted (0 Days)
          </span>
        );
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-600" /> Critical ({days}d)
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
            <Clock className="w-3.5 h-3.5 text-amber-600" /> High Risk ({days}d)
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800 border border-yellow-300">
            <Clock className="w-3.5 h-3.5 text-yellow-600" /> Medium ({days}d)
          </span>
        );
      case 'LOW':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Safe Buffer (60+d)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
            No prediction available
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-gradient-to-tr from-indigo-600 to-violet-600 rounded-lg text-white shadow-sm">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-800">{title}</h3>
              <p className="text-xs text-slate-500">
                Predictive early warning based on daily consumption trends and replenishment dynamics
              </p>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={fetchStockoutPredictions}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
            title="Refresh AI Predictions"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Filters & Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 my-4">
        {/* Risk Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          <span className="text-xs font-semibold text-slate-500 mr-1 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" /> Risk:
          </span>
          {['ALL', 'CRITICAL', 'HIGH', 'LOW'].map(f => (
            <button
              key={f}
              onClick={() => setRiskFilter(f)}
              className={`px-3 py-1 text-xs font-medium rounded-full transition ${
                riskFilter === f
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {f === 'ALL' ? 'All Medicines' : f.charAt(0) + f.slice(1).toLowerCase()}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search medicine name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white"
          />
        </div>
      </div>

      {/* Loading Skeleton */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="h-32 bg-slate-100 rounded-xl border border-slate-200"></div>
          ))}
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      ) : filteredPredictions.length === 0 ? (
        <div className="text-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-slate-500 text-sm">
          <Package className="w-8 h-8 mx-auto text-slate-400 mb-2" />
          No medicine predictions matching the current filter.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPredictions.map((pred) => {
            const isDanger = pred.risk_level === 'CRITICAL' || pred.risk_level === 'STOCK_OUT';
            const isWarning = pred.risk_level === 'HIGH';

            return (
              <div
                key={pred.medicine_id}
                className={`p-4 rounded-xl border transition hover:shadow-md ${
                  isDanger
                    ? 'bg-gradient-to-b from-rose-50/70 to-white border-rose-200 shadow-rose-100/50'
                    : isWarning
                    ? 'bg-gradient-to-b from-amber-50/70 to-white border-amber-200'
                    : 'bg-white border-slate-200 hover:border-slate-300'
                }`}
              >
                {/* Top Row: Name & Risk Badge */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm">
                      {pred.medicine_name || `Medicine #${pred.medicine_id}`}
                    </h4>
                    <span className="text-[11px] text-slate-500 font-medium">
                      {pred.medicine_category || 'General Medicine'}
                    </span>
                  </div>
                  {getRiskBadge(pred.risk_level, pred.predicted_days_until_stockout)}
                </div>

                {/* Stock Details */}
                <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-slate-100 text-xs">
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase font-semibold">Current Stock</span>
                    <span className="font-bold text-slate-800 text-sm">
                      {pred.current_stock ?? '—'} <span className="text-[10px] font-normal text-slate-500">units</span>
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase font-semibold">Safety Buffer</span>
                    <span className="font-medium text-slate-700">
                      {pred.minimum_stock ?? '—'} <span className="text-[10px] text-slate-400">min</span>
                    </span>
                  </div>
                </div>

                {/* Forecast Metric */}
                <div className="mt-3 pt-2.5 bg-slate-50/80 rounded-lg p-2.5 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5 text-slate-600">
                    <TrendingDown className="w-3.5 h-3.5 text-slate-400" />
                    <span>Est. Depletion:</span>
                  </div>
                  <span className={`font-bold ${
                    isDanger ? 'text-rose-600 text-sm' : isWarning ? 'text-amber-600 text-sm' : 'text-slate-700'
                  }`}>
                    {pred.predicted_days_until_stockout !== null && pred.predicted_days_until_stockout !== undefined
                      ? pred.predicted_days_until_stockout >= 60
                        ? '60+ days (Safe)'
                        : `${pred.predicted_days_until_stockout} days`
                      : 'No prediction available'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default AiStockoutPredictionSection;
