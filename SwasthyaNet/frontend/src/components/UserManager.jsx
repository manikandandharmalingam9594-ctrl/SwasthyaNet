import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import api from '../services/api';
import { 
  Users, 
  UserPlus, 
  Search, 
  Filter, 
  CheckCircle2, 
  XCircle, 
  Shield, 
  Building2, 
  MapPin, 
  AlertTriangle,
  X,
  Loader2,
  Lock,
  Mail,
  User as UserIcon,
  ToggleLeft,
  ToggleRight
} from 'lucide-react';

const UserManager = () => {
  const { user: currentUser } = useContext(AuthContext);
  const isSuperAdmin = currentUser?.role === 'SUPER_ADMIN';

  const [usersList, setUsersList] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [centres, setCentres] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successToast, setSuccessToast] = useState('');

  // Filtering
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);

  // Form Fields
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: isSuperAdmin ? 'DISTRICT_ADMIN' : 'PHC_STAFF',
    district_id: isSuperAdmin ? '' : currentUser?.district_id || '',
    centre_id: ''
  });

  const showToast = (msg) => {
    setSuccessToast(msg);
    setTimeout(() => setSuccessToast(''), 4000);
  };

  const fetchUsersAndMetadata = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [usersRes, distRes, centresRes] = await Promise.all([
        api.get('/users'),
        api.get('/districts').catch(() => ({ data: [] })),
        api.get('/centres').catch(() => ({ data: [] }))
      ]);

      setUsersList(usersRes.data || []);
      setDistricts(distRes.data || []);
      setCentres(centresRes.data || []);
    } catch (err) {
      console.error('Error loading users:', err);
      setError(err.response?.data?.detail || 'Failed to load user management data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsersAndMetadata();
  }, []);

  const handleToggleStatus = async (targetUser) => {
    try {
      const newStatus = !targetUser.is_active;
      await api.patch(`/users/${targetUser.user_id}/status`, {
        is_active: newStatus
      });
      showToast(`User ${targetUser.email} has been ${newStatus ? 'activated' : 'deactivated'}.`);
      // Update locally
      setUsersList(prev => prev.map(u => 
        u.user_id === targetUser.user_id ? { ...u, is_active: newStatus } : u
      ));
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update user status.');
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setFormError(null);
    setIsSubmitting(true);

    try {
      const payload = {
        name: formData.name.trim(),
        email: formData.email.trim(),
        password: formData.password,
        role: formData.role,
        district_id: formData.district_id ? parseInt(formData.district_id) : null,
        centre_id: formData.centre_id ? parseInt(formData.centre_id) : null,
        is_active: true
      };

      if (!payload.name || !payload.email || !payload.password) {
        throw new Error('Please fill in all required fields.');
      }

      if (payload.role === 'DISTRICT_ADMIN' && !payload.district_id) {
        throw new Error('District selection is required for District Admin role.');
      }

      if ((payload.role === 'PHC_STAFF' || payload.role === 'CHC_STAFF') && !payload.centre_id) {
        throw new Error('Centre selection is required for Staff roles.');
      }

      const res = await api.post('/users', payload);
      showToast(`User account for ${res.data.email} created successfully!`);
      setIsModalOpen(false);
      
      // Reset form
      setFormData({
        name: '',
        email: '',
        password: '',
        role: isSuperAdmin ? 'DISTRICT_ADMIN' : 'PHC_STAFF',
        district_id: isSuperAdmin ? '' : currentUser?.district_id || '',
        centre_id: ''
      });

      // Refresh list
      fetchUsersAndMetadata();
    } catch (err) {
      console.error('Error creating user:', err);
      setFormError(err.response?.data?.detail || err.message || 'Failed to create user account.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Maps for lookup
  const districtMap = {};
  districts.forEach(d => { districtMap[d.district_id] = d.district_name; });

  const centreMap = {};
  centres.forEach(c => { centreMap[c.centre_id] = c; });

  // Filtered centre options based on chosen district and role
  const availableCentres = centres.filter(c => {
    if (!formData.district_id) return false;
    const matchesDistrict = c.district_id === parseInt(formData.district_id);
    if (formData.role === 'PHC_STAFF') return matchesDistrict && c.centre_type === 'PHC';
    if (formData.role === 'CHC_STAFF') return matchesDistrict && c.centre_type === 'CHC';
    return matchesDistrict;
  });

  // Filtered Users
  const filteredUsers = usersList.filter(u => {
    const matchesSearch = 
      u.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (districtMap[u.district_id] && districtMap[u.district_id].toLowerCase().includes(searchQuery.toLowerCase())) ||
      (centreMap[u.centre_id] && centreMap[u.centre_id].centre_name.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesRole = roleFilter === 'ALL' || u.role === roleFilter;
    const matchesStatus = 
      statusFilter === 'ALL' || 
      (statusFilter === 'ACTIVE' && u.is_active) || 
      (statusFilter === 'INACTIVE' && !u.is_active);

    return matchesSearch && matchesRole && matchesStatus;
  });

  return (
    <div className="space-y-6">
      
      {/* Toast Notification */}
      {successToast && (
        <div className="fixed top-4 right-4 bg-emerald-100 border border-emerald-400 text-emerald-800 px-4 py-3 rounded-lg flex items-center shadow-lg z-50 animate-pulse">
          <CheckCircle2 className="h-5 w-5 mr-2 text-emerald-600" />
          <span className="font-medium text-sm">{successToast}</span>
        </div>
      )}

      {/* Header & Action Bar */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center">
            <Users className="h-6 w-6 text-indigo-600 mr-2" />
            User & Access Management
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {isSuperAdmin 
              ? 'Manage system-wide administrators and healthcare staff across all districts.' 
              : 'Manage healthcare personnel and assignments within your district.'}
          </p>
        </div>

        <button
          onClick={() => { setFormError(null); setIsModalOpen(true); }}
          className="inline-flex items-center justify-center px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm rounded-lg shadow-sm transition focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <UserPlus className="h-4 w-4 mr-2" />
          Create New User
        </button>
      </div>

      {/* Filter and Search Toolbar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-1 min-w-[240px] items-center relative">
          <Search className="h-4 w-4 absolute left-3 text-slate-400" />
          <input 
            type="text"
            placeholder="Search by name, email, district or centre..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Role Filter */}
          <select 
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="ALL">All Roles</option>
            {isSuperAdmin && <option value="SUPER_ADMIN">Super Admin</option>}
            {isSuperAdmin && <option value="DISTRICT_ADMIN">District Admin</option>}
            <option value="PHC_STAFF">PHC Staff</option>
            <option value="CHC_STAFF">CHC Staff</option>
          </select>

          {/* Status Filter */}
          <select 
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="ALL">All Status</option>
            <option value="ACTIVE">Active Only</option>
            <option value="INACTIVE">Inactive Only</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="py-12 flex flex-col items-center justify-center">
            <Loader2 className="h-8 w-8 text-indigo-600 animate-spin mb-2" />
            <p className="text-sm text-slate-500">Loading user accounts...</p>
          </div>
        ) : error ? (
          <div className="p-6 text-center text-red-600">
            <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <p className="text-sm font-medium">{error}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th scope="col" className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    User Details
                  </th>
                  <th scope="col" className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th scope="col" className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Jurisdiction / Assignment
                  </th>
                  <th scope="col" className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3.5 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {filteredUsers.map((u) => {
                  const centre = centreMap[u.centre_id];
                  const districtName = districtMap[u.district_id] || (centre ? districtMap[centre.district_id] : null);
                  const isSelf = u.user_id === currentUser?.user_id;

                  return (
                    <tr key={u.user_id} className="hover:bg-slate-50 transition">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="h-9 w-9 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 font-semibold text-sm mr-3">
                            {u.name ? u.name.charAt(0).toUpperCase() : 'U'}
                          </div>
                          <div>
                            <div className="text-sm font-semibold text-slate-900 flex items-center">
                              {u.name}
                              {isSelf && (
                                <span className="ml-2 text-[10px] bg-slate-100 text-slate-600 font-bold px-2 py-0.5 rounded-full">
                                  You
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-slate-500">{u.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2.5 py-1 inline-flex text-xs font-semibold rounded-full ${
                          u.role === 'SUPER_ADMIN' ? 'bg-indigo-100 text-indigo-800' :
                          u.role === 'DISTRICT_ADMIN' ? 'bg-blue-100 text-blue-800' :
                          u.role === 'CHC_STAFF' ? 'bg-purple-100 text-purple-800' :
                          'bg-emerald-100 text-emerald-800'
                        }`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-slate-800">
                          {centre ? (
                            <div className="flex items-center text-xs text-slate-700">
                              <Building2 className="h-3.5 w-3.5 text-slate-400 mr-1 flex-shrink-0" />
                              <span className="font-medium">{centre.centre_name}</span>
                              <span className="text-slate-400 ml-1">({centre.centre_type})</span>
                            </div>
                          ) : districtName ? (
                            <div className="flex items-center text-xs text-slate-700">
                              <MapPin className="h-3.5 w-3.5 text-slate-400 mr-1 flex-shrink-0" />
                              <span className="font-medium">{districtName} District</span>
                            </div>
                          ) : (
                            <span className="text-xs text-slate-400">System-Wide Access</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2.5 py-0.5 inline-flex text-xs font-semibold rounded-full ${
                          u.is_active 
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}>
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        {/* Only allow toggle if not self and permitted by RBAC */}
                        {!isSelf && (isSuperAdmin || (u.role !== 'SUPER_ADMIN' && u.role !== 'DISTRICT_ADMIN')) ? (
                          <button
                            onClick={() => handleToggleStatus(u)}
                            className={`inline-flex items-center px-2.5 py-1 text-xs font-semibold rounded-md border transition ${
                              u.is_active
                                ? 'border-rose-300 text-rose-700 hover:bg-rose-50'
                                : 'border-emerald-300 text-emerald-700 hover:bg-emerald-50'
                            }`}
                          >
                            {u.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                        ) : (
                          <span className="text-xs text-slate-400 italic">Protected</span>
                        )}
                      </td>
                    </tr>
                  );
                })}

                {filteredUsers.length === 0 && (
                  <tr>
                    <td colSpan="5" className="px-6 py-10 text-center text-sm text-slate-500">
                      No user accounts match the current filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create User Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden transform transition-all animate-in fade-in zoom-in-95">
            
            {/* Modal Header */}
            <div className="px-6 py-4 bg-indigo-600 text-white flex items-center justify-between">
              <h3 className="text-lg font-bold flex items-center">
                <UserPlus className="h-5 w-5 mr-2" />
                Create New User Account
              </h3>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="text-indigo-200 hover:text-white transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Body / Form */}
            <form onSubmit={handleCreateUser} className="p-6 space-y-4">
              
              {formError && (
                <div className="bg-rose-50 border border-rose-200 text-rose-700 p-3 rounded-lg text-xs font-medium flex items-center">
                  <AlertTriangle className="h-4 w-4 mr-2 flex-shrink-0 text-rose-500" />
                  <span>{formError}</span>
                </div>
              )}

              {/* Full Name */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Full Name <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <UserIcon className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input 
                    type="text" 
                    required
                    placeholder="e.g. Dr. Rajesh Kumar"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              {/* Email Address */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Email Address <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <Mail className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input 
                    type="email" 
                    required
                    placeholder="e.g. rajesh@swasthyanet.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Password <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <Lock className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input 
                    type="password" 
                    required
                    placeholder="Enter secure password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              {/* Role Selection */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Role <span className="text-rose-500">*</span>
                </label>
                <select
                  value={formData.role}
                  onChange={(e) => {
                    setFormData({ 
                      ...formData, 
                      role: e.target.value,
                      centre_id: '' 
                    });
                  }}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {isSuperAdmin && <option value="DISTRICT_ADMIN">District Admin</option>}
                  <option value="PHC_STAFF">PHC Staff</option>
                  <option value="CHC_STAFF">CHC Staff</option>
                </select>
              </div>

              {/* District Selection (Only visible for Super Admin) */}
              {isSuperAdmin && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    District <span className="text-rose-500">*</span>
                  </label>
                  <select
                    required
                    value={formData.district_id}
                    onChange={(e) => {
                      setFormData({ 
                        ...formData, 
                        district_id: e.target.value,
                        centre_id: '' 
                      });
                    }}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">-- Select District --</option>
                    {districts.map(d => (
                      <option key={d.district_id} value={d.district_id}>
                        {d.district_name} ({d.state})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Centre Selection (For Staff roles) */}
              {(formData.role === 'PHC_STAFF' || formData.role === 'CHC_STAFF') && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Assigned Health Centre <span className="text-rose-500">*</span>
                  </label>
                  <select
                    required
                    value={formData.centre_id}
                    onChange={(e) => setFormData({ ...formData, centre_id: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">-- Select Assigned Centre --</option>
                    {availableCentres.map(c => (
                      <option key={c.centre_id} value={c.centre_id}>
                        {c.centre_name} ({c.centre_type})
                      </option>
                    ))}
                  </select>
                  {availableCentres.length === 0 && formData.district_id && (
                    <p className="text-[11px] text-amber-600 mt-1">
                      No matching {formData.role === 'PHC_STAFF' ? 'PHC' : 'CHC'} centres found in this district.
                    </p>
                  )}
                </div>
              )}

              {/* Modal Footer */}
              <div className="pt-4 flex items-center justify-end space-x-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm transition flex items-center disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Creating Account...
                    </>
                  ) : (
                    'Create User'
                  )}
                </button>
              </div>

            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default UserManager;
