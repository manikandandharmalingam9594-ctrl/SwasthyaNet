import React, { useEffect, useState, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { AuthContext } from '../context/AuthContext';
import DistrictMap from '../components/DistrictMap';
import {
  ArrowLeft,
  Activity,
  Bed,
  Package,
  History,
  Users,
  AlertTriangle,
  Building2,
  CalendarCheck,
  MapPin
} from 'lucide-react';

const CentreDetails = () => {
  const { centreId } = useParams();
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const [data, setData] = useState({
    centre: null,
    score: null,
    inventory: [],
    medicines: [],
    stockHistory: [],
    wards: [],
    beds: [],
    doctors: [],
    attendance: [],
    alerts: []
  });

  useEffect(() => {
    const fetchCentreDetails = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const [
          centreRes,
          scoreRes,
          invRes,
          medsRes,
          histRes,
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
          api.get(`/centres/${centreId}/stock-history`),
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
          stockHistory: histRes.data,
          wards: wardsRes.data,
          beds: bedsRes.data,
          doctors: docsRes.data,
          attendance: attRes.data,
          alerts: alertsRes.data
        });

      } catch (err) {
        console.error("Error fetching centre details:", err);
        if (err.response && err.response.status === 403) {
            setError("You do not have permission to view this centre's data.");
        } else {
            setError("Failed to load centre data. Please try again later.");
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchCentreDetails();
  }, [centreId]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600 mb-4"></div>
        <p className="text-slate-600">Loading Centre Details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 p-8">
        <div className="max-w-4xl mx-auto bg-red-50 border border-red-200 p-6 rounded-lg shadow-sm">
            <div className="flex items-center">
                <AlertTriangle className="h-8 w-8 text-red-500 mr-4" />
                <div>
                    <h2 className="text-xl font-bold text-red-700">Access Error</h2>
                    <p className="text-red-600 mt-1">{error}</p>
                </div>
            </div>
            <button 
                onClick={() => navigate(-1)}
                className="mt-6 px-4 py-2 bg-white border border-red-300 text-red-700 rounded-md hover:bg-red-50"
            >
                Go Back
            </button>
        </div>
      </div>
    );
  }

  const { centre, score, inventory, medicines, stockHistory, wards, beds, doctors, attendance, alerts } = data;

  const getMedicineName = (medicineId) => {
    const med = medicines?.find(m => m.medicine_id === medicineId);
    return med ? med.medicine_name : `Medicine #${medicineId}`;
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-12">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button 
            onClick={() => navigate(-1)}
            className="flex items-center text-sm text-slate-500 hover:text-blue-600 transition mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-1" /> Back
          </button>
          
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div className="flex items-center">
              <div className="bg-blue-100 p-3 rounded-lg mr-4">
                <Building2 className="h-8 w-8 text-blue-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">{centre.centre_name}</h1>
                <p className="text-slate-500">{centre.centre_type} | {centre.block || centre.village_town || 'Unknown Location'}</p>
              </div>
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-8">
            
            {/* Wards & Beds */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-200 flex items-center bg-slate-50">
                    <Bed className="h-5 w-5 text-teal-600 mr-2" />
                    <h3 className="text-lg font-medium text-slate-900">Wards & Bed Occupancy</h3>
                </div>
                <div className="p-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {wards.map(ward => {
                        const latestBed = beds.find(b => b.ward_id === ward.ward_id);
                        const total = ward.total_beds || 0;
                        const occupied = latestBed ? (latestBed.occupied_beds || 0) : (ward.occupied_beds || 0);
                        const pct = total > 0 ? Math.round((occupied / total) * 100) : 0;
                        return (
                            <div key={ward.ward_id} className="border border-slate-200 p-4 rounded-lg bg-slate-50">
                                <div className="flex justify-between items-center mb-2">
                                    <h4 className="font-semibold text-slate-800">{ward.ward_name}</h4>
                                    <span className="text-xs px-2 py-0.5 bg-slate-200 text-slate-700 rounded-full">{ward.ward_type}</span>
                                </div>
                                <div className="text-sm text-slate-600 mb-2">
                                    Occupancy: <span className="font-bold text-slate-800">{occupied}/{total}</span> beds ({pct}%)
                                </div>
                                <div className="w-full bg-slate-200 rounded-full h-2">
                                    <div 
                                        className={`h-2 rounded-full ${pct > 80 ? 'bg-red-500' : pct > 50 ? 'bg-orange-500' : 'bg-teal-500'}`} 
                                        style={{ width: `${Math.min(pct, 100)}%` }}
                                    ></div>
                                </div>
                            </div>
                        )
                    })}
                    {wards.length === 0 && <p className="text-slate-500 text-sm">No ward data available.</p>}
                </div>
            </div>

            {/* Inventory */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-200 flex items-center bg-slate-50">
                    <Package className="h-5 w-5 text-orange-600 mr-2" />
                    <h3 className="text-lg font-medium text-slate-900">Medicine Inventory</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-200">
                        <thead className="bg-white">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Medicine</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Stock</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Min Stock</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200">
                            {inventory.map(item => (
                                <tr key={item.inventory_id}>
                                    <td className="px-6 py-4 text-sm text-slate-900">
                                        <div className="font-semibold text-slate-800">{getMedicineName(item.medicine_id)}</div>
                                        <div className="text-xs text-slate-400">ID #{item.medicine_id}</div>
                                    </td>
                                    <td className="px-6 py-4 text-sm font-bold text-slate-800">{item.current_stock}</td>
                                    <td className="px-6 py-4 text-sm text-slate-500">{item.minimum_stock || 0}</td>
                                    <td className="px-6 py-4 text-sm">
                                        {item.current_stock < (item.minimum_stock || 50) ? (
                                            <span className="text-red-600 font-semibold bg-red-50 px-2 py-1 rounded-full text-xs">Low Stock</span>
                                        ) : (
                                            <span className="text-green-600 font-semibold bg-green-50 px-2 py-1 rounded-full text-xs">Adequate</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {inventory.length === 0 && (
                                <tr>
                                    <td colSpan="4" className="px-6 py-4 text-slate-500 text-center">No inventory records.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Stock History */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-200 flex items-center bg-slate-50">
                    <History className="h-5 w-5 text-indigo-600 mr-2" />
                    <h3 className="text-lg font-medium text-slate-900">Recent Stock History</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-200">
                        <thead className="bg-white">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Date</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Medicine ID</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Type</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Quantity</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200">
                            {stockHistory.slice(0, 5).map(hist => (
                                <tr key={hist.history_id}>
                                    <td className="px-6 py-4 text-sm text-slate-500">{new Date(hist.recorded_at).toLocaleDateString()}</td>
                                    <td className="px-6 py-4 text-sm text-slate-900">{hist.medicine_id}</td>
                                    <td className="px-6 py-4 text-sm">
                                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                                            hist.transaction_type === 'IN' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                        }`}>
                                            {hist.transaction_type}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm font-medium">{hist.quantity}</td>
                                </tr>
                            ))}
                            {stockHistory.length === 0 && (
                                <tr>
                                    <td colSpan="4" className="px-6 py-4 text-slate-500 text-center">No history records.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>

        {/* Right Column */}
        <div className="space-y-8">
            
            {/* Geographical Map */}
            <DistrictMap 
              centres={[{ ...centre, healthScore: score?.score }]} 
              title="Geographical Location" 
              currentCentreId={centre.centre_id} 
              height="260px" 
            />

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

            {/* Doctors */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-200 flex items-center bg-slate-50">
                    <Users className="h-5 w-5 text-blue-600 mr-2" />
                    <h3 className="text-lg font-medium text-slate-900">Medical Staff</h3>
                </div>
                <div className="p-4">
                    {doctors.map(doc => (
                        <div key={doc.doctor_id} className="flex items-center justify-between py-3 border-b border-slate-100 last:border-0">
                            <div>
                                <h4 className="text-sm font-semibold text-slate-800">{doc.doctor_name}</h4>
                                <p className="text-xs text-slate-500">{doc.specialization}</p>
                            </div>
                            <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                                doc.employment_status === 'ACTIVE' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-700'
                            }`}>
                                {doc.employment_status}
                            </span>
                        </div>
                    ))}
                    {doctors.length === 0 && (
                        <p className="text-slate-500 text-sm text-center py-4">No staff records.</p>
                    )}
                </div>
            </div>

            {/* Attendance */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-200 flex items-center bg-slate-50">
                    <CalendarCheck className="h-5 w-5 text-purple-600 mr-2" />
                    <h3 className="text-lg font-medium text-slate-900">Recent Attendance</h3>
                </div>
                <div className="p-4">
                    {attendance.slice(0, 5).map(att => {
                        const doc = doctors.find(d => d.doctor_id === att.doctor_id);
                        return (
                            <div key={att.attendance_id} className="mb-3 last:mb-0 border border-slate-200 p-3 rounded-lg bg-slate-50">
                                <div className="flex justify-between">
                                    <h4 className="text-sm font-semibold text-slate-800">{doc ? doc.doctor_name : `Doc ID: ${att.doctor_id}`}</h4>
                                    <span className="text-xs text-slate-500">{new Date(att.attendance_date).toLocaleDateString()}</span>
                                </div>
                                <div className="mt-2 text-xs font-medium">
                                    Status: <span className={att.status === 'PRESENT' ? 'text-green-600' : 'text-red-600'}>{att.status}</span>
                                </div>
                            </div>
                        )
                    })}
                    {attendance.length === 0 && (
                        <p className="text-slate-500 text-sm text-center py-4">No attendance records.</p>
                    )}
                </div>
            </div>

        </div>

      </div>
    </div>
  );
};

export default CentreDetails;
