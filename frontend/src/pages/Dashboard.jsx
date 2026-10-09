import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, DJANGO_BASE_URL, FASTAPI_BASE_URL } from '../api';
import { CreditCard, PlusCircle, Send, CheckCircle2, XCircle, LogOut, RefreshCw, IndianRupee, ShieldCheck } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { Sun, Moon } from 'lucide-react';
import { Link } from 'react-router-dom';


export default function Dashboard() {
  const { user, logout } = useAuth();
  const [cards, setCards] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const { theme, toggleTheme } = useTheme();

  // Dashboard Summary State
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState(null);

  // Add Card form state
  const [cardholderName, setCardholderName] = useState('');
  const [cardNumber, setCardNumber] = useState('');
  const [expiryMonth, setExpiryMonth] = useState('12');
  const [expiryYear, setExpiryYear] = useState('2028');
  const [cardError, setCardError] = useState('');

  // Payment form state
  const [selectedCardId, setSelectedCardId] = useState('');
  const [merchantName, setMerchantName] = useState('Amazon India');
  const [amount, setAmount] = useState('1499');
  const [cvv, setCvv] = useState('789');
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [processing, setProcessing] = useState(false);

  const fetchSummary = async () => {
    setSummaryLoading(true);
    setSummaryError(null);
    try {
      const res = await api.get(`${FASTAPI_BASE_URL}/dashboard/summary`);
      setSummary(res.data);
    } catch (err) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        setSummaryError('JWT Session expired or invalid. Please sign in again.');
      } else {
        setSummaryError('Unable to load analytics summary metrics.');
      }
    } finally {
      setSummaryLoading(false);
    }
  };

  const fetchCards = async () => {
    try {
      const res = await api.get(`${DJANGO_BASE_URL}/api/cards/`);
      setCards(res.data);
      if (res.data.length > 0 && !selectedCardId) {
        setSelectedCardId(res.data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchTransactions = async () => {
    try {
      const res = await api.get(`${FASTAPI_BASE_URL}/api/payments/transactions/`);
      setTransactions(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  useEffect(() => {
    fetchCards();
    fetchTransactions();
    fetchSummary();
  }, []);

  const handleAddCard = async (e) => {
    e.preventDefault();
    setCardError('');
    try {
      await api.post(`${DJANGO_BASE_URL}/api/cards/`, {
        cardholder_name: cardholderName,
        card_number: cardNumber.replace(/\s+/g, ''),
        expiry_month: parseInt(expiryMonth),
        expiry_year: parseInt(expiryYear)
      });
      setCardNumber('');
      setCardholderName('');
      await fetchCards();
      await fetchSummary();
    } catch (err) {
      setCardError(err.response?.data?.card_number?.[0] || 'Failed to save card. Check details.');
    }
  };

  const handleProcessPayment = async (e) => {
    e.preventDefault();
    setProcessing(true);
    setPaymentStatus(null);
    try {
      const res = await api.post(`${FASTAPI_BASE_URL}/api/payments/process/`, {
        card_id: parseInt(selectedCardId),
        amount: parseFloat(amount),
        merchant_name: merchantName,
        cvv: cvv
      });
      setPaymentStatus(res.data);
      await fetchTransactions();
      await fetchSummary();
    } catch (err) {
      setPaymentStatus({
        status: 'FAILED',
        failure_reason: err.response?.data?.detail || 'Gateway error during payment execution.'
      });
    } finally {
      setProcessing(false);
    }
  };

  const [isDark, setIsDark] = useState(() => {
  return localStorage.getItem('theme') !== 'light';
});


return (
    <div className={`min-h-screen transition-colors duration-200 ${
      theme === 'dark' ? 'bg-slate-950 text-slate-100' : 'bg-slate-100 text-slate-900'
    }`}>
      {/* Navbar */}
      <nav className={`border-b px-6 py-4 backdrop-blur-md ${
        theme === 'dark' ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white/80'
      }`}>
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="rounded-xl bg-indigo-600/20 p-2 text-indigo-400 border border-indigo-500/30">
              <CreditCard className="h-6 w-6" />
            </div>
            <div>
              <h1 className={`text-lg font-bold tracking-tight ${theme === 'dark' ? 'text-white' : 'text-slate-900'}`}>Payment Engine</h1>
              <p className={`text-xs ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>Django + FastAPI Hybrid Architecture</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <span className={`text-sm font-medium ${theme === 'dark' ? 'text-slate-300' : 'text-slate-700'}`}>Welcome, {user?.username}</span>
            
            <button
              onClick={toggleTheme}
              className={`flex items-center justify-center rounded-lg border p-2 transition ${
                theme === 'dark'
                  ? 'border-slate-700 bg-slate-800 text-amber-400 hover:bg-slate-700'
                  : 'border-slate-300 bg-slate-200 text-slate-800 hover:bg-slate-300'
              }`}
              title="Toggle theme"
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
            {user?.role === 'ADMIN' && (
            <Link
              to="/admin/fraud"
              className="flex items-center space-x-1.5 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs font-semibold text-red-500 hover:bg-red-500/20 transition"
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Fraud Center</span>
            </Link>
      )}

            <button
              onClick={logout}
              className={`flex items-center space-x-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition ${
                theme === 'dark'
                  ? 'border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700'
                  : 'border-slate-300 bg-slate-200 text-slate-700 hover:bg-slate-300'
              }`}
            >
              <LogOut className="h-3.5 w-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </nav>

    <main className="mx-auto max-w-7xl p-6 space-y-6">
      {/* 4 Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryLoading ? (
          Array.from({ length: 4 }).map((_, idx) => (
            <div key={idx} className={`rounded-2xl border p-5 animate-pulse space-y-3 ${isDark ? 'border-slate-800 bg-slate-900/80' : 'border-slate-200 bg-white'}`}>
              <div className={`h-3.5 rounded w-1/2 ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`}></div>
              <div className={`h-7 rounded w-3/4 ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`}></div>
            </div>
          ))
        ) : summary ? (
          <>
            <div className={`rounded-2xl border p-5 shadow-sm ${isDark ? 'border-slate-800 bg-slate-900/80' : 'border-slate-200 bg-white'}`}>
              <p className={`text-xs font-bold uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Total Spent</p>
              <p className={`text-2xl font-extrabold mt-1.5 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                ₹{summary.total_amount_spent.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
              <p className="text-[11px] text-slate-500 mt-1">Across all authorized transactions</p>
            </div>

            <div className={`rounded-2xl border p-5 shadow-sm ${isDark ? 'border-slate-800 bg-slate-900/80' : 'border-slate-200 bg-white'}`}>
              <p className="text-xs font-bold uppercase tracking-wider text-emerald-500">Available Credit</p>
              <p className="text-2xl font-extrabold text-emerald-500 mt-1.5">
                ₹{summary.available_credit_limit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
              <p className="text-[11px] text-slate-500 mt-1">Active revolving limit</p>
            </div>

            <div className={`rounded-2xl border p-5 shadow-sm ${isDark ? 'border-slate-800 bg-slate-900/80' : 'border-slate-200 bg-white'}`}>
              <p className="text-xs font-bold uppercase tracking-wider text-sky-500">Total Transactions</p>
              <p className={`text-2xl font-extrabold mt-1.5 ${isDark ? 'text-white' : 'text-slate-900'}`}>{summary.total_transactions}</p>
              <p className="text-[11px] text-slate-500 mt-1">Processed count</p>
            </div>

            <div className={`rounded-2xl border p-5 shadow-sm ${isDark ? 'border-slate-800 bg-slate-900/80' : 'border-slate-200 bg-white'}`}>
              <p className="text-xs font-bold uppercase tracking-wider text-amber-500">This Month Spending</p>
              <p className="text-2xl font-extrabold text-amber-500 mt-1.5">
                ₹{summary.current_month_spending.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
              <p className="text-[11px] text-slate-500 mt-1">Current billing cycle</p>
            </div>
          </>
        ) : null}
      </div>

      {/* 3 Main Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Saved Cards */}
        <section className="space-y-6">
          <div className={`rounded-2xl border p-5 shadow-sm ${isDark ? 'border-slate-800 bg-slate-900/80' : 'border-slate-200 bg-white'}`}>
            <h2 className="flex items-center text-sm font-bold tracking-wide uppercase text-indigo-500 mb-4">
              <CreditCard className="mr-2 h-4 w-4" />
              Saved Cards ({cards.length})
            </h2>
            <div className="space-y-3">
              {cards.map((c) => (
                <div
                  key={c.id}
                  onClick={() => setSelectedCardId(c.id)}
                  className={`cursor-pointer rounded-xl border p-4 transition ${
                    selectedCardId === c.id
                      ? 'border-indigo-500 bg-indigo-500/10'
                      : isDark ? 'border-slate-800 bg-slate-950 hover:border-slate-700' : 'border-slate-200 bg-slate-50 hover:border-slate-300'
                  }`}
                >
                  <div className="flex justify-between items-center text-xs font-mono text-slate-400">
                    <span>{c.card_type}</span>
                    <span>{c.expiry_month}/{c.expiry_year}</span>
                  </div>
                  <div className={`my-2 font-mono text-lg tracking-widest ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                    {c.masked_card}
                  </div>
                  <div className="text-xs font-medium text-slate-400 uppercase">
                    {c.cardholder_name}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Add New Card Form */}
          <div className={`rounded-2xl border p-5 shadow-sm ${isDark ? 'border-slate-800 bg-slate-900/80' : 'border-slate-200 bg-white'}`}>
            <h2 className="flex items-center text-sm font-bold tracking-wide uppercase text-indigo-500 mb-4">
              <PlusCircle className="mr-2 h-4 w-4" />
              Add New Card
            </h2>
            {cardError && (
              <div className="mb-3 rounded-lg bg-red-500/10 border border-red-500/20 p-2.5 text-xs text-red-400">
                {cardError}
              </div>
            )}
            <form onSubmit={handleAddCard} className="space-y-3 text-xs">
              <div>
                <label className={`block mb-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Cardholder Name</label>
                <input
                  type="text"
                  required
                  value={cardholderName}
                  onChange={(e) => setCardholderName(e.target.value)}
                  placeholder="e.g. SHASANK S"
                  className={`w-full rounded-lg border p-2 focus:border-indigo-500 focus:outline-none ${
                    isDark ? 'border-slate-700 bg-slate-800 text-white placeholder-slate-500' : 'border-slate-300 bg-slate-50 text-slate-900 placeholder-slate-400'
                  }`}
                />
              </div>
              <div>
                <label className={`block mb-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Card Number (16 Digits)</label>
                <input
                  type="text"
                  required
                  maxLength={16}
                  value={cardNumber}
                  onChange={(e) => setCardNumber(e.target.value)}
                  placeholder="4111222233334444"
                  className={`w-full rounded-lg border p-2 font-mono focus:border-indigo-500 focus:outline-none ${
                    isDark ? 'border-slate-700 bg-slate-800 text-white placeholder-slate-500' : 'border-slate-300 bg-slate-50 text-slate-900 placeholder-slate-400'
                  }`}
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className={`block mb-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Expiry Month</label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    required
                    value={expiryMonth}
                    onChange={(e) => setExpiryMonth(e.target.value)}
                    className={`w-full rounded-lg border p-2 focus:border-indigo-500 focus:outline-none ${
                      isDark ? 'border-slate-700 bg-slate-800 text-white' : 'border-slate-300 bg-slate-50 text-slate-900'
                    }`}
                  />
                </div>
                <div>
                  <label className={`block mb-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Expiry Year</label>
                  <input
                    type="number"
                    min="2026"
                    max="2040"
                    required
                    value={expiryYear}
                    onChange={(e) => setExpiryYear(e.target.value)}
                    className={`w-full rounded-lg border p-2 focus:border-indigo-500 focus:outline-none ${
                      isDark ? 'border-slate-700 bg-slate-800 text-white' : 'border-slate-300 bg-slate-50 text-slate-900'
                    }`}
                  />
                </div>
              </div>
              <button
                type="submit"
                className="mt-2 w-full rounded-lg bg-indigo-600 py-2.5 font-semibold text-white hover:bg-indigo-500 transition"
              >
                Save Card Securely
              </button>
            </form>
          </div>
        </section>

        {/* Center Column: Payment Terminal */}
        <section className="space-y-6">
          <div className={`rounded-2xl border p-5 shadow-sm ${isDark ? 'border-slate-800 bg-slate-900/80' : 'border-slate-200 bg-white'}`}>
            <h2 className="flex items-center text-sm font-bold tracking-wide uppercase text-indigo-500 mb-4">
              <Send className="mr-2 h-4 w-4" />
              FastAPI Payment Terminal
            </h2>
            <form onSubmit={handleProcessPayment} className="space-y-4 text-xs">
              <div>
                <label className={`block mb-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Select Active Card</label>
                <select
                  value={selectedCardId}
                  onChange={(e) => setSelectedCardId(e.target.value)}
                  className={`w-full rounded-lg border p-2 focus:border-indigo-500 focus:outline-none ${
                    isDark ? 'border-slate-700 bg-slate-800 text-white' : 'border-slate-300 bg-slate-50 text-slate-900'
                  }`}
                  disabled={cards.length === 0}
                >
                  {cards.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.masked_card} ({c.card_type}) - {c.cardholder_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className={`block mb-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Merchant Name</label>
                <input
                  type="text"
                  required
                  value={merchantName}
                  onChange={(e) => setMerchantName(e.target.value)}
                  className={`w-full rounded-lg border p-2 focus:border-indigo-500 focus:outline-none ${
                    isDark ? 'border-slate-700 bg-slate-800 text-white' : 'border-slate-300 bg-slate-50 text-slate-900'
                  }`}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={`block mb-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Amount (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className={`w-full rounded-lg border p-2 font-mono focus:border-indigo-500 focus:outline-none ${
                      isDark ? 'border-slate-700 bg-slate-800 text-white' : 'border-slate-300 bg-slate-50 text-slate-900'
                    }`}
                  />
                </div>
                <div>
                  <label className={`block mb-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>CVV (Simulated)</label>
                  <input
                    type="password"
                    maxLength={4}
                    required
                    value={cvv}
                    onChange={(e) => setCvv(e.target.value)}
                    placeholder="789"
                    className={`w-full rounded-lg border p-2 font-mono focus:border-indigo-500 focus:outline-none ${
                      isDark ? 'border-slate-700 bg-slate-800 text-white' : 'border-slate-300 bg-slate-50 text-slate-900'
                    }`}
                  />
                </div>
              </div>

              <div className={`rounded-lg border p-3 text-[11px] space-y-1 ${isDark ? 'border-slate-800 bg-slate-950 text-slate-400' : 'border-slate-200 bg-slate-50 text-slate-600'}`}>
                <p className={`font-semibold ${isDark ? 'text-slate-300' : 'text-slate-800'}`}>Simulation Scenarios:</p>
                <p>Standard input (e.g. CVV 789, ₹1,499) → <span className="text-emerald-500">SUCCESS</span></p>
                <p>CVV <strong>000</strong> → <span className="text-rose-500">FAILS: Invalid CVV</span></p>
                <p>Amount &gt; <strong>₹50,000</strong> → <span className="text-rose-500">FAILS: Limit Exceeded</span></p>
              </div>

              <button
                type="submit"
                disabled={processing || cards.length === 0}
                className="w-full rounded-lg bg-emerald-600 py-3 font-semibold text-white shadow-lg shadow-emerald-600/20 hover:bg-emerald-500 transition disabled:opacity-50"
              >
                {processing ? 'Authorizing with Gateway...' : `Authorize ₹${amount || '0'} Transaction`}
              </button>
            </form>

            {paymentStatus && (
              <div className={`mt-4 rounded-xl border p-4 text-xs ${
                paymentStatus.status === 'SUCCESS'
                  ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400'
                  : 'border-rose-500/40 bg-rose-500/10 text-rose-400'
              }`}>
                <div className="flex items-center space-x-2 font-bold mb-1">
                  {paymentStatus.status === 'SUCCESS' ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  ) : (
                    <XCircle className="h-4 w-4 text-rose-500" />
                  )}
                  <span>Transaction {paymentStatus.status}</span>
                </div>
                {paymentStatus.reference_id && (
                  <p className="font-mono text-[11px] opacity-75">Ref: {paymentStatus.reference_id}</p>
                )}
                {paymentStatus.failure_reason && (
                  <p className="mt-1">{paymentStatus.failure_reason}</p>
                )}
              </div>
            )}
          </div>
        </section>

        {/* Right Column: Transaction History */}
        <section className="space-y-6">
          <div className={`rounded-2xl border p-5 shadow-sm ${isDark ? 'border-slate-800 bg-slate-900/80' : 'border-slate-200 bg-white'}`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="flex items-center text-sm font-bold tracking-wide uppercase text-indigo-500">
                <RefreshCw className="mr-2 h-4 w-4" />
                Transaction Ledger
              </h2>
              <button
                onClick={() => { fetchTransactions(); fetchSummary(); }}
                className="text-xs text-indigo-500 hover:text-indigo-600 transition"
              >
                Refresh
              </button>
            </div>

            <div className="space-y-2.5 max-h-[560px] overflow-y-auto pr-1">
              {transactions.length === 0 ? (
                <p className="text-xs text-slate-500">No payment records found.</p>
              ) : (
                transactions.map((t) => (
                  <div
                    key={t.transaction_id}
                    className={`rounded-xl border p-3 text-xs ${
                      isDark ? 'border-slate-800 bg-slate-950' : 'border-slate-200 bg-slate-50'
                    }`}
                  >
                    <div className="flex justify-between items-center mb-1">
                      <span className={`font-semibold ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>{t.merchant}</span>
                      <span className={`font-mono font-bold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>₹{t.amount.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between items-center text-[11px] text-slate-400">
                      <span className="font-mono">{t.reference_id}</span>
                      <span className={`font-semibold px-2 py-0.5 rounded ${
                        t.status === 'SUCCESS'
                          ? 'bg-emerald-500/10 text-emerald-500'
                          : 'bg-rose-500/10 text-rose-500'
                      }`}>
                        {t.status}
                      </span>
                    </div>
                    {t.failure_reason && (
                      <p className="mt-1 text-[10px] text-rose-500">{t.failure_reason}</p>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </section>
      </div>
    </main>
  </div>
);
}