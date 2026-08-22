import React, { useEffect, useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import DistrictMap from '../components/DistrictMap';
import VoiceInventoryIntake from '../components/VoiceInventoryIntake';
import AiStockoutPredictionSection from '../components/AiStockoutPredictionSection';
import AiBedForecastSection from '../components/AiBedForecastSection';
import {
  Activity,
  Bed,
  Package,
  Users,
  AlertTriangle,
  Building2,
  CalendarCheck,
  LogOut,
  Save,
  CheckCircle2,
  Stethoscope,
  TrendingUp,
  MapPin
} from 'lucide-react';

const ChcDashboard = () => {
  const { user, logoutUser } = useContext(AuthContext);
  const navigate = useNavigate();

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState('');

  const [data, setData] = useState({
    centre: null,
    score: null,
    inventory: [],
    medicines: [],
    wards: [],
    beds: [],
    doctors: [],
    attendance: [],
    alerts: []
  });

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const centreId = user?.centre_id;

      if (!centreId) {
        throw new Error('No centre assigned to this account.');
      }

      const [
        centreRes,
        scoreRes,
        invRes,
        medsRes,
        wardsRes,
        bedsRes,
        docsRes,
        attRes,
        alertsRes
      ] = await Promise.all([
        api.get(`/centres/${centreId}`),
        api.get(`/centres/${centreId}/health-score`),
        api.get(`/centres/${centreId}/inventory`),
        api.get('/medicines'),
        api.get(`/centres/${centreId}/wards`),
        api.get(`/centres/${centreId}/beds`),
        api.get(`/centres/${centreId}/doctors`),
        api.get(`/centres/${centreId}/attendance`),
        api.get(`/centres/${centreId}/alerts`)
      ]);

      setData({
        centre: centreRes.data,
        score: scoreRes.data[0] || null,
        inventory: invRes.data,
        medicines: medsRes.data,
        wards: wardsRes.data,
        beds: bedsRes.data,
        doctors: docsRes.data,
        attendance: attRes.data,
        alerts: alertsRes.data
      });
    } catch (err) {
      console.error(err);
      if (err.response?.status === 403) {
        setError('You do not have permission to view this centre\'s data.');
      } else {
        setError('Failed to load dashboard. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (user?.centre_id) {
      fetchData();
    } else {
      setError('Your account does not have a designated Health Centre. Please contact your Administrator.');
      setIsLoading(false);
    }
  }, [user]);

  const showSuccess = (msg) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(''), 3500);
  };

  const handleUpdateInventory = async (inventory_id, qty, type) => {
    try {
      await api.put(`/inventory/${inventory_id}`, {
        quantity: parseInt(qty),
        transaction_type: type
      });
      showSuccess('Inventory updated successfully!');
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update inventory.');
    }
  };

  const handleUpdateBeds = async (ward_id, occupied_beds, total_beds) => {
    const occ = parseInt(occupied_beds);
    if (occ < 0 || occ > total_beds) {
      alert(`Occupied beds must be between 0 and ${total_beds}.`);
      return;
    }
    try {
      await api.put(`/wards/${ward_id}/occupancy`, {
        occupied_beds: occ,
        recorded_at: new Date().toISOString()
      });
      showSuccess('Bed occupancy updated successfully!');
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update bed occupancy.');
    }
  };

  const handleUpdateAttendance = async (doctor_id, status) => {
    try {
      await api.post(`/attendance`, {
        doctor_id: parseInt(doctor_id),
        attendance_date: new Date().toISOString().split('T')[0],
        status: status
      });
      showSuccess('Attendance recorded successfully!');
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to record attendance.');
    }
  };

  const handleLogout = () => {
    logoutUser();
    navigate('/login');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-600 mb-4"></div>
        <p className="text-slate-600 font-medium">Loading CHC Dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 p-8">
        <div className="max-w-4xl mx-auto bg-red-50 border border-red-200 p-6 rounded-xl shadow-sm">
          <div className="flex items-start">
            <AlertTriangle className="h-8 w-8 text-red-500 mr-4 flex-shrink-0 mt-0.5" />
            <div>
              <h2 className="text-xl font-bold text-red-700">Access Error</h2>
              <p className="text-red-600 mt-1">{error}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="mt-6 px-4 py-2 bg-white border border-red-300 text-red-700 rounded-md hover:bg-red-50 text-sm font-medium"
          >
            Logout
          </button>
        </div>
      </div>
    );
  }

  const { centre, score, inventory, medicines, wards, beds, doctors, attendance, alerts } = data;

  const getMedicineName = (medicineId) => {
    const med = medicines?.find(m => m.medicine_id === medicineId);
    return med ? med.medicine_name : `Medicine #${medicineId}`;
  };

  const activeAlerts = alerts.filter(a => a.status !== 'RESOLVED' && a.status !== 'Resolved');
  const todayStr = new Date().toISOString().split('T')[0];

  const totalOccupied = wards.reduce((sum, w) => {
    const b = beds.find(x => x.ward_id === w.ward_id);
    return sum + (b ? (b.occupied_beds || 0) : 0);
  }, 0);
  const totalCapacity = wards.reduce((sum, w) => sum + (w.total_beds || 0), 0);
  const occupancyPct = totalCapacity > 0 ? Math.round((totalOccupied / totalCapacity) * 100) : 0;

  const lowStockCount = inventory.filter(i => i.current_stock < (i.minimum_stock || 50)).length;

  return (
    <div className="min-h-screen bg-slate-50 pb-12">
      {/* Success Toast */}
      {successMsg && (
        <div className="fixed top-4 right-4 bg-green-100 border border-green-400 text-green-800 px-4 py-3 rounded-lg flex items-center shadow-lg z-50 animate-pulse">
          <CheckCircle2 className="h-5 w-5 mr-2 text-green-600" />
          <span className="font-medium text-sm">{successMsg}</span>
        </div>
      )}

      {/* Navbar */}
      <nav className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Stethoscope className="h-7 w-7 text-purple-600 mr-2" />
              <span className="font-bold text-xl text-slate-800">SwasthyaNet | CHC Staff</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-slate-500 hidden sm:block">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="inline-flex items-center px-3 py-2 border border-slate-200 text-sm font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 transition"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Centre Header */}
      <div className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="flex items-center">
              <div className="bg-purple-100 p-3 rounded-lg mr-4 flex-shrink-0">
                <Building2 className="h-8 w-8 text-purple-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">{centre.centre_name}</h1>
                <p className="text-slate-500 text-sm mt-0.5">
                  {centre.centre_type} &bull; {centre.block || centre.village_town || 'Location N/A'}
                </p>
              </div>
            </div>
            <div className="flex gap-4 flex-wrap">
              <div className="flex items-center bg-slate-50 border border-slate-200 px-4 py-2 rounded-lg">
                <Activity className="h-5 w-5 text-slate-400 mr-2" />
                <span className="text-sm font-medium text-slate-600 mr-2">Health Score:</span>
                {score ? (
                  <span className={`text-xl font-bold ${score.score > 80 ? 'text-green-600' : score.score >= 50 ? 'text-orange-500' : 'text-red-600'}`}>
                    {score.score}/100
                  </span>
                ) : (
                  <span className="text-xl font-bold text-slate-400">N/A</span>
                )}
              </div>
            </div>
          </div>

          {/* Quick stats */}
          <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-purple-50 border border-purple-100 rounded-lg p-3 flex items-center">
              <Bed className="h-6 w-6 text-purple-500 mr-3 flex-shrink-0" />
              <div>
                <p className="text-xs text-slate-500">Bed Occupancy</p>
                <p className="text-lg font-bold text-slate-800">{occupancyPct}%</p>
              </div>
            </div>
            <div className="bg-orange-50 border border-orange-100 rounded-lg p-3 flex items-center">
              <Package className="h-6 w-6 text-orange-500 mr-3 flex-shrink-0" />
              <div>
                <p className="text-xs text-slate-500">Low Stock Items</p>
                <p className="text-lg font-bold text-slate-800">{lowStockCount}</p>
              </div>
            </div>
            <div className="bg-red-50 border border-red-100 rounded-lg p-3 flex items-center">
              <AlertTriangle className="h-6 w-6 text-red-500 mr-3 flex-shrink-0" />
              <div>
                <p className="text-xs text-slate-500">Active Alerts</p>
                <p className="text-lg font-bold text-slate-800">{activeAlerts.length}</p>
              </div>
            </div>
            <div className="bg-teal-50 border border-teal-100 rounded-lg p-3 flex items-center">
              <Users className="h-6 w-6 text-teal-500 mr-3 flex-shrink-0" />
              <div>
                <p className="text-xs text-slate-500">Doctors</p>
                <p className="text-lg font-bold text-slate-800">{doctors.length}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        
        {/* CHC Facility Location Map */}
        <DistrictMap 
          centres={[{ ...centre, healthScore: score?.score }]} 
          title={`${centre.centre_name} • Facility Location Map`} 
          currentCentreId={centre.centre_id} 
          height="320px" 
        />

        {/* AI Stock-Out Prediction Section */}
        <AiStockoutPredictionSection
          centreId={centre.centre_id}
          inventory={inventory}
          medicines={medicines}
          title={`AI Medicine Stock-Out Predictions — ${centre.centre_name}`}
        />

        {/* AI Bed Occupancy Forecasting Section */}
        <AiBedForecastSection
          centreId={centre.centre_id}
          wards={wards}
          title={`AI Bed Occupancy Forecasting — ${centre.centre_name}`}
          lastUpdated={beds}
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

        {/* === LEFT COLUMN === */}
        <div className="space-y-8">

          {/* Inventory Management */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-orange-50 flex items-center justify-between">
              <div className="flex items-center">
                <Package className="h-5 w-5 text-orange-600 mr-2" />
                <h3 className="text-base font-semibold text-slate-800">Manage Medicine Inventory</h3>
              </div>
              <VoiceInventoryIntake 
                inventory={inventory} 
                medicines={medicines}
                onUpdateSuccess={(msg) => {
                  showSuccess(msg);
                  fetchData();
                }} 
              />
            </div>
            <div className="divide-y divide-slate-100">
              {inventory.length === 0 && (
                <p className="p-6 text-sm text-slate-500 text-center">No inventory records for this centre.</p>
              )}
              {inventory.map(item => (
                <div key={item.inventory_id} className="px-6 py-4">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div>
                      <h4 className="font-semibold text-slate-800 text-base flex items-center gap-2">
                        <span>{getMedicineName(item.medicine_id)}</span>
                        <span className="text-[11px] font-medium text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                          ID #{item.medicine_id}
                        </span>
                      </h4>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-sm text-slate-500">Stock: <span className="font-bold text-slate-800">{item.current_stock}</span></span>
                        <span className="text-xs text-slate-400">Min: {item.minimum_stock || 0}</span>
                        {item.current_stock < (item.minimum_stock || 50) && (
                          <span className="text-xs bg-red-100 text-red-700 font-semibold px-2 py-0.5 rounded-full">Low Stock</span>
                        )}
                      </div>
                    </div>
                    <form
                      className="flex items-center gap-2"
                      onSubmit={e => {
                        e.preventDefault();
                        const qty = e.target.elements.qty.value;
                        const type = e.target.elements.type.value;
                        if (qty) handleUpdateInventory(item.inventory_id, qty, type);
                        e.target.reset();
                      }}
                    >
                      <input
                        type="number"
                        name="qty"
                        min="1"
                        placeholder="Qty"
                        required
                        className="w-20 px-2 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
                      />
                      <select
                        name="type"
                        className="px-2 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white"
                      >
                        <option value="IN">Add (IN)</option>
                        <option value="OUT">Use (OUT)</option>
                      </select>
                      <button
                        type="submit"
                        className="p-1.5 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition"
                        title="Save"
                      >
                        <Save className="h-4 w-4" />
                      </button>
                    </form>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Bed Occupancy */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-purple-50 flex items-center">
              <Bed className="h-5 w-5 text-purple-600 mr-2" />
              <h3 className="text-base font-semibold text-slate-800">Update Bed Occupancy</h3>
            </div>
            <div className="divide-y divide-slate-100">
              {wards.length === 0 && (
                <p className="p-6 text-sm text-slate-500 text-center">No wards configured for this centre.</p>
              )}
              {wards.map(ward => {
                const latestBed = beds.find(b => b.ward_id === ward.ward_id);
                const occupied = latestBed ? (latestBed.occupied_beds || 0) : 0;
                const total = ward.total_beds;
                const pct = total > 0 ? Math.round((occupied / total) * 100) : 0;

                return (
                  <div key={ward.ward_id} className="px-6 py-4">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-slate-800">{ward.ward_name}</p>
                        <div className="mt-1.5 flex items-center gap-3">
                          <div className="flex-1 bg-slate-200 rounded-full h-2 max-w-[120px]">
                            <div
                              className={`h-2 rounded-full ${pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-orange-400' : 'bg-purple-500'}`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="text-xs text-slate-500">{occupied}/{total} beds ({pct}%)</span>
                        </div>
                      </div>
                      <form
                        className="flex items-center gap-2"
                        onSubmit={e => {
                          e.preventDefault();
                          const occ = e.target.elements.occ.value;
                          if (occ !== '') handleUpdateBeds(ward.ward_id, occ, total);
                        }}
                      >
                        <input
                          type="number"
                          name="occ"
                          min="0"
                          max={total}
                          defaultValue={occupied}
                          className="w-20 px-2 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
                        />
                        <button
                          type="submit"
                          className="px-3 py-1.5 bg-purple-600 text-white rounded-md text-sm font-medium hover:bg-purple-700 transition"
                        >
                          Update
                        </button>
                      </form>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>

        {/* === RIGHT COLUMN === */}
        <div className="space-y-8">

          {/* Doctor Attendance */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-teal-50 flex items-center">
              <CalendarCheck className="h-5 w-5 text-teal-600 mr-2" />
              <h3 className="text-base font-semibold text-slate-800">Mark Attendance — {new Date().toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' })}</h3>
            </div>
            <div className="divide-y divide-slate-100">
              {doctors.length === 0 && (
                <p className="p-6 text-sm text-slate-500 text-center">No medical staff found for this centre.</p>
              )}
              {doctors.map(doc => {
                const todayAtt = attendance.find(
                  a => a.doctor_id === doc.doctor_id && a.attendance_date === todayStr
                );
                return (
                  <div key={doc.doctor_id} className="px-6 py-4 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-800">{doc.doctor_name}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{doc.specialization}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {todayAtt ? (
                        <span className={`text-xs font-semibold px-3 py-1 rounded-full ${
                          todayAtt.status === 'PRESENT' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                        }`}>
                          {todayAtt.status === 'PRESENT' ? '✓ Present' : '✗ Absent'}
                        </span>
                      ) : (
                        <>
                          <button
                            onClick={() => handleUpdateAttendance(doc.doctor_id, 'PRESENT')}
                            className="px-3 py-1 bg-green-50 text-green-700 border border-green-200 rounded-md text-xs font-medium hover:bg-green-100 transition"
                          >
                            Present
                          </button>
                          <button
                            onClick={() => handleUpdateAttendance(doc.doctor_id, 'ABSENT')}
                            className="px-3 py-1 bg-red-50 text-red-700 border border-red-200 rounded-md text-xs font-medium hover:bg-red-100 transition"
                          >
                            Absent
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Active Alerts */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-red-50 flex items-center justify-between">
              <div className="flex items-center">
                <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
                <h3 className="text-base font-semibold text-red-900">Active Alerts</h3>
              </div>
              {activeAlerts.length > 0 && (
                <span className="text-xs bg-red-600 text-white font-bold px-2 py-0.5 rounded-full">
                  {activeAlerts.length}
                </span>
              )}
            </div>
            <div className="p-4 space-y-3 max-h-80 overflow-y-auto">
              {activeAlerts.length === 0 && (
                <div className="text-center py-6">
                  <CheckCircle2 className="h-10 w-10 text-green-400 mx-auto mb-2" />
                  <p className="text-sm text-slate-500">No active alerts. Centre is in good standing.</p>
                </div>
              )}
              {activeAlerts.map(alert => (
                <div key={alert.alert_id} className="bg-red-50 border border-red-200 p-3 rounded-lg">
                  <div className="flex items-start justify-between">
                    <h4 className="text-sm font-semibold text-red-800">{alert.title}</h4>
                    <span className={`ml-2 text-xs px-1.5 py-0.5 rounded font-medium flex-shrink-0 ${
                      alert.severity === 'HIGH' ? 'bg-red-700 text-white' :
                      alert.severity === 'MEDIUM' ? 'bg-orange-500 text-white' :
                      'bg-yellow-400 text-yellow-900'
                    }`}>
                      {alert.severity || 'INFO'}
                    </span>
                  </div>
                  <p className="text-xs text-red-600 mt-1">{alert.description}</p>
                  <div className="mt-1.5 flex items-center justify-between text-xs text-slate-400">
                    <span>{alert.alert_type}</span>
                    <span>{new Date(alert.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Doctor List */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center">
              <Users className="h-5 w-5 text-slate-500 mr-2" />
              <h3 className="text-base font-semibold text-slate-800">Medical Staff Directory</h3>
            </div>
            <div className="divide-y divide-slate-100">
              {doctors.length === 0 && (
                <p className="p-6 text-sm text-slate-500 text-center">No staff records.</p>
              )}
              {doctors.map(doc => (
                <div key={doc.doctor_id} className="px-6 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{doc.doctor_name}</p>
                    <p className="text-xs text-slate-500">{doc.specialization}</p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    doc.employment_status === 'ACTIVE'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {doc.employment_status || 'N/A'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        </div>
      </div>
    </div>
  );
};

export default ChcDashboard;
