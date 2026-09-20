import React, { useState, useEffect, useContext } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import api from '../services/api';
import { 
  ShieldCheck, 
  Lock, 
  KeyRound, 
  CheckCircle2, 
  AlertTriangle, 
  Loader2, 
  Eye, 
  EyeOff, 
  User, 
  Mail, 
  Building2, 
  MapPin, 
  ArrowRight,
  Sparkles
} from 'lucide-react';

const ActivateAccount = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const { loginUser } = useContext(AuthContext);

  const [isVerifying, setIsVerifying] = useState(true);
  const [tokenError, setTokenError] = useState(null);
  const [userInfo, setUserInfo] = useState(null);

  // Form State
  const [tempPassword, setTempPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showTempPassword, setShowTempPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);
  const [isActivatedSuccess, setIsActivatedSuccess] = useState(false);
  const [activatedUserData, setActivatedUserData] = useState(null);

  useEffect(() => {
    if (!token) {
      setIsVerifying(false);
      setTokenError('No activation token provided in the URL. Please check the link in your email.');
      return;
    }

    const verifyToken = async () => {
      try {
        setIsVerifying(true);
        setTokenError(null);
        const res = await api.get(`/auth/verify-activation-token?token=${encodeURIComponent(token)}`);
        setUserInfo(res.data);
      } catch (err) {
        console.error('Token verification error:', err);
        setTokenError(err.response?.data?.detail || 'Invalid or expired activation link. Please contact your system administrator.');
      } finally {
        setIsVerifying(false);
      }
    };

    verifyToken();
  }, [token]);

  // Password Strength Calculation
  const calculateStrength = (pwd) => {
    if (!pwd) return { score: 0, label: 'None', color: 'bg-slate-200' };
    let score = 0;
    if (pwd.length >= 6) score += 1;
    if (pwd.length >= 8) score += 1;
    if (/[A-Z]/.test(pwd)) score += 1;
    if (/[0-9]/.test(pwd)) score += 1;
    if (/[^A-Za-z0-9]/.test(pwd)) score += 1;

    if (score <= 2) return { score: 1, label: 'Weak', color: 'bg-rose-500' };
    if (score <= 4) return { score: 2, label: 'Moderate', color: 'bg-amber-500' };
    return { score: 3, label: 'Strong', color: 'bg-emerald-500' };
  };

  const strength = calculateStrength(newPassword);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);

    if (newPassword.length < 6) {
      setFormError('New password must be at least 6 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setFormError('New password and confirmation password do not match.');
      return;
    }

    try {
      setIsSubmitting(true);
      const res = await api.post('/auth/activate-account', {
        token: token,
        temporary_password: tempPassword.trim() || null,
        new_password: newPassword
      });

      const { access_token, user } = res.data;
      setActivatedUserData(user);
      setIsActivatedSuccess(true);

      // Log in user immediately
      loginUser(access_token, user);

      // Auto redirect after 2.5 seconds
      setTimeout(() => {
        redirectToDashboard(user.role);
      }, 2500);

    } catch (err) {
      console.error('Activation submission error:', err);
      setFormError(err.response?.data?.detail || 'Failed to activate account. Please check your credentials and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const redirectToDashboard = (role) => {
    switch (role) {
      case 'SUPER_ADMIN':
        navigate('/super-admin');
        break;
      case 'DISTRICT_ADMIN':
        navigate('/district-admin');
        break;
      case 'PHC_STAFF':
        navigate('/phc');
        break;
      case 'CHC_STAFF':
        navigate('/chc');
        break;
      default:
        navigate('/login');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="h-14 w-14 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-200">
            <ShieldCheck className="h-8 w-8" />
          </div>
        </div>
        <h1 className="mt-4 text-center text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          SwasthyaNet
        </h1>
        <p className="mt-1 text-center text-xs sm:text-sm font-medium text-slate-500 uppercase tracking-wider">
          Account Activation & Password Setup
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-lg">
        <div className="bg-white py-8 px-6 shadow-xl shadow-slate-200/60 rounded-2xl border border-slate-200/80">
          
          {/* Loading State */}
          {isVerifying && (
            <div className="py-12 flex flex-col items-center justify-center text-center">
              <Loader2 className="h-10 w-10 text-indigo-600 animate-spin mb-4" />
              <h3 className="text-base font-semibold text-slate-800">Verifying Activation Link...</h3>
              <p className="text-xs text-slate-500 mt-1">Please wait while we validate your invitation token.</p>
            </div>
          )}

          {/* Token Error State */}
          {!isVerifying && tokenError && (
            <div className="text-center py-6">
              <div className="h-14 w-14 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto mb-4 border border-rose-200">
                <AlertTriangle className="h-7 w-7" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Activation Link Invalid or Expired</h3>
              <p className="text-xs sm:text-sm text-slate-600 mb-6 leading-relaxed">
                {tokenError}
              </p>
              <div className="space-y-3">
                <Link
                  to="/login"
                  className="w-full inline-flex justify-center items-center py-2.5 px-4 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition shadow-sm"
                >
                  Return to Login
                </Link>
              </div>
            </div>
          )}

          {/* Successful Activation Screen */}
          {!isVerifying && isActivatedSuccess && (
            <div className="text-center py-6 animate-in fade-in zoom-in-95">
              <div className="h-16 w-16 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-4 border border-emerald-200">
                <CheckCircle2 className="h-9 w-9" />
              </div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-50 border border-indigo-200 rounded-full text-indigo-700 text-xs font-semibold mb-3">
                <Sparkles className="h-3.5 w-3.5" />
                Account Activated Successfully!
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-1">
                Welcome to SwasthyaNet, {activatedUserData?.name || userInfo?.name}!
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 mb-6 leading-relaxed">
                Your permanent password has been configured. You are being redirected to your dashboard...
              </p>

              <button
                onClick={() => redirectToDashboard(activatedUserData?.role || userInfo?.role)}
                className="w-full inline-flex justify-center items-center py-2.5 px-4 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition shadow-md gap-2"
              >
                Go to Dashboard Now
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Activation Form Screen */}
          {!isVerifying && !tokenError && !isActivatedSuccess && userInfo && (
            <div>
              
              {/* User Greeting & Jurisdiction Info */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 mb-6">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-base font-bold text-slate-900 flex items-center gap-1.5">
                      <User className="h-4 w-4 text-indigo-600" />
                      {userInfo.name}
                    </h2>
                    <div className="text-xs text-slate-600 flex items-center gap-1 mt-0.5">
                      <Mail className="h-3.5 w-3.5 text-slate-400" />
                      {userInfo.email}
                    </div>
                  </div>
                  <span className="px-2.5 py-1 text-[11px] font-bold rounded-full bg-indigo-100 text-indigo-800 border border-indigo-200">
                    {userInfo.role?.replace('_', ' ')}
                  </span>
                </div>

                {(userInfo.centre_name || userInfo.district_name) && (
                  <div className="mt-3 pt-3 border-t border-slate-200 text-xs text-slate-700 flex flex-wrap gap-3">
                    {userInfo.centre_name && (
                      <div className="flex items-center gap-1">
                        <Building2 className="h-3.5 w-3.5 text-slate-400" />
                        <span className="font-semibold">{userInfo.centre_name}</span>
                      </div>
                    )}
                    {userInfo.district_name && (
                      <div className="flex items-center gap-1">
                        <MapPin className="h-3.5 w-3.5 text-slate-400" />
                        <span>{userInfo.district_name} District</span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {formError && (
                <div className="mb-5 bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-xl text-xs font-medium flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-rose-500 flex-shrink-0" />
                  <span>{formError}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                
                {/* Temporary Password Field (Optional if verified by token) */}
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Temporary Password (from email)
                  </label>
                  <div className="relative">
                    <KeyRound className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type={showTempPassword ? 'text' : 'password'}
                      placeholder="Paste temporary password (optional)"
                      value={tempPassword}
                      onChange={(e) => setTempPassword(e.target.value)}
                      className="w-full pl-9 pr-10 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                    />
                    <button
                      type="button"
                      onClick={() => setShowTempPassword(!showTempPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none"
                    >
                      {showTempPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Found in the invitation email sent to your inbox.
                  </p>
                </div>

                {/* New Permanent Password Field */}
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Set New Permanent Password <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Lock className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type={showNewPassword ? 'text' : 'password'}
                      required
                      minLength={6}
                      placeholder="Enter minimum 6 characters"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full pl-9 pr-10 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none"
                    >
                      {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>

                  {/* Password Strength Indicator */}
                  {newPassword && (
                    <div className="mt-2 space-y-1">
                      <div className="flex items-center justify-between text-[11px] font-medium text-slate-600">
                        <span>Password Strength:</span>
                        <span className={`font-semibold ${strength.score === 3 ? 'text-emerald-600' : strength.score === 2 ? 'text-amber-600' : 'text-rose-600'}`}>
                          {strength.label}
                        </span>
                      </div>
                      <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden flex gap-1">
                        <div className={`h-full rounded-full flex-1 ${strength.score >= 1 ? strength.color : 'bg-slate-200'}`} />
                        <div className={`h-full rounded-full flex-1 ${strength.score >= 2 ? strength.color : 'bg-slate-200'}`} />
                        <div className={`h-full rounded-full flex-1 ${strength.score >= 3 ? strength.color : 'bg-slate-200'}`} />
                      </div>
                    </div>
                  )}
                </div>

                {/* Confirm Password Field */}
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Confirm Permanent Password <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Lock className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      required
                      minLength={6}
                      placeholder="Re-enter your new password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full pl-9 pr-10 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none"
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                {/* Submit Action */}
                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full flex justify-center items-center py-2.5 px-4 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 shadow-md shadow-indigo-100 disabled:opacity-50 transition"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        Activating Account...
                      </>
                    ) : (
                      'Activate Account & Log In'
                    )}
                  </button>
                </div>

              </form>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default ActivateAccount;
