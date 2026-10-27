import React, { useState, useEffect } from 'react';
import { 
  Users, AlertTriangle, ShieldCheck, Activity, 
  RefreshCw, TrendingUp, Building2, LogOut, Lock,
  CalendarCheck, CheckCircle2, XCircle, Search, UserPlus, X,
  FileSpreadsheet, Printer, History, ClipboardCheck, Clock, Save, Layers, ChevronRight, User, Shield, UploadCloud, FileText, Check
} from 'lucide-react';
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid 
} from 'recharts';
import { 
  authService, 
  analyticsService, 
  employeeService, 
  departmentService, 
  leaveService,
  auditService,
  retentionService,
  datasetService
} from './services/api';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!authService.getToken());
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [email, setEmail] = useState('admin@workforce.ai');
  const [password, setPassword] = useState('AdminPassword123');
  const [loginError, setLoginError] = useState('');

  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [exportingCsv, setExportingCsv] = useState(false);
  const [evaluatingId, setEvaluatingId] = useState(null);

  const [analytics, setAnalytics] = useState(null);
  const [deptRisk, setDeptRisk] = useState([]);
  const [highRiskList, setHighRiskList] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [leaves, setLeaves] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  // Onboarding Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const [newEmp, setNewEmp] = useState({
    employee_code: '',
    first_name: '',
    last_name: '',
    email: '',
    password: 'Password@123',
    department_id: '',
    designation: '',
    date_of_joining: new Date().toISOString().split('T')[0],
    monthly_salary: '',
    phone: '',
    role: 'EMPLOYEE'
  });

  // Batch CSV Import Modal State
  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false);
  const [csvFile, setCsvFile] = useState(null);
  const [uploadingCsv, setUploadingCsv] = useState(false);
  const [csvUploadResult, setCsvUploadResult] = useState(null);
  const [csvError, setCsvError] = useState('');

  // Employee Leave Application Form (Self-Service)
  const [applyingLeave, setApplyingLeave] = useState(false);
  const [leaveForm, setLeaveForm] = useState({
    leave_type: 'CASUAL',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    reason: 'Personal time off'
  });

  // Retention Case Drawer State
  const [selectedCaseEmp, setSelectedCaseEmp] = useState(null);
  const [caseDiagnostics, setCaseDiagnostics] = useState(null);
  const [loadingCase, setLoadingCase] = useState(false);
  const [savingCase, setSavingCase] = useState(false);
  const [caseForm, setCaseForm] = useState({
    status: 'OPEN',
    priority: 'HIGH',
    action_plan: '1-on-1 Mentorship & Workload Adjustment',
    notes: ''
  });

  // Department Deep-Dive Modal State
  const [selectedDeptCode, setSelectedDeptCode] = useState(null);
  const [deptDeepDive, setDeptDeepDive] = useState(null);
  const [loadingDept, setLoadingDept] = useState(false);

  const loadUserProfile = async () => {
    try {
      const profile = await authService.getMe();
      setCurrentUser(profile);
      if (profile.role === 'EMPLOYEE') {
        setActiveTab('portal');
      } else {
        setActiveTab('dashboard');
      }
    } catch (err) {
      console.error('Failed to load profile:', err);
      handleLogout();
    }
  };

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [analyticsData, deptData, highRiskData] = await Promise.all([
        analyticsService.getAnalytics(),
        analyticsService.getDepartmentRisk(),
        analyticsService.getHighRiskEmployees(),
      ]);
      setAnalytics(analyticsData);
      setDeptRisk(deptData);
      setHighRiskList(highRiskData);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchEmployees = async () => {
    try {
      const data = await employeeService.getAll();
      setEmployees(data);
    } catch (err) {
      console.error('Failed to load employees:', err);
    }
  };

  const fetchDepartments = async () => {
    try {
      const data = await departmentService.getAll();
      setDepartments(data);
      if (data.length > 0 && !newEmp.department_id) {
        setNewEmp(prev => ({ ...prev, department_id: data[0].id }));
      }
    } catch (err) {
      console.error('Failed to load departments:', err);
    }
  };

  const fetchLeaves = async () => {
    try {
      const data = await leaveService.getAll();
      setLeaves(data);
    } catch (err) {
      console.error('Failed to load leaves:', err);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const data = await auditService.getAll(50);
      setAuditLogs(data);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      loadUserProfile();
      fetchDepartments();
      fetchLeaves();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (currentUser) {
      if (currentUser.role === 'ADMIN' || currentUser.role === 'HR') {
        fetchDashboardData();
        fetchEmployees();
        fetchAuditLogs();
      } else if (currentUser.role === 'MANAGER') {
        fetchDashboardData();
        fetchEmployees();
      }
    }
  }, [currentUser]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    try {
      await authService.login(email, password);
      setIsAuthenticated(true);
    } catch (err) {
      setLoginError(err.response?.data?.detail || 'Invalid login credentials');
    }
  };

  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(false);
    setCurrentUser(null);
  };

  const handleBulkRecompute = async () => {
    try {
      setRefreshing(true);
      await analyticsService.triggerBulkPredict();
      await fetchDashboardData();
      await fetchAuditLogs();
      if (selectedDeptCode) {
        handleOpenDeptDeepDive(selectedDeptCode);
      }
    } catch (err) {
      console.error('Recalculation error:', err);
    } finally {
      setRefreshing(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      setExportingCsv(true);
      await analyticsService.downloadCSV();
    } catch (err) {
      console.error('CSV Export failed:', err);
    } finally {
      setExportingCsv(false);
    }
  };

  const handlePrintPDF = () => {
    window.print();
  };

  const handleIndividualPredict = async (empId) => {
    try {
      setEvaluatingId(empId);
      await analyticsService.predictIndividual(empId);
      await fetchDashboardData();
      await fetchAuditLogs();
      if (selectedDeptCode) {
        handleOpenDeptDeepDive(selectedDeptCode);
      }
    } catch (err) {
      console.error('Error scoring employee:', err);
    } finally {
      setEvaluatingId(null);
    }
  };

  const handleOpenCaseDrawer = async (empId) => {
    setSelectedCaseEmp(empId);
    setLoadingCase(true);
    try {
      const diag = await retentionService.getDiagnostics(empId);
      setCaseDiagnostics(diag);
      if (diag.case) {
        setCaseForm({
          status: diag.case.status,
          priority: diag.case.priority,
          action_plan: diag.case.action_plan || '1-on-1 Mentorship & Workload Adjustment',
          notes: diag.case.notes || ''
        });
      } else {
        setCaseForm({
          status: 'OPEN',
          priority: 'HIGH',
          action_plan: '1-on-1 Mentorship & Workload Adjustment',
          notes: ''
        });
      }
    } catch (err) {
      console.error('Failed to load diagnostics:', err);
    } finally {
      setLoadingCase(false);
    }
  };

  const handleSaveRetentionCase = async (e) => {
    e.preventDefault();
    if (!selectedCaseEmp) return;
    setSavingCase(true);
    try {
      await retentionService.saveCase({
        employee_id: selectedCaseEmp,
        ...caseForm
      });
      await fetchAuditLogs();
      const updatedDiag = await retentionService.getDiagnostics(selectedCaseEmp);
      setCaseDiagnostics(updatedDiag);
      alert('Retention case intervention saved successfully!');
    } catch (err) {
      console.error('Failed to save retention case:', err);
      alert('Error updating case.');
    } finally {
      setSavingCase(false);
    }
  };

  const handleOpenDeptDeepDive = async (deptCode) => {
    if (!deptCode) return;
    setSelectedDeptCode(deptCode);
    setLoadingDept(true);
    try {
      const data = await departmentService.getDeepDive(deptCode);
      setDeptDeepDive(data);
    } catch (err) {
      console.error('Failed to load department deep-dive:', err);
    } finally {
      setLoadingDept(false);
    }
  };

  const handleLeaveStatusUpdate = async (leaveId, status) => {
    try {
      await leaveService.updateStatus(leaveId, status);
      await fetchLeaves();
      await fetchDashboardData();
      await fetchAuditLogs();
    } catch (err) {
      console.error('Failed to update leave status:', err);
    }
  };

  const handleApplyLeave = async (e) => {
    e.preventDefault();
    if (!currentUser?.employee_id) {
      alert('No employee profile associated with this account to apply leave.');
      return;
    }
    setApplyingLeave(true);
    try {
      const s = new Date(leaveForm.start_date);
      const en = new Date(leaveForm.end_date);
      const totalDays = Math.max(1, Math.round((en - s) / (1000 * 60 * 60 * 24)) + 1);

      await leaveService.create({
        employee_id: currentUser.employee_id,
        leave_type: leaveForm.leave_type,
        start_date: leaveForm.start_date,
        end_date: leaveForm.end_date,
        total_days: totalDays,
        reason: leaveForm.reason
      });
      alert('Leave application submitted successfully!');
      await fetchLeaves();
    } catch (err) {
      console.error('Failed to apply leave:', err);
      alert(err.response?.data?.detail || 'Error submitting leave application');
    } finally {
      setApplyingLeave(false);
    }
  };

  const handleCreateEmployee = async (e) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);
    try {
      const payload = {
        ...newEmp,
        department_id: parseInt(newEmp.department_id),
        monthly_salary: parseFloat(newEmp.monthly_salary)
      };
      await employeeService.create(payload);
      setIsModalOpen(false);
      setNewEmp({
        employee_code: '',
        first_name: '',
        last_name: '',
        email: '',
        password: 'Password@123',
        department_id: departments[0]?.id || '',
        designation: '',
        date_of_joining: new Date().toISOString().split('T')[0],
        monthly_salary: '',
        phone: '',
        role: 'EMPLOYEE'
      });
      await fetchEmployees();
      await fetchAuditLogs();
      await handleBulkRecompute();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to onboard employee');
    } finally {
      setSubmitting(false);
    }
  };

  const handleUploadCSV = async (e) => {
    e.preventDefault();
    if (!csvFile) {
      setCsvError('Please select a .csv file to upload.');
      return;
    }
    setCsvError('');
    setUploadingCsv(true);
    try {
      const result = await datasetService.uploadCSV(csvFile);
      setCsvUploadResult(result);
      await fetchEmployees();
      await fetchDashboardData();
      await fetchAuditLogs();
    } catch (err) {
      setCsvError(err.response?.data?.detail || 'Failed to parse and upload CSV dataset');
    } finally {
      setUploadingCsv(false);
    }
  };

  const downloadSampleTemplate = () => {
    const csvContent = "data:text/csv;charset=utf-8," + 
      "employee_code,first_name,last_name,email,department_code,designation,monthly_salary,date_of_joining\n" +
      "EMP101,Suresh,Raina,suresh.raina@workforce.ai,ENG,Staff Engineer,115000,2022-04-15\n" +
      "EMP102,Deepa,Reddy,deepa.reddy@workforce.ai,HR,Senior HR Partner,72000,2023-08-10\n" +
      "EMP103,Manoj,Tiwari,manoj.tiwari@workforce.ai,OPS,Operations Specialist,52000,2024-01-20\n";
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "employee_import_template.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="bg-slate-800 border border-slate-700 w-full max-w-md p-8 rounded-2xl shadow-2xl">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-indigo-600/20 text-indigo-400 rounded-xl">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-wide">WorkForce AI Pro</h1>
              <p className="text-xs text-slate-400">Enterprise HR Intelligence Login</p>
            </div>
          </div>

          {loginError && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg">
              {loginError}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Corporate Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>
            <button
              type="submit"
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 rounded-lg transition-all text-sm flex items-center justify-center gap-2 mt-2"
            >
              <Lock className="w-4 h-4" /> Sign In
            </button>
          </form>

          <div className="mt-6 pt-4 border-t border-slate-700/60 text-[11px] text-slate-400">
            <p className="font-semibold text-slate-300 mb-1">Demo Accounts:</p>
            <div className="space-y-0.5">
              <p><strong className="text-indigo-400">ADMIN:</strong> admin@workforce.ai / AdminPassword123</p>
              <p><strong className="text-emerald-400">EMPLOYEE:</strong> aarav@workforce.ai / Password@123</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const role = currentUser?.role || 'EMPLOYEE';
  const isAdminOrHR = role === 'ADMIN' || role === 'HR';
  const isManager = role === 'MANAGER';

  const pieData = analytics ? [
    { name: 'Low Risk', value: analytics.distribution.low_risk, color: '#10b981' },
    { name: 'Moderate Risk', value: analytics.distribution.moderate_risk, color: '#f59e0b' },
    { name: 'High Risk', value: analytics.distribution.high_risk, color: '#ef4444' },
  ] : [];

  const filteredEmployees = employees.filter(emp => 
    `${emp.first_name} ${emp.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
    emp.employee_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    emp.designation.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const myLeaves = leaves.filter(l => l.employee_id === currentUser?.employee_id);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-4 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-30 print:hidden">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg border border-indigo-500/20">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white leading-tight">WorkForce AI Pro</h1>
            <p className="text-xs text-slate-400">Attrition Intelligence & Operational Risk Engine</p>
          </div>
        </div>

        <div className="flex items-center bg-slate-800/80 p-1 rounded-xl border border-slate-700/60">
          {(isAdminOrHR || isManager) && (
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'dashboard' 
                  ? 'bg-indigo-600 text-white shadow-sm' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Activity className="w-3.5 h-3.5" /> Intelligence Dashboard
            </button>
          )}

          {(isAdminOrHR || isManager) && (
            <button
              onClick={() => setActiveTab('employees')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'employees' 
                  ? 'bg-indigo-600 text-white shadow-sm' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Users className="w-3.5 h-3.5" /> Employee Directory
            </button>
          )}

          <button
            onClick={() => setActiveTab('leaves')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'leaves' 
                ? 'bg-indigo-600 text-white shadow-sm' 
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <CalendarCheck className="w-3.5 h-3.5" /> {isAdminOrHR ? 'Leave Approvals' : 'Company Leaves'}
          </button>

          <button
            onClick={() => setActiveTab('portal')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'portal' 
                ? 'bg-indigo-600 text-white shadow-sm' 
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <User className="w-3.5 h-3.5" /> My Portal
          </button>

          {isAdminOrHR && (
            <button
              onClick={() => {
                setActiveTab('audit');
                fetchAuditLogs();
              }}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'audit' 
                  ? 'bg-indigo-600 text-white shadow-sm' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <History className="w-3.5 h-3.5" /> Audit Trail
            </button>
          )}
        </div>

        <div className="flex items-center gap-3">
          {currentUser && (
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/80 text-xs">
              <Shield className="w-3.5 h-3.5 text-indigo-400" />
              <span className="font-semibold text-slate-200">{currentUser.full_name}</span>
              <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                {currentUser.role}
              </span>
            </div>
          )}

          {activeTab === 'dashboard' && isAdminOrHR && (
            <>
              <button
                onClick={handleExportCSV}
                disabled={exportingCsv}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 rounded-lg transition-all cursor-pointer"
                title="Download CSV"
              >
                <FileSpreadsheet className="w-3.5 h-3.5" /> {exportingCsv ? '...' : 'CSV'}
              </button>
              <button
                onClick={handlePrintPDF}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 rounded-lg transition-all cursor-pointer"
                title="Print or Save as PDF"
              >
                <Printer className="w-3.5 h-3.5" /> PDF
              </button>
              <button
                onClick={handleBulkRecompute}
                disabled={refreshing}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded-lg transition-all disabled:opacity-50 cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
                {refreshing ? 'Evaluating...' : 'Re-run'}
              </button>
            </>
          )}

          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-all border border-slate-700 cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" /> Logout
          </button>
        </div>
      </header>

      <main className="flex-1 p-6 max-w-7xl w-full mx-auto space-y-6">
        {activeTab === 'dashboard' && (isAdminOrHR || isManager) && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-medium uppercase tracking-wider">Workforce Evaluated</span>
                  <Users className="w-4 h-4 text-indigo-400" />
                </div>
                <div className="text-2xl font-bold text-white">{analytics?.total_workforce_evaluated ?? 0}</div>
                <p className="text-xs text-slate-500 mt-1">Active talent scored</p>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <div className="flex items-center justify-between text-emerald-400 mb-2">
                  <span className="text-xs font-medium uppercase tracking-wider">Low Risk / Stable</span>
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <div className="text-2xl font-bold text-emerald-400">{analytics?.distribution.low_risk ?? 0}</div>
                <p className="text-xs text-slate-500 mt-1">High retention stability</p>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <div className="flex items-center justify-between text-amber-400 mb-2">
                  <span className="text-xs font-medium uppercase tracking-wider">Moderate Watch</span>
                  <TrendingUp className="w-4 h-4" />
                </div>
                <div className="text-2xl font-bold text-amber-400">{analytics?.distribution.moderate_risk ?? 0}</div>
                <p className="text-xs text-slate-500 mt-1">Emerging risk factors</p>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <div className="flex items-center justify-between text-rose-400 mb-2">
                  <span className="text-xs font-medium uppercase tracking-wider">Immediate Intervention</span>
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <div className="text-2xl font-bold text-rose-400">{analytics?.distribution.high_risk ?? 0}</div>
                <p className="text-xs text-slate-500 mt-1">Risk score &ge; 65%</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex flex-col">
                <h2 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-indigo-400" /> Risk Distribution
                </h2>
                <div className="h-56 w-full flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={55}
                        outerRadius={80}
                        paddingAngle={4}
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} 
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-around text-xs text-slate-400 mt-2 border-t border-slate-800/80 pt-3">
                  <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Low</div>
                  <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Moderate</div>
                  <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> High</div>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl lg:col-span-2 flex flex-col">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-indigo-400" /> Department Risk Index
                    </h2>
                    <p className="text-[11px] text-slate-400 mt-0.5">Click any bar or department button below to open deep-dive analysis</p>
                  </div>
                </div>
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart 
                      data={deptRisk} 
                      margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="department_code" stroke="#64748b" fontSize={11} />
                      <YAxis stroke="#64748b" fontSize={11} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} 
                      />
                      <Bar 
                        dataKey="average_risk_score" 
                        name="Avg Risk Score (%)" 
                        radius={[4, 4, 0, 0]}
                      >
                        {deptRisk.map((entry, idx) => (
                          <Cell 
                            key={`dept-cell-${idx}`} 
                            fill="#6366f1"
                            cursor="pointer"
                            onClick={() => handleOpenDeptDeepDive(entry.department_code)}
                            className="hover:fill-indigo-400 transition-colors"
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                
                <div className="flex flex-wrap items-center justify-center gap-2 mt-3 pt-3 border-t border-slate-800/80">
                  {deptRisk.map((d) => (
                    <button
                      key={d.department_code}
                      onClick={() => handleOpenDeptDeepDive(d.department_code)}
                      className="flex items-center gap-1.5 px-3 py-1 text-xs font-medium bg-slate-800/90 hover:bg-indigo-600 hover:text-white text-slate-300 border border-slate-700/80 rounded-lg transition-all cursor-pointer shadow-sm"
                    >
                      <span>{d.department_code}</span>
                      <span className="font-mono text-indigo-300">({d.average_risk_score}%)</span>
                      <ChevronRight className="w-3 h-3 text-slate-400" />
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
              <div className="p-5 border-b border-slate-800 flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-rose-400" /> Urgent Retention Intervention List
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">Employees scoring above 65% probability of exit</p>
                </div>
                <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  {highRiskList.length} Flagged
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/40 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold">
                    <tr>
                      <th className="py-3 px-4">Employee</th>
                      <th className="py-3 px-4">Code</th>
                      <th className="py-3 px-4">Designation</th>
                      <th className="py-3 px-4">Risk Probability</th>
                      <th className="py-3 px-4">Primary Risk Driver</th>
                      <th className="py-3 px-4 text-right print:hidden">Intervention</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    {highRiskList.map((emp) => (
                      <tr key={emp.employee_id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3 px-4 font-medium text-white">{emp.full_name}</td>
                        <td className="py-3 px-4 text-slate-400 font-mono">{emp.employee_code}</td>
                        <td className="py-3 px-4 text-slate-400">{emp.designation}</td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                            {emp.risk_score}%
                          </span>
                        </td>
                        <td className="py-3 px-4 text-amber-300">{emp.top_contributing_factor}</td>
                        <td className="py-3 px-4 text-right print:hidden">
                          <div className="flex items-center justify-end gap-2">
                            {isAdminOrHR && (
                              <button 
                                onClick={() => handleOpenCaseDrawer(emp.employee_id)}
                                className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded transition-all text-xs flex items-center gap-1 cursor-pointer shadow-sm"
                              >
                                <ClipboardCheck className="w-3.5 h-3.5" /> Review Case
                              </button>
                            )}
                            <button 
                              onClick={() => handleIndividualPredict(emp.employee_id)}
                              disabled={evaluatingId === emp.employee_id}
                              className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded transition-all text-xs cursor-pointer"
                              title="Recalculate score"
                            >
                              {evaluatingId === emp.employee_id ? '...' : <RefreshCw className="w-3 h-3" />}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {activeTab === 'employees' && (isAdminOrHR || isManager) && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden space-y-4 p-5">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Users className="w-5 h-5 text-indigo-400" /> Organization Directory
                </h2>
                <p className="text-xs text-slate-400">Manage employee records, batch import datasets, and score talent</p>
              </div>
              <div className="flex items-center gap-3 w-full sm:w-auto">
                <div className="relative flex-1 sm:w-64">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="Search staff, code, role..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                {isAdminOrHR && (
                  <>
                    <button
                      onClick={() => {
                        setCsvFile(null);
                        setCsvUploadResult(null);
                        setCsvError('');
                        setIsCsvModalOpen(true);
                      }}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 font-semibold rounded-lg text-xs transition-all whitespace-nowrap shadow-sm cursor-pointer"
                    >
                      <UploadCloud className="w-4 h-4" /> Import CSV
                    </button>
                    <button
                      onClick={() => setIsModalOpen(true)}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg text-xs transition-all whitespace-nowrap shadow-sm cursor-pointer"
                    >
                      <UserPlus className="w-4 h-4" /> Add Employee
                    </button>
                  </>
                )}
              </div>
            </div>

            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/60 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="py-3 px-4">Code</th>
                    <th className="py-3 px-4">Full Name</th>
                    <th className="py-3 px-4">Designation</th>
                    <th className="py-3 px-4">Joining Date</th>
                    {isAdminOrHR && <th className="py-3 px-4">Monthly Salary</th>}
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Model Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {filteredEmployees.map((emp) => (
                    <tr key={emp.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 font-mono text-slate-400">{emp.employee_code}</td>
                      <td className="py-3 px-4 font-medium text-white">{emp.first_name} {emp.last_name}</td>
                      <td className="py-3 px-4 text-slate-300">{emp.designation}</td>
                      <td className="py-3 px-4 text-slate-400">{emp.date_of_joining}</td>
                      {isAdminOrHR && (
                        <td className="py-3 px-4 font-mono text-slate-300">₹{emp.monthly_salary?.toLocaleString()}</td>
                      )}
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          ACTIVE
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleIndividualPredict(emp.id)}
                          disabled={evaluatingId === emp.id}
                          className="px-2.5 py-1 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded text-xs transition-all disabled:opacity-50 cursor-pointer"
                        >
                          {evaluatingId === emp.id ? 'Scoring...' : 'Run Prediction'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'leaves' && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden space-y-4 p-5">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <CalendarCheck className="w-5 h-5 text-indigo-400" /> Organization Leave Management
              </h2>
              <p className="text-xs text-slate-400">Review leave requests; approved durations actively feed the attrition engine</p>
            </div>

            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/60 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="py-3 px-4">Leave ID</th>
                    <th className="py-3 px-4">Emp ID</th>
                    <th className="py-3 px-4">Leave Type</th>
                    <th className="py-3 px-4">Duration</th>
                    <th className="py-3 px-4">Total Days</th>
                    <th className="py-3 px-4">Status</th>
                    {isAdminOrHR && <th className="py-3 px-4 text-right">Approvals</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {leaves.map((lv) => (
                    <tr key={lv.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 font-mono text-slate-400">#{lv.id}</td>
                      <td className="py-3 px-4 font-mono text-indigo-300">EMP-{lv.employee_id}</td>
                      <td className="py-3 px-4 font-medium text-white">{lv.leave_type}</td>
                      <td className="py-3 px-4 text-slate-400">{lv.start_date} to {lv.end_date}</td>
                      <td className="py-3 px-4 font-semibold text-slate-200">{lv.total_days} days</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                          lv.status === 'APPROVED' 
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                            : lv.status === 'PENDING'
                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        }`}>
                          {lv.status}
                        </span>
                      </td>
                      {isAdminOrHR && (
                        <td className="py-3 px-4 text-right">
                          {lv.status === 'PENDING' ? (
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => handleLeaveStatusUpdate(lv.id, 'APPROVED')}
                                className="p-1 text-emerald-400 hover:bg-emerald-500/20 rounded border border-emerald-500/30 transition-all cursor-pointer"
                                title="Approve"
                              >
                                <CheckCircle2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleLeaveStatusUpdate(lv.id, 'REJECTED')}
                                className="p-1 text-rose-400 hover:bg-rose-500/20 rounded border border-rose-500/30 transition-all cursor-pointer"
                                title="Reject"
                              >
                                <XCircle className="w-4 h-4" />
                              </button>
                            </div>
                          ) : (
                            <span className="text-slate-500 text-[11px]">Processed</span>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'portal' && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-2xl border border-indigo-500/20">
                  <User className="w-8 h-8" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">{currentUser?.full_name}</h2>
                  <p className="text-xs text-slate-400">{currentUser?.designation} &bull; {currentUser?.department_name}</p>
                  <p className="text-xs font-mono text-indigo-400 mt-0.5">{currentUser?.employee_code || 'CODE: ADMIN'}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Retention Profile: Stable
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                  <CalendarCheck className="w-4 h-4 text-indigo-400" /> Submit Leave Request
                </h3>
                <form onSubmit={handleApplyLeave} className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Leave Category</label>
                    <select
                      value={leaveForm.leave_type}
                      onChange={(e) => setLeaveForm({ ...leaveForm, leave_type: e.target.value })}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                    >
                      <option value="CASUAL">Casual Leave</option>
                      <option value="SICK">Sick Leave</option>
                      <option value="EMERGENCY">Emergency Leave</option>
                      <option value="UNPAID">Unpaid Leave</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">From Date</label>
                      <input
                        type="date"
                        required
                        value={leaveForm.start_date}
                        onChange={(e) => setLeaveForm({ ...leaveForm, start_date: e.target.value })}
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">To Date</label>
                      <input
                        type="date"
                        required
                        value={leaveForm.end_date}
                        onChange={(e) => setLeaveForm({ ...leaveForm, end_date: e.target.value })}
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Purpose / Reason</label>
                    <textarea
                      rows="2"
                      required
                      placeholder="Brief note on leave purpose..."
                      value={leaveForm.reason}
                      onChange={(e) => setLeaveForm({ ...leaveForm, reason: e.target.value })}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={applyingLeave}
                    className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-lg transition-all disabled:opacity-50 cursor-pointer shadow-sm"
                  >
                    {applyingLeave ? 'Submitting...' : 'Apply for Leave'}
                  </button>
                </form>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 lg:col-span-2 flex flex-col">
                <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-indigo-400" /> My Leave Records & Approval Status
                </h3>
                <div className="overflow-x-auto flex-1 rounded-lg border border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-800/60 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold">
                      <tr>
                        <th className="py-2.5 px-3">Type</th>
                        <th className="py-2.5 px-3">Date Range</th>
                        <th className="py-2.5 px-3">Days</th>
                        <th className="py-2.5 px-3">Reason</th>
                        <th className="py-2.5 px-3 text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-slate-300">
                      {myLeaves.length === 0 ? (
                        <tr>
                          <td colSpan="5" className="py-8 text-center text-slate-500">
                            No leave applications submitted yet.
                          </td>
                        </tr>
                      ) : (
                        myLeaves.map((l) => (
                          <tr key={l.id} className="hover:bg-slate-800/30 transition-colors">
                            <td className="py-2.5 px-3 font-medium text-white">{l.leave_type}</td>
                            <td className="py-2.5 px-3 text-slate-400">{l.start_date} to {l.end_date}</td>
                            <td className="py-2.5 px-3 font-semibold">{l.total_days} days</td>
                            <td className="py-2.5 px-3 text-slate-400 text-[11px]">{l.reason || '—'}</td>
                            <td className="py-2.5 px-3 text-right">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                                l.status === 'APPROVED'
                                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                  : l.status === 'PENDING'
                                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                                  : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                              }`}>
                                {l.status}
                              </span>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'audit' && isAdminOrHR && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden space-y-4 p-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <History className="w-5 h-5 text-indigo-400" /> Operational Audit Trail & Event Logs
                </h2>
                <p className="text-xs text-slate-400">Chronological history of security, HR lifecycle actions, and system recalculations</p>
              </div>
              <button
                onClick={fetchAuditLogs}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-lg text-xs font-semibold transition-all cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Refresh Logs
              </button>
            </div>

            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/60 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="py-3 px-4">Timestamp</th>
                    <th className="py-3 px-4">Action</th>
                    <th className="py-3 px-4">Target Entity</th>
                    <th className="py-3 px-4">Performed By</th>
                    <th className="py-3 px-4">Event Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {auditLogs.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="py-8 text-center text-slate-500">
                        No activity records logged yet.
                      </td>
                    </tr>
                  ) : (
                    auditLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3 px-4 font-mono text-slate-400">
                          {new Date(log.timestamp).toLocaleString()}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                            log.action.includes('CREATED') || log.action.includes('OPENED') || log.action.includes('IMPORTED')
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                              : log.action.includes('UPDATED')
                              ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                              : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                          }`}>
                            {log.action}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-300">
                          {log.entity_type} {log.entity_id ? `(#${log.entity_id})` : ''}
                        </td>
                        <td className="py-3 px-4 text-indigo-300 font-medium">{log.performed_by}</td>
                        <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                          {log.details || '—'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Batch CSV Import Modal */}
      {isCsvModalOpen && isAdminOrHR && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-lg rounded-2xl shadow-2xl p-6 relative">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
                  <UploadCloud className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Batch Employee Dataset Import</h3>
                  <p className="text-xs text-slate-400">Upload CSV file to onboard talent and trigger predictive AI scoring</p>
                </div>
              </div>
              <button 
                onClick={() => setIsCsvModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-all cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {csvError && (
              <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs rounded-lg">
                {csvError}
              </div>
            )}

            {!csvUploadResult ? (
              <form onSubmit={handleUploadCSV} className="space-y-4">
                <div className="border-2 border-dashed border-slate-700 hover:border-indigo-500/60 rounded-xl p-6 text-center transition-all bg-slate-950/40">
                  <input
                    type="file"
                    accept=".csv"
                    id="csv-file-input"
                    onChange={(e) => setCsvFile(e.target.files[0])}
                    className="hidden"
                  />
                  <label htmlFor="csv-file-input" className="cursor-pointer flex flex-col items-center">
                    <FileSpreadsheet className="w-10 h-10 text-indigo-400 mb-2" />
                    <span className="text-xs font-semibold text-white">
                      {csvFile ? csvFile.name : "Click to select workforce .CSV file"}
                    </span>
                    <span className="text-[11px] text-slate-500 mt-1">UTF-8 Comma-separated spreadsheet format</span>
                  </label>
                </div>

                <div className="flex items-center justify-between text-xs pt-1">
                  <button
                    type="button"
                    onClick={downloadSampleTemplate}
                    className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium transition-colors"
                  >
                    <FileText className="w-3.5 h-3.5" /> Download Standard CSV Template
                  </button>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsCsvModalOpen(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-all cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={uploadingCsv || !csvFile}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer shadow-sm"
                  >
                    {uploadingCsv ? 'Ingesting Dataset...' : 'Upload & Score Dataset'}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                <div className="bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-xl text-center">
                  <Check className="w-8 h-8 text-emerald-400 mx-auto mb-1" />
                  <h4 className="text-sm font-bold text-white">Dataset Ingestion Complete</h4>
                  <p className="text-xs text-slate-300 mt-0.5">Automated predictive attrition scoring has evaluated the imported records</p>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase">Processed</span>
                    <span className="text-sm font-bold text-white">{csvUploadResult.total_rows}</span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase">Imported</span>
                    <span className="text-sm font-bold text-emerald-400">+{csvUploadResult.successful_imports}</span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase">Duplicates</span>
                    <span className="text-sm font-bold text-amber-400">{csvUploadResult.duplicates_skipped}</span>
                  </div>
                </div>

                {csvUploadResult.errors.length > 0 && (
                  <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg text-[11px] text-slate-400 max-h-32 overflow-y-auto font-mono">
                    {csvUploadResult.errors.map((err, i) => (
                      <div key={i} className="text-amber-300/80">{err}</div>
                    ))}
                  </div>
                )}

                <div className="flex justify-end pt-2">
                  <button
                    onClick={() => setIsCsvModalOpen(false)}
                    className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all cursor-pointer"
                  >
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Onboarding Modal */}
      {isModalOpen && isAdminOrHR && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-xl rounded-2xl shadow-2xl p-6 relative">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
                  <UserPlus className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white">Onboard New Employee</h3>
              </div>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-all cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs rounded-lg">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateEmployee} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Employee Code</label>
                  <input
                    type="text"
                    required
                    placeholder="EMP010"
                    value={newEmp.employee_code}
                    onChange={(e) => setNewEmp({ ...newEmp, employee_code: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Department</label>
                  <select
                    value={newEmp.department_id}
                    onChange={(e) => setNewEmp({ ...newEmp, department_id: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.code})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">First Name</label>
                  <input
                    type="text"
                    required
                    placeholder="Aditi"
                    value={newEmp.first_name}
                    onChange={(e) => setNewEmp({ ...newEmp, first_name: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Last Name</label>
                  <input
                    type="text"
                    required
                    placeholder="Sharma"
                    value={newEmp.last_name}
                    onChange={(e) => setNewEmp({ ...newEmp, last_name: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Corporate Email</label>
                  <input
                    type="email"
                    required
                    placeholder="aditi.sharma@workforce.ai"
                    value={newEmp.email}
                    onChange={(e) => setNewEmp({ ...newEmp, email: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Designation</label>
                  <input
                    type="text"
                    required
                    placeholder="Frontend Engineer"
                    value={newEmp.designation}
                    onChange={(e) => setNewEmp({ ...newEmp, designation: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Monthly Salary (₹)</label>
                  <input
                    type="number"
                    required
                    placeholder="75000"
                    value={newEmp.monthly_salary}
                    onChange={(e) => setNewEmp({ ...newEmp, monthly_salary: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Date of Joining</label>
                  <input
                    type="date"
                    required
                    value={newEmp.date_of_joining}
                    onChange={(e) => setNewEmp({ ...newEmp, date_of_joining: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-all cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer"
                >
                  {submitting ? 'Creating...' : 'Onboard Employee'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Retention Case Drawer & Department Modal remain intact */}
      {selectedDeptCode && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-4xl rounded-2xl shadow-2xl p-6 relative max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4 shrink-0">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
                  <Building2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    {deptDeepDive ? `${deptDeepDive.name} (${deptDeepDive.code})` : 'Department Deep-Dive'}
                  </h3>
                  <p className="text-xs text-slate-400">Departmental turnover metrics and talent roster</p>
                </div>
              </div>
              <button 
                onClick={() => setSelectedDeptCode(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-all cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {loadingDept ? (
              <div className="flex-1 flex items-center justify-center text-slate-400 text-xs py-16">
                <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading department diagnostics...
              </div>
            ) : deptDeepDive ? (
              <div className="flex-1 overflow-y-auto space-y-5 pr-1">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
                    <span className="text-slate-500 text-[11px] block uppercase font-medium">Headcount</span>
                    <span className="text-xl font-bold text-white">{deptDeepDive.headcount}</span>
                  </div>
                  <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
                    <span className="text-slate-500 text-[11px] block uppercase font-medium">Avg Risk Index</span>
                    <span className="text-xl font-bold text-indigo-400">{deptDeepDive.average_risk_score}%</span>
                  </div>
                  <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
                    <span className="text-slate-500 text-[11px] block uppercase font-medium">Avg Monthly Pay</span>
                    <span className="text-xl font-bold text-slate-200 font-mono">₹{deptDeepDive.average_salary.toLocaleString()}</span>
                  </div>
                  <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
                    <span className="text-slate-500 text-[11px] block uppercase font-medium">Urgent Watch</span>
                    <span className="text-xl font-bold text-rose-400">{deptDeepDive.high_risk_count} High Risk</span>
                  </div>
                </div>

                <div className="bg-indigo-500/10 border border-indigo-500/20 p-3 rounded-xl flex items-center justify-between text-xs">
                  <span className="text-slate-300">
                    <strong className="text-indigo-300">Dominant Department Risk Factor:</strong> {deptDeepDive.primary_team_driver}
                  </span>
                  <div className="flex gap-2 text-[10px]">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">{deptDeepDive.low_risk_count} Stable</span>
                    <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">{deptDeepDive.moderate_risk_count} Watch</span>
                    <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30">{deptDeepDive.high_risk_count} High</span>
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Active Department Talent Roster</h4>
                  <div className="overflow-x-auto rounded-lg border border-slate-800">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-800/60 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold">
                        <tr>
                          <th className="py-2.5 px-3">Code</th>
                          <th className="py-2.5 px-3">Staff Name</th>
                          <th className="py-2.5 px-3">Designation</th>
                          {isAdminOrHR && <th className="py-2.5 px-3">Monthly Pay</th>}
                          <th className="py-2.5 px-3">Risk Probability</th>
                          <th className="py-2.5 px-3">Primary Factor</th>
                          {isAdminOrHR && <th className="py-2.5 px-3 text-right">Action</th>}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800 text-slate-300">
                        {deptDeepDive.employees.map((emp) => (
                          <tr key={emp.id} className="hover:bg-slate-800/30 transition-colors">
                            <td className="py-2.5 px-3 font-mono text-slate-400">{emp.employee_code}</td>
                            <td className="py-2.5 px-3 font-medium text-white">{emp.full_name}</td>
                            <td className="py-2.5 px-3 text-slate-400">{emp.designation}</td>
                            {isAdminOrHR && (
                              <td className="py-2.5 px-3 font-mono text-slate-300">₹{emp.monthly_salary.toLocaleString()}</td>
                            )}
                            <td className="py-2.5 px-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                                emp.risk_category === 'HIGH'
                                  ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                                  : emp.risk_category === 'MODERATE'
                                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                                  : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                              }`}>
                                {emp.risk_score}%
                              </span>
                            </td>
                            <td className="py-2.5 px-3 text-amber-300/90 text-[11px]">{emp.top_contributing_factor}</td>
                            {isAdminOrHR && (
                              <td className="py-2.5 px-3 text-right">
                                {emp.risk_category === 'HIGH' ? (
                                  <button
                                    onClick={() => {
                                      setSelectedDeptCode(null);
                                      handleOpenCaseDrawer(emp.id);
                                    }}
                                    className="px-2 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-[11px] transition-all cursor-pointer font-medium"
                                  >
                                    Review
                                  </button>
                                ) : (
                                  <button
                                    onClick={() => handleIndividualPredict(emp.id)}
                                    disabled={evaluatingId === emp.id}
                                    className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 text-[11px] transition-all cursor-pointer"
                                  >
                                    {evaluatingId === emp.id ? '...' : 'Score'}
                                  </button>
                                )}
                              </td>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : null}

            <div className="flex justify-end pt-4 border-t border-slate-800 mt-4 shrink-0">
              <button
                onClick={() => setSelectedDeptCode(null)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-all cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedCaseEmp && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 h-full shadow-2xl flex flex-col p-6 overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-rose-500/10 text-rose-400 rounded-lg">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Retention Case Diagnostic</h3>
                  <p className="text-xs text-slate-400">Actionable retention review and risk intervention plan</p>
                </div>
              </div>
              <button 
                onClick={() => setSelectedCaseEmp(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-all cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {loadingCase ? (
              <div className="flex-1 flex items-center justify-center text-slate-400 text-xs">
                <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading Diagnostic Metrics...
              </div>
            ) : caseDiagnostics ? (
              <div className="mt-4 space-y-6 flex-1">
                <div className="bg-slate-800/40 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-white">{caseDiagnostics.employee_name}</h4>
                    <p className="text-xs text-slate-400">{caseDiagnostics.designation} &bull; {caseDiagnostics.department_name}</p>
                    <p className="text-[11px] font-mono text-indigo-400 mt-0.5">{caseDiagnostics.employee_code}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400 block">Calculated Exit Risk</span>
                    <span className="text-xl font-extrabold text-rose-400">{caseDiagnostics.latest_risk_score}%</span>
                  </div>
                </div>

                <div>
                  <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Key Diagnostic Signals</h5>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg">
                      <span className="text-slate-500 block mb-1">Tenure with Org</span>
                      <span className="text-slate-200 font-semibold">{caseDiagnostics.tenure_days} days</span>
                    </div>
                    <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg">
                      <span className="text-slate-500 block mb-1">Compensation</span>
                      <span className="text-slate-200 font-semibold font-mono">₹{caseDiagnostics.monthly_salary?.toLocaleString()}/mo</span>
                    </div>
                    <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg">
                      <span className="text-slate-500 block mb-1">Average Shift Length</span>
                      <span className="text-slate-200 font-semibold">{caseDiagnostics.avg_daily_hours} hrs/day</span>
                    </div>
                    <div className="bg-slate-950 border border-slate-800 p-3 rounded-lg">
                      <span className="text-slate-500 block mb-1">Approved Leaves</span>
                      <span className="text-slate-200 font-semibold">{caseDiagnostics.total_leaves_taken} days logged</span>
                    </div>
                  </div>
                </div>

                <div className="bg-amber-500/10 border border-amber-500/30 p-3 rounded-lg flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div className="text-xs">
                    <span className="font-semibold text-amber-300 block">AI Detected Primary Driver:</span>
                    <span className="text-slate-300">{caseDiagnostics.primary_factor}</span>
                  </div>
                </div>

                <form onSubmit={handleSaveRetentionCase} className="space-y-4 pt-2 border-t border-slate-800">
                  <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Intervention Plan</h5>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Case Status</label>
                      <select
                        value={caseForm.status}
                        onChange={(e) => setCaseForm({ ...caseForm, status: e.target.value })}
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                      >
                        <option value="OPEN">OPEN</option>
                        <option value="UNDER_REVIEW">UNDER REVIEW</option>
                        <option value="ACTION_PLANNED">ACTION PLANNED</option>
                        <option value="RESOLVED">RESOLVED (RETAINED)</option>
                        <option value="LOST">LOST (ATTRITED)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Intervention Priority</label>
                      <select
                        value={caseForm.priority}
                        onChange={(e) => setCaseForm({ ...caseForm, priority: e.target.value })}
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                      >
                        <option value="CRITICAL">CRITICAL</option>
                        <option value="HIGH">HIGH</option>
                        <option value="MEDIUM">MEDIUM</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Proposed Action</label>
                    <select
                      value={caseForm.action_plan}
                      onChange={(e) => setCaseForm({ ...caseForm, action_plan: e.target.value })}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                    >
                      <option value="1-on-1 Mentorship & Workload Adjustment">1-on-1 Mentorship & Workload Adjustment</option>
                      <option value="Compensation Revision & Bonus Incentive">Compensation Revision & Bonus Incentive</option>
                      <option value="Project Reassignment / Lateral Rotation">Project Reassignment / Lateral Rotation</option>
                      <option value="Wellness & Extended Leave Approval">Wellness & Extended Leave Approval</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Manager Notes & Follow-up Log</label>
                    <textarea
                      rows="3"
                      placeholder="Record discussion outcomes, salary counter-offers, or timeline commitments..."
                      value={caseForm.notes}
                      onChange={(e) => setCaseForm({ ...caseForm, notes: e.target.value })}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => setSelectedCaseEmp(null)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-all cursor-pointer"
                    >
                      Close
                    </button>
                    <button
                      type="submit"
                      disabled={savingCase}
                      className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all flex items-center gap-1.5 disabled:opacity-50 cursor-pointer shadow-sm"
                    >
                      <Save className="w-3.5 h-3.5" />
                      {savingCase ? 'Saving...' : 'Save Case Plan'}
                    </button>
                  </div>
                </form>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
