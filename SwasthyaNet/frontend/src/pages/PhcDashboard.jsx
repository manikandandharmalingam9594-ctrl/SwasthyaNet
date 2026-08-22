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
  Plus,
  Save,
  CheckCircle2,
  MapPin
} from 'lucide-react';

const PhcDashboard = () => {
  const { user, logoutUser } = useContext(AuthContext);
  const navigate = useNavigate();

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState("");

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
        throw new Error("No Centre ID associated with this user.");
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
      setError("Failed to load dashboard data. You might not have access to this centre.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (user?.centre_id) {
        fetchData();
    } else {
        setError("Your account does not have a designated Health Centre. Please contact Administrator.");
        setIsLoading(false);
    }
  }, [user]);

  const showSuccess = (msg) => {
      setSuccessMsg(msg);
      setTimeout(() => setSuccessMsg(""), 3000);
  };

  const handleUpdateInventory = async (inventory_id, qty, type) => {
      try {
          await api.put(`/inventory/${inventory_id}`, {
              quantity: parseInt(qty),
              transaction_type: type
          });
          showSuccess("Inventory updated successfully!");
          fetchData(); // Refresh data
      } catch (err) {
          alert("Failed to update inventory.");
      }
  };

  const handleUpdateBeds = async (ward_id, occupied_beds) => {
      try {
          await api.put(`/wards/${ward_id}/occupancy`, {
              occupied_beds: parseInt(occupied_beds),
              recorded_at: new Date().toISOString()
          });
          showSuccess("Bed occupancy updated successfully!");
          fetchData();
      } catch (err) {
          alert("Failed to update beds.");
      }
  };

  const handleUpdateAttendance = async (doctor_id, status) => {
      try {
          await api.post(`/attendance`, {
              doctor_id: parseInt(doctor_id),
              attendance_date: new Date().toISOString().split('T')[0],
              status: status
          });
          showSuccess("Attendance recorded successfully!");
          fetchData();
      } catch (err) {
          alert("Failed to record attendance.");
      }
  };

  const handleLogout = () => {
    logoutUser();
    navigate('/login');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-600 mb-4"></div>
        <p className="text-slate-600">Loading Dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 p-8">
        <div className="max-w-4xl mx-auto bg-red-50 border border-red-200 p-6 rounded-lg shadow-sm">
            <h2 className="text-xl font-bold text-red-700">Access Error</h2>
            <p className="text-red-600 mt-1">{error}</p>
            <button onClick={handleLogout} className="mt-4 px-4 py-2 bg-white text-red-700 border border-red-300 rounded">Logout</button>
        </div>
      </div>
    );
  }

  const { centre, score, inventory, medicines, wards, beds, doctors, attendance, alerts } = data;

  const getMedicineName = (medicineId) => {
    const med = medicines?.find(m => m.medicine_id === medicineId);
    return med ? med.medicine_name : `Medicine #${medicineId}`;
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-12">
      {/* Navbar */}
      <nav className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Building2 className="h-8 w-8 text-green-600 mr-3" />
              <div>
                <span className="text-xl font-bold text-slate-800">SwasthyaNet</span>
                <span className="ml-2 px-2 py-0.5 text-xs font-semibold bg-green-100 text-green-800 rounded-full">
                  PHC Staff
                </span>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-slate-600">{user?.email}</span>
              <button 
                onClick={handleLogout}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-slate-700 bg-slate-100 hover:bg-slate-200 focus:outline-none"
              >
                <LogOut className="h-4 w-4 mr-2" /> Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {successMsg && (
          <div className="fixed top-4 right-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded flex items-center shadow-md z-50 transition-opacity">
              <CheckCircle2 className="h-5 w-5 mr-2" /> {successMsg}
          </div>
      )}

      {/* Header */}
      <div className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">{centre.centre_name} Dashboard</h1>
              <p className="text-slate-500">{centre.centre_type} | {centre.block || centre.village_town || 'Unknown'}</p>
            </div>
            
            <div className="mt-4 md:mt-0 flex items-center bg-slate-50 px-4 py-2 rounded-lg border border-slate-200">
              <Activity className="h-5 w-5 text-slate-500 mr-2" />
              <span className="font-medium text-slate-700 mr-2">Health Score:</span>
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
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        {/* PHC Facility Location Map */}
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
        
        {/* Left Column - Updates */}
        <div className="space-y-8">
            
            {/* Inventory Update */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
                    <div className="flex items-center">
                        <Package className="h-5 w-5 text-orange-600 mr-2" />
                        <h3 className="text-lg font-medium text-slate-900">Manage Inventory</h3>
                    </div>
                    <VoiceInventoryIntake 
                        inventory={inventory} 
                        medicines={medicines}
                        onUpdateSuccess={(msg) => {
                            setSuccessMsg(msg);
                            fetchData();
                        }} 
                    />
                </div>
                <div className="p-6">
                    {inventory.map(item => (
                        <div key={item.inventory_id} className="flex flex-col sm:flex-row sm:items-center justify-between py-3 border-b border-slate-100 last:border-0">
                            <div>
                                <h4 className="font-semibold text-slate-800 text-base flex items-center gap-2">
                                    <span>{getMedicineName(item.medicine_id)}</span>
                                    <span className="text-[11px] font-medium text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                                      ID #{item.medicine_id}
                                    </span>
                                </h4>
                                <p className="text-sm text-slate-500 mt-0.5">Current Stock: <span className="font-bold text-slate-800">{item.current_stock}</span></p>
                            </div>
                            <form 
                                className="flex mt-2 sm:mt-0 space-x-2"
                                onSubmit={(e) => {
                                    e.preventDefault();
                                    const qty = e.target.elements.qty.value;
                                    const type = e.target.elements.type.value;
                                    if(qty) handleUpdateInventory(item.inventory_id, qty, type);
                                    e.target.reset();
                                }}
                            >
                                <input type="number" name="qty" min="1" placeholder="Qty" required className="w-20 px-2 py-1 border border-slate-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-green-500" />
                                <select name="type" className="px-2 py-1 border border-slate-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-green-500">
                                    <option value="IN">Add (IN)</option>
                                    <option value="OUT">Use (OUT)</option>
                                </select>
                                <button type="submit" className="p-1.5 bg-green-600 text-white rounded hover:bg-green-700 transition">
                                    <Save className="h-4 w-4" />
                                </button>
                            </form>
                        </div>
                    ))}
                    {inventory.length === 0 && <p className="text-sm text-slate-500">No inventory tracked.</p>}
                </div>
            </div>

            {/* Bed Occupancy Update */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-200 flex items-center bg-slate-50">
                    <Bed className="h-5 w-5 text-teal-600 mr-2" />
                    <h3 className="text-lg font-medium text-slate-900">Update Bed Occupancy</h3>
                </div>
                <div className="p-6">
                    {wards.map(ward => {
                        const latestBed = beds.find(b => b.ward_id === ward.ward_id);
                        const occupied = latestBed ? (latestBed.occupied_beds || 0) : 0;
                        const total = ward.total_beds;
                        
                        return (
                            <div key={ward.ward_id} className="flex flex-col sm:flex-row sm:items-center justify-between py-3 border-b border-slate-100 last:border-0">
                                <div>
                                    <h4 className="font-medium text-slate-800">{ward.ward_name}</h4>
                                    <p className="text-sm text-slate-500">Occupied: {occupied} / {total}</p>
                                </div>
                                <form 
                                    className="flex mt-2 sm:mt-0 space-x-2"
                                    onSubmit={(e) => {
                                        e.preventDefault();
                                        const occ = e.target.elements.occ.value;
                                        if(occ) handleUpdateBeds(ward.ward_id, occ);
                                    }}
                                >
                                    <input type="number" name="occ" min="0" max={total} defaultValue={occupied} required className="w-20 px-2 py-1 border border-slate-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-teal-500" />
                                    <button type="submit" className="px-3 py-1.5 bg-teal-600 text-white rounded text-sm font-medium hover:bg-teal-700 transition">
                                        Update
                                    </button>
                                </form>
                            </div>
                        )
                    })}
                    {wards.length === 0 && <p className="text-sm text-slate-500">No wards available.</p>}
                </div>
            </div>

        </div>

        {/* Right Column - Status */}
        <div className="space-y-8">
            
            {/* Doctors & Attendance */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-200 flex items-center bg-slate-50">
                    <CalendarCheck className="h-5 w-5 text-purple-600 mr-2" />
                    <h3 className="text-lg font-medium text-slate-900">Mark Attendance</h3>
                </div>
                <div className="p-6">
                    {doctors.map(doc => {
                        const todayStr = new Date().toISOString().split('T')[0];
                        const todayAtt = attendance.find(a => a.doctor_id === doc.doctor_id && a.attendance_date === todayStr);
                        
                        return (
                            <div key={doc.doctor_id} className="flex flex-col sm:flex-row sm:items-center justify-between py-3 border-b border-slate-100 last:border-0">
                                <div>
                                    <h4 className="font-medium text-slate-800">{doc.doctor_name}</h4>
                                    <p className="text-xs text-slate-500">{doc.specialization}</p>
                                </div>
                                <div className="mt-2 sm:mt-0 flex items-center space-x-2">
                                    {todayAtt ? (
                                        <span className={`text-xs font-semibold px-2 py-1 rounded-full ${todayAtt.status === 'PRESENT' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                            Marked: {todayAtt.status}
                                        </span>
                                    ) : (
                                        <>
                                            <button onClick={() => handleUpdateAttendance(doc.doctor_id, 'PRESENT')} className="px-3 py-1 bg-green-50 text-green-700 border border-green-200 rounded text-xs font-medium hover:bg-green-100 transition">Present</button>
                                            <button onClick={() => handleUpdateAttendance(doc.doctor_id, 'ABSENT')} className="px-3 py-1 bg-red-50 text-red-700 border border-red-200 rounded text-xs font-medium hover:bg-red-100 transition">Absent</button>
                                        </>
                                    )}
                                </div>
                            </div>
                        )
                    })}
                    {doctors.length === 0 && <p className="text-sm text-slate-500">No medical staff found.</p>}
                </div>
            </div>

            {/* Alerts */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-200 flex items-center bg-red-50">
                    <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
                    <h3 className="text-lg font-medium text-red-900">Active Alerts</h3>
                </div>
                <div className="p-4">
                    {alerts.filter(a => a.status !== 'RESOLVED' && a.status !== 'Resolved').map(alert => (
                        <div key={alert.alert_id} className="mb-3 last:mb-0 bg-white border border-red-200 p-3 rounded-lg shadow-sm">
                            <h4 className="font-semibold text-red-700 text-sm">{alert.title}</h4>
                            <p className="text-xs text-red-600 mt-1">{alert.description}</p>
                            <div className="mt-2 text-xs text-slate-500 flex justify-between">
                                <span>{alert.alert_type}</span>
                                <span>{new Date(alert.created_at).toLocaleDateString()}</span>
                            </div>
                        </div>
                    ))}
                    {alerts.filter(a => a.status !== 'RESOLVED' && a.status !== 'Resolved').length === 0 && (
                        <p className="text-slate-500 text-sm text-center py-4">No active alerts.</p>
                    )}
                </div>
            </div>

        </div>
      </div>
      </div>
    </div>
  );
};

export default PhcDashboard;
