import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import DistrictMap from '../components/DistrictMap';
import UserManager from '../components/UserManager';
import AiAggregatedInsightsSection from '../components/AiAggregatedInsightsSection';
import { 
  Building2, 
  Bed, 
  AlertTriangle, 
  PackageMinus,
  Activity, 
  LogOut, 
  MapPin, 
  Stethoscope,
  LayoutDashboard,
  UserCheck,
  Sparkles
} from 'lucide-react';

const DistrictAdminDashboard = () => {
  const { user, logoutUser } = useContext(AuthContext);
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'staff'
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const [metrics, setMetrics] = useState({
    totalCentres: 0,
    totalBeds: 0,
    occupancyRate: 0,
    openAlerts: 0,
    lowStock: 0
  });

  const [centres, setCentres] = useState([]);

  const handleLogout = () => {
    logoutUser();
    navigate('/login');
  };

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // 1. Fetch all centres and filter by user's district_id
        const centresRes = await api.get('/centres');
        const districtCentres = centresRes.data.filter(c => c.district_id === user.district_id);
        
        // 2. Fetch global alerts and health scores
        const [alertsRes, scoresRes] = await Promise.all([
          api.get('/alerts'),
          api.get('/health-scores')
        ]);

        const districtAlerts = alertsRes.data.filter(a => 
          districtCentres.some(c => c.centre_id === a.centre_id) && 
          (a.status !== 'RESOLVED' && a.status !== 'Resolved')
        );

        // 3. Fetch beds and inventory for each centre
        const bedPromises = districtCentres.map(c => api.get(`/centres/${c.centre_id}/beds`));
        const invPromises = districtCentres.map(c => api.get(`/centres/${c.centre_id}/inventory`));
        
        const bedsResponses = await Promise.all(bedPromises);
        const invResponses = await Promise.all(invPromises);

        let totalOccupied = 0;
        let totalAvailable = 0;
        
        bedsResponses.forEach(res => {
          res.data.forEach(ward => {
            totalOccupied += ward.occupied_beds || 0;
            totalAvailable += ward.available_beds || 0;
          });
        });

        const totalBedsActual = totalOccupied + totalAvailable;
        const occupancyRate = totalBedsActual > 0 
          ? Math.round((totalOccupied / totalBedsActual) * 100) 
          : 0;

        let lowStockCount = 0;
        invResponses.forEach(res => {
          res.data.forEach(item => {
            if (item.current_stock < (item.minimum_stock || 50)) {
              lowStockCount++;
            }
          });
        });

        // 4. Map health scores to centres
        const mappedCentres = districtCentres.map(c => {
          const scoreObj = scoresRes.data.find(s => s.centre_id === c.centre_id);
          return {
            ...c,
            healthScore: scoreObj ? scoreObj.score : 'N/A'
          };
        });

        setCentres(mappedCentres);
        setMetrics({
          totalCentres: districtCentres.length,
          totalBeds: districtCentres.reduce((sum, c) => sum + (c.total_beds || 0), 0),
          occupancyRate,
          openAlerts: districtAlerts.length,
          lowStock: lowStockCount
        });

      } catch (err) {
        console.error("Error fetching dashboard data:", err);
        setError("Failed to load dashboard data. Please try again later.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [user]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navbar */}
      <nav className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-blue-600 mr-2" />
              <span className="font-bold text-xl text-slate-800">SwasthyaNet | District Admin</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-slate-600">{user?.email}</span>
              <button 
                onClick={handleLogout}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-slate-700 bg-slate-100 hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-5 w-5 text-red-500" />
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex items-center space-x-3 mb-6 border-b border-slate-200 pb-3">
          <button
            onClick={() => setActiveTab('overview')}
            className={`inline-flex items-center px-4 py-2 text-sm font-semibold rounded-lg transition ${
              activeTab === 'overview'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <LayoutDashboard className="h-4 w-4 mr-2" />
            District Overview & Map
          </button>
          <button
            onClick={() => setActiveTab('ai_insights')}
            className={`inline-flex items-center px-4 py-2 text-sm font-semibold rounded-lg transition ${
              activeTab === 'ai_insights'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <Sparkles className="h-4 w-4 mr-2 text-indigo-400" />
            District AI Insights & Forecasts
          </button>
          <button
            onClick={() => setActiveTab('staff')}
            className={`inline-flex items-center px-4 py-2 text-sm font-semibold rounded-lg transition ${
              activeTab === 'staff'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <UserCheck className="h-4 w-4 mr-2" />
            Staff Management
          </button>
        </div>

        {activeTab === 'staff' ? (
          <UserManager />
        ) : activeTab === 'ai_insights' ? (
          <AiAggregatedInsightsSection 
            centres={centres} 
            title="District AI Predictive Intelligence & Forecasting"
            isSuperAdmin={false}
          />
        ) : (
          <>
            {/* Top Metrics */}
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5 mb-8">
              <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5 transition hover:shadow-md">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-blue-100 rounded-md p-3">
                <Building2 className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-slate-500 truncate">Total Centres</dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-bold text-slate-900">{metrics.totalCentres}</div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5 transition hover:shadow-md">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-teal-100 rounded-md p-3">
                <Bed className="h-6 w-6 text-teal-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-slate-500 truncate">Total Beds</dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-bold text-slate-900">{metrics.totalBeds}</div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5 transition hover:shadow-md">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-indigo-100 rounded-md p-3">
                <Activity className="h-6 w-6 text-indigo-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-slate-500 truncate">Bed Occupancy</dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-bold text-slate-900">{metrics.occupancyRate}%</div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5 transition hover:shadow-md">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-red-100 rounded-md p-3">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-slate-500 truncate">Open Alerts</dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-bold text-slate-900">{metrics.openAlerts}</div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5 transition hover:shadow-md">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-orange-100 rounded-md p-3">
                <PackageMinus className="h-6 w-6 text-orange-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-slate-500 truncate">Low Stock Meds</dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-bold text-slate-900">{metrics.lowStock}</div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Interactive Map */}
        <DistrictMap 
          centres={centres} 
          title="District Healthcare Network (PHCs & CHCs) Map" 
          height="400px" 
        />

        {/* Centre List Table */}
        <div className="bg-white shadow-sm rounded-xl border border-slate-200 overflow-hidden">
          <div className="px-6 py-5 border-b border-slate-200 flex justify-between items-center">
            <h3 className="text-lg leading-6 font-medium text-slate-900 flex items-center">
              <Building2 className="h-5 w-5 mr-2 text-slate-500" />
              District Health Centres
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Centre
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Location
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Health Score
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {centres.map((centre) => (
                  <tr 
                    key={centre.centre_id} 
                    className="hover:bg-slate-100 transition cursor-pointer"
                    onClick={() => navigate(`/centres/${centre.centre_id}`)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <Stethoscope className="h-5 w-5 text-blue-600" />
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-slate-900">{centre.centre_name}</div>
                          <div className="text-sm text-slate-500">ID: {centre.centre_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-slate-100 text-slate-800">
                        {centre.centre_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-slate-900">
                        <MapPin className="h-4 w-4 text-slate-400 mr-1" />
                        {centre.block || centre.village_town || 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-slate-900 font-medium">
                        {centre.healthScore !== 'N/A' ? (
                          <span className={centre.healthScore >= 80 ? 'text-green-600' : centre.healthScore >= 50 ? 'text-orange-500' : 'text-red-600'}>
                            {centre.healthScore}/100
                          </span>
                        ) : (
                          <span className="text-slate-400">N/A</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        centre.status?.toLowerCase() === 'active' || centre.status?.toLowerCase() === 'operational' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {centre.status || 'Unknown'}
                      </span>
                    </td>
                  </tr>
                ))}
                
                {centres.length === 0 && (
                  <tr>
                    <td colSpan="5" className="px-6 py-8 text-center text-sm text-slate-500">
                      No health centres found in this district.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </>
    )}
  </main>
</div>
);
};

export default DistrictAdminDashboard;
