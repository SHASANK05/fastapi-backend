import React, { useState, useEffect } from 'react';
import API from './api';
import { 
  Users, Calendar, Clock, DollarSign, LogOut, Download, Briefcase, UserCheck 
} from 'lucide-react';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [userRole, setUserRole] = useState(localStorage.getItem('role') || '');
  const [email, setEmail] = useState('admin@hrms.com');
  const [password, setPassword] = useState('Admin@12345');
  const [summary, setSummary] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [punchMsg, setPunchMsg] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');
    try {
      // Use URLSearchParams to match OAuth2PasswordRequestForm
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const res = await API.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      const { access_token, role } = res.data;
      localStorage.setItem('token', access_token);
      localStorage.setItem('role', role || 'ADMIN');
      setToken(access_token);
      setUserRole(role || 'ADMIN');
    } catch (err) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    setToken('');
    setUserRole('');
    setSummary(null);
  };

  useEffect(() => {
    if (token && (userRole === 'ADMIN' || userRole === 'HR')) {
      API.get('/dashboard/summary')
        .then((res) => setSummary(res.data))
        .catch((err) => console.error(err));
    }
  }, [token, userRole]);

  const handleCheckIn = async () => {
    try {
      const res = await API.post('/attendance/check-in');
      setPunchMsg(`Checked in successfully at ${res.data.check_in}`);
    } catch (err) {
      setPunchMsg(err.response?.data?.detail || 'Check-in failed');
    }
  };

  const handleCheckOut = async () => {
    try {
      const res = await API.post('/attendance/check-out');
      setPunchMsg(`Checked out successfully! Total Hours: ${res.data.total_hours}`);
    } catch (err) {
      setPunchMsg(err.response?.data?.detail || 'Check-out failed');
    }
  };

  const downloadReport = (type) => {
    window.open(`http://127.0.0.1:8000/api/reports/${type}/csv`, '_blank');
  };

  if (!token) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-100 p-4">
        <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 border border-slate-200">
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold text-slate-800">HRMS Portal</h1>
            <p className="text-sm text-slate-500">Sign in to access your organization dashboard</p>
          </div>

          {errorMsg && (
            <div className="mb-4 p-3 bg-red-50 border-l-4 border-red-500 text-red-700 text-sm">
              {errorMsg}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition duration-150 text-sm"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 border-t pt-4 text-xs text-slate-500 text-center">
            Demo: <span className="font-mono">admin@hrms.com</span> / <span className="font-mono">Admin@12345</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col justify-between p-4">
        <div>
          <div className="text-xl font-bold text-white mb-8 px-2 flex items-center gap-2">
            <Briefcase className="text-blue-400" /> HRMS Core
          </div>
          <nav className="space-y-1">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition ${
                activeTab === 'dashboard' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('attendance')}
              className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition ${
                activeTab === 'attendance' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800'
              }`}
            >
              Daily Attendance
            </button>
            {(userRole === 'ADMIN' || userRole === 'HR') && (
              <button
                onClick={() => setActiveTab('reports')}
                className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition ${
                  activeTab === 'reports' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800'
                }`}
              >
                Export Reports
              </button>
            )}
          </nav>
        </div>

        <div className="border-t border-slate-800 pt-4 px-2">
          <div className="text-xs text-slate-400 mb-1">Logged in as</div>
          <div className="text-sm font-semibold text-white uppercase tracking-wider">{userRole}</div>
          <button
            onClick={handleLogout}
            className="mt-4 flex items-center gap-2 text-xs text-red-400 hover:text-red-300 transition"
          >
            <LogOut size={14} /> Sign Out
          </button>
        </div>
      </aside>

      <main className="flex-1 p-8 overflow-y-auto">
        <header className="flex justify-between items-center mb-8 border-b pb-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 capitalize">{activeTab}</h1>
            <p className="text-sm text-slate-500">HRMS Management & Self-Service Portal</p>
          </div>
        </header>

        {activeTab === 'dashboard' && (
          <div>
            {(userRole === 'ADMIN' || userRole === 'HR') ? (
              <div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                  <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                    <div className="p-3 bg-blue-50 text-blue-600 rounded-lg"><Users size={24} /></div>
                    <div>
                      <div className="text-xs text-slate-500 font-medium">Total Headcount</div>
                      <div className="text-2xl font-bold text-slate-800">{summary?.employees?.total ?? 0}</div>
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                    <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg"><UserCheck size={24} /></div>
                    <div>
                      <div className="text-xs text-slate-500 font-medium">Present Today</div>
                      <div className="text-2xl font-bold text-slate-800">{summary?.today_attendance?.present ?? 0}</div>
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                    <div className="p-3 bg-amber-50 text-amber-600 rounded-lg"><Calendar size={24} /></div>
                    <div>
                      <div className="text-xs text-slate-500 font-medium">Pending Leaves</div>
                      <div className="text-2xl font-bold text-slate-800">{summary?.leaves?.pending_approval ?? 0}</div>
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                    <div className="p-3 bg-purple-50 text-purple-600 rounded-lg"><DollarSign size={24} /></div>
                    <div>
                      <div className="text-xs text-slate-500 font-medium">Payroll (Oct 2026)</div>
                      <div className="text-2xl font-bold text-slate-800">
                        ₹{(summary?.payroll?.total_disbursed ?? 0).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                  <h3 className="text-base font-semibold text-slate-800 mb-2">Administrative Actions</h3>
                  <p className="text-sm text-slate-500 mb-4">Quick shortcuts for daily administrative tasks</p>
                  <div className="flex gap-4">
                    <button 
                      onClick={() => setActiveTab('attendance')} 
                      className="px-4 py-2 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-md text-sm font-medium transition"
                    >
                      Record Attendance
                    </button>
                    <button 
                      onClick={() => downloadReport('payroll?month=10&year=2026')} 
                      className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md text-sm font-medium transition flex items-center gap-2"
                    >
                      <Download size={16} /> Export Payroll CSV
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <h2 className="text-lg font-bold text-slate-800 mb-2">Welcome to Your Employee Portal</h2>
                <p className="text-sm text-slate-500 mb-4">Use the sidebar to mark your attendance and view records.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'attendance' && (
          <div className="max-w-xl bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-lg font-bold text-slate-800 mb-1">Time & Attendance Punch</h3>
            <p className="text-sm text-slate-500 mb-6">Log your official daily check-in and check-out</p>

            {punchMsg && (
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md text-sm text-blue-800">
                {punchMsg}
              </div>
            )}

            <div className="flex gap-4">
              <button
                onClick={handleCheckIn}
                className="flex-1 flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-3 rounded-lg shadow-sm transition"
              >
                <Clock size={18} /> Clock In
              </button>
              <button
                onClick={handleCheckOut}
                className="flex-1 flex items-center justify-center gap-2 bg-rose-600 hover:bg-rose-700 text-white font-medium py-3 rounded-lg shadow-sm transition"
              >
                <Clock size={18} /> Clock Out
              </button>
            </div>
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h4 className="font-semibold text-slate-800 mb-1">Attendance Register</h4>
              <p className="text-xs text-slate-500 mb-4">Export full organization punch logs</p>
              <button
                onClick={() => downloadReport('attendance')}
                className="w-full py-2 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-sm font-medium flex items-center justify-center gap-2"
              >
                <Download size={14} /> Download CSV
              </button>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h4 className="font-semibold text-slate-800 mb-1">Leaves Ledger</h4>
              <p className="text-xs text-slate-500 mb-4">Export approved and pending leave records</p>
              <button
                onClick={() => downloadReport('leaves')}
                className="w-full py-2 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-sm font-medium flex items-center justify-center gap-2"
              >
                <Download size={14} /> Download CSV
              </button>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h4 className="font-semibold text-slate-800 mb-1">Payroll Summary</h4>
              <p className="text-xs text-slate-500 mb-4">Export salary sheets for current month</p>
              <button
                onClick={() => downloadReport('payroll?month=10&year=2026')}
                className="w-full py-2 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-sm font-medium flex items-center justify-center gap-2"
              >
                <Download size={14} /> Download CSV
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
