import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import UserManager from '../components/UserManager';
import DistrictMap from '../components/DistrictMap';
import AiAggregatedInsightsSection from '../components/AiAggregatedInsightsSection';
import { 
  Building2, 
  Bed, 
  AlertTriangle, 
  Package, 
  Activity, 
  LogOut, 
  MapPin, 
  Stethoscope, 
  Users, 
  Map, 
  ShieldAlert, 
  Search, 
  Filter, 
  ChevronRight,
  Hospital,
  LayoutDashboard,
  UserCheck,
  Sparkles
} from 'lucide-react';

const SuperAdminDashboard = () => {
  const { user, logoutUser } = useContext(AuthContext);
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'users'
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const [metrics, setMetrics] = useState({
    totalDistricts: 0,
    totalCentres: 0,
    phcCount: 0,
    chcCount: 0,
    totalDoctors: 0,
    totalMedicines: 0,
    activeAlerts: 0,
    bedOccupancy: 0
  });

  const [centres, setCentres] = useState([]);
  const [districtsMap, setDistrictsMap] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');

  const handleLogout = () => {
    logoutUser();
    navigate('/login');
  };

  useEffect(() => {
    const fetchSuperAdminData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // 1. Fetch system-wide core entities in parallel
        const [
          districtsRes, 
          centresRes, 
          healthScoresRes, 
          alertsRes, 
          medicinesRes
        ] = await Promise.all([
          api.get('/districts'),
          api.get('/centres'),
          api.get('/health-scores'),
          api.get('/alerts'),
          api.get('/medicines')
        ]);

        const districtsData = districtsRes.data || [];
        const centresData = centresRes.data || [];
        const healthScoresData = healthScoresRes.data || [];
        const alertsData = alertsRes.data || [];
        const medicinesData = medicinesRes.data || [];

        // Build district ID to Name map
        const dMap = {};
        districtsData.forEach(d => {
          dMap[d.district_id] = d.district_name;
        });
        setDistrictsMap(dMap);

        // Calculate counts
        const phcs = centresData.filter(c => c.centre_type === 'PHC');
        const chcs = centresData.filter(c => c.centre_type === 'CHC');
        const activeAlertsList = alertsData.filter(
          a => a.status !== 'RESOLVED' && a.status !== 'Resolved'
        );

        // 2. Fetch doctors and beds for all centres concurrently
        const doctorsPromises = centresData.map(c => 
          api.get(`/centres/${c.centre_id}/doctors`).catch(() => ({ data: [] }))
        );
        const bedsPromises = centresData.map(c => 
          api.get(`/centres/${c.centre_id}/beds`).catch(() => ({ data: [] }))
        );

        const doctorsResponses = await Promise.all(doctorsPromises);
        const bedsResponses = await Promise.all(bedsPromises);

        let totalDoctorsCount = 0;
        doctorsResponses.forEach(res => {
          totalDoctorsCount += (res.data || []).length;
        });

        let totalOccupiedBeds = 0;
        let totalAvailableBeds = 0;
        bedsResponses.forEach(res => {
          (res.data || []).forEach(ward => {
            totalOccupiedBeds += (ward.occupied_beds || 0);
            totalAvailableBeds += (ward.available_beds || 0);
          });
        });

        const totalBedsActual = totalOccupiedBeds + totalAvailableBeds;
        const bedOccupancyRate = totalBedsActual > 0 
          ? Math.round((totalOccupiedBeds / totalBedsActual) * 100) 
          : 0;

        // 3. Map health scores to centres
        const mappedCentres = centresData.map(c => {
          const scoreObj = healthScoresData.find(s => s.centre_id === c.centre_id);
          return {
            ...c,
            districtName: dMap[c.district_id] || `District ${c.district_id}`,
            healthScore: scoreObj ? scoreObj.score : 'N/A'
          };
        });

        setCentres(mappedCentres);
        setMetrics({
          totalDistricts: districtsData.length,
          totalCentres: centresData.length,
          phcCount: phcs.length,
          chcCount: chcs.length,
          totalDoctors: totalDoctorsCount,
          totalMedicines: medicinesData.length,
          activeAlerts: activeAlertsList.length,
          bedOccupancy: bedOccupancyRate
        });

      } catch (err) {
        console.error('Error fetching Super Admin dashboard data:', err);
        setError('Failed to load system-wide dashboard data. Please verify your connection.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSuperAdminData();
  }, []);

  const filteredCentres = centres.filter(centre => {
    const matchesSearch = 
      centre.centre_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      centre.districtName?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (centre.block && centre.block.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesType = 
      typeFilter === 'ALL' || 
      centre.centre_type === typeFilter;

    return matchesSearch && matchesType;
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600 mb-4"></div>
        <p className="text-slate-600 font-medium">Loading System-Wide Dashboard...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 pb-12">
      {/* Navbar */}
      <nav className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="bg-indigo-600 text-white p-2 rounded-lg">
                <ShieldAlert className="h-6 w-6" />
              </div>
              <div>
                <span className="font-bold text-xl text-slate-800">SwasthyaNet</span>
                <span className="ml-2 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-800">
                  Super Admin
                </span>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-slate-600 hidden sm:inline">{user?.email}</span>
              <button 
                onClick={handleLogout}
                className="inline-flex items-center px-3 py-2 border border-slate-300 text-sm leading-4 font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded-md shadow-sm">
            <div className="flex">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-5 w-5 text-red-500" />
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700 font-medium">{error}</p>
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
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <LayoutDashboard className="h-4 w-4 mr-2" />
            Overview & Analytics
          </button>
          <button
            onClick={() => setActiveTab('ai_insights')}
            className={`inline-flex items-center px-4 py-2 text-sm font-semibold rounded-lg transition ${
              activeTab === 'ai_insights'
                ? 'bg-purple-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <Sparkles className="h-4 w-4 mr-2 text-purple-400" />
            System AI Insights & Forecasting
          </button>
          <button
            onClick={() => setActiveTab('users')}
            className={`inline-flex items-center px-4 py-2 text-sm font-semibold rounded-lg transition ${
              activeTab === 'users'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <UserCheck className="h-4 w-4 mr-2" />
            User Management
          </button>
        </div>

        {activeTab === 'users' ? (
          <UserManager />
        ) : activeTab === 'ai_insights' ? (
          <AiAggregatedInsightsSection
            centres={centres}
            title="State-Wide AI Healthcare Intelligence & Predictive Forecasting"
            isSuperAdmin={true}
          />
        ) : (
          <>
            {/* Dashboard Title & Overview */}
            <div className="mb-8">
              <h1 className="text-2xl font-bold text-slate-900">System Overview</h1>
              <p className="text-sm text-slate-500 mt-1">
                Real-time aggregate operational intelligence across all districts and healthcare facilities.
              </p>
            </div>

        {/* Metric Cards Grid - 8 Cards */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          
          {/* Total Districts */}
          <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5 hover:shadow-md transition">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-blue-100 rounded-lg p-3">
                <Map className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Districts</dt>
                  <dd className="text-2xl font-bold text-slate-900 mt-1">{metrics.totalDistricts}</dd>
                </dl>
              </div>
            </div>
          </div>

          {/* Total Health Centres */}
          <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5 hover:shadow-md transition">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-indigo-100 rounded-lg p-3">
                <Hospital className="h-6 w-6 text-indigo-600" />
              </div>
              <div className="ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Centres</dt>
                  <dd className="text-2xl font-bold text-slate-900 mt-1">{metrics.totalCentres}</dd>
                </dl>
              </div>
            </div>
          </div>

          {/* PHC Count */}
          <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5 hover:shadow-md transition">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-emerald-100 rounded-lg p-3">
                <Building2 className="h-6 w-6 text-emerald-600" />
              </div>
              <div className="ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs font-semibold text-slate-500 uppercase tracking-wider">PHC Count</dt>
                  <dd className="text-2xl font-bold text-slate-900 mt-1">{metrics.phcCount}</dd>
                </dl>
              </div>
            </div>
          </div>

          {/* CHC Count */}
          <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5 hover:shadow-md transition">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-purple-100 rounded-lg p-3">
                <Building2 className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs font-semibold text-slate-500 uppercase tracking-wider">CHC Count</dt>
                  <dd className="text-2xl font-bold text-slate-900 mt-1">{metrics.chcCount}</dd>
                </dl>
              </div>
            </div>
          </div>

          {/* Total Doctors */}
          <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5 hover:shadow-md transition">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-cyan-100 rounded-lg p-3">
                <Users className="h-6 w-6 text-cyan-600" />
              </div>
              <div className="ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Doctors</dt>
                  <dd className="text-2xl font-bold text-slate-900 mt-1">{metrics.totalDoctors}</dd>
                </dl>
              </div>
            </div>
          </div>

          {/* Total Medicines */}
          <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5 hover:shadow-md transition">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-amber-100 rounded-lg p-3">
                <Package className="h-6 w-6 text-amber-600" />
              </div>
              <div className="ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Medicines</dt>
                  <dd className="text-2xl font-bold text-slate-900 mt-1">{metrics.totalMedicines}</dd>
                </dl>
              </div>
            </div>
          </div>

          {/* Active Alerts */}
          <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5 hover:shadow-md transition">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-rose-100 rounded-lg p-3">
                <AlertTriangle className="h-6 w-6 text-rose-600" />
              </div>
              <div className="ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Alerts</dt>
                  <dd className="text-2xl font-bold text-slate-900 mt-1">{metrics.activeAlerts}</dd>
                </dl>
              </div>
            </div>
          </div>

          {/* Overall Bed Occupancy */}
          <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5 hover:shadow-md transition">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-teal-100 rounded-lg p-3">
                <Bed className="h-6 w-6 text-teal-600" />
              </div>
              <div className="ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Bed Occupancy</dt>
                  <dd className="text-2xl font-bold text-slate-900 mt-1">{metrics.bedOccupancy}%</dd>
                </dl>
              </div>
            </div>
          </div>

        </div>

        {/* State-Wide Facilities Map */}
        <DistrictMap 
          centres={centres} 
          title="State-Wide Healthcare Facilities (PHCs & CHCs) Map" 
          height="440px" 
        />

        {/* System-wide Centres Table Section */}
        <div className="bg-white shadow-sm rounded-xl border border-slate-200 overflow-hidden">
          
          {/* Table Header & Controls */}
          <div className="p-5 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center">
                <Hospital className="h-5 w-5 mr-2 text-indigo-600" />
                System-Wide Health Centres ({filteredCentres.length})
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">Click any centre row to open the detailed centre dashboard.</p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {/* Search Bar */}
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input 
                  type="text" 
                  placeholder="Search centre or district..." 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 pr-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 w-56 sm:w-64"
                />
              </div>

              {/* Type Filter */}
              <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-lg">
                <button 
                  onClick={() => setTypeFilter('ALL')}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition ${
                    typeFilter === 'ALL' 
                      ? 'bg-white text-indigo-700 shadow-sm' 
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  All
                </button>
                <button 
                  onClick={() => setTypeFilter('PHC')}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition ${
                    typeFilter === 'PHC' 
                      ? 'bg-white text-emerald-700 shadow-sm' 
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  PHC
                </button>
                <button 
                  onClick={() => setTypeFilter('CHC')}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition ${
                    typeFilter === 'CHC' 
                      ? 'bg-white text-purple-700 shadow-sm' 
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  CHC
                </button>
              </div>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th scope="col" className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Centre Name
                  </th>
                  <th scope="col" className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th scope="col" className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    District
                  </th>
                  <th scope="col" className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Health Score
                  </th>
                  <th scope="col" className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3.5 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {filteredCentres.map((centre) => (
                  <tr 
                    key={centre.centre_id} 
                    onClick={() => navigate(`/centres/${centre.centre_id}`)}
                    className="hover:bg-indigo-50/50 transition cursor-pointer group"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className={`flex-shrink-0 h-10 w-10 rounded-lg flex items-center justify-center ${
                          centre.centre_type === 'CHC' ? 'bg-purple-100 text-purple-600' : 'bg-emerald-100 text-emerald-600'
                        }`}>
                          <Stethoscope className="h-5 w-5" />
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-semibold text-slate-900 group-hover:text-indigo-600 transition">
                            {centre.centre_name}
                          </div>
                          <div className="text-xs text-slate-500">
                            ID: #{centre.centre_id} {centre.block ? `• ${centre.block}` : ''}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2.5 py-1 inline-flex text-xs leading-4 font-semibold rounded-full ${
                        centre.centre_type === 'CHC' 
                          ? 'bg-purple-100 text-purple-800' 
                          : 'bg-emerald-100 text-emerald-800'
                      }`}>
                        {centre.centre_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-slate-700 font-medium">
                        <MapPin className="h-4 w-4 text-slate-400 mr-1.5 flex-shrink-0" />
                        {centre.districtName}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-bold">
                        {centre.healthScore !== 'N/A' ? (
                          <span className={
                            centre.healthScore >= 80 
                              ? 'text-emerald-600' 
                              : centre.healthScore >= 50 
                                ? 'text-amber-500' 
                                : 'text-rose-600'
                          }>
                            {centre.healthScore}/100
                          </span>
                        ) : (
                          <span className="text-slate-400 font-normal">N/A</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2.5 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        centre.status?.toLowerCase() === 'active' || centre.status?.toLowerCase() === 'operational'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                          : 'bg-rose-50 text-rose-700 border border-rose-200'
                      }`}>
                        {centre.status || 'Active'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <span className="text-indigo-600 group-hover:text-indigo-800 inline-flex items-center text-xs font-semibold">
                        View Details
                        <ChevronRight className="h-4 w-4 ml-0.5 group-hover:translate-x-0.5 transition-transform" />
                      </span>
                    </td>
                  </tr>
                ))}

                {filteredCentres.length === 0 && (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center text-sm text-slate-500">
                      <div className="flex flex-col items-center">
                        <Building2 className="h-8 w-8 text-slate-300 mb-2" />
                        <p className="font-medium text-slate-600">No health centres match the selected filters.</p>
                      </div>
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

export default SuperAdminDashboard;
