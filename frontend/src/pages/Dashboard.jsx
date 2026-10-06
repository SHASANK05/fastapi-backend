import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, DJANGO_BASE_URL, FASTAPI_BASE_URL } from '../api';
import { CreditCard, PlusCircle, Send, CheckCircle2, XCircle, LogOut, RefreshCw } from 'lucide-react';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [cards, setCards] = useState([]);
  const [transactions, setTransactions] = useState([]);

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
    fetchCards();
    fetchTransactions();
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
    } catch (err) {
      setPaymentStatus({
        status: 'FAILED',
        failure_reason: err.response?.data?.detail || 'Gateway error during payment execution.'
      });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Navbar */}
      <nav className="border-b border-slate-800 bg-slate-900/60 px-6 py-4 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="rounded-xl bg-indigo-600/20 p-2 text-indigo-400 border border-indigo-500/30">
              <CreditCard className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white">Payment Engine</h1>
              <p className="text-xs text-slate-400">Django + FastAPI Hybrid Architecture</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm font-medium text-slate-300">Welcome, {user?.username}</span>
            <button
              onClick={logout}
              className="flex items-center space-x-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:bg-slate-700 transition"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Main Container */}
      <main className="mx-auto max-w-7xl p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Card Vault */}
        <section className="space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg">
            <h2 className="flex items-center text-sm font-bold tracking-wide uppercase text-indigo-400 mb-4">
              <CreditCard className="mr-2 h-4 w-4" />
              Saved Cards ({cards.length})
            </h2>
            
            <div className="space-y-3">
              {cards.length === 0 ? (
                <p className="text-xs text-slate-500">No cards registered yet. Add a card below.</p>
              ) : (
                cards.map((c) => (
                  <div
                    key={c.id}
                    onClick={() => setSelectedCardId(c.id)}
                    className={`cursor-pointer rounded-xl border p-4 transition ${
                      selectedCardId === c.id
                        ? 'border-indigo-500 bg-indigo-950/20'
                        : 'border-slate-800 bg-slate-950 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex justify-between items-center text-xs font-mono text-slate-400">
                      <span>{c.card_type}</span>
                      <span>{c.expiry_month}/{c.expiry_year}</span>
                    </div>
                    <div className="my-2 font-mono text-lg tracking-widest text-slate-100">
                      {c.masked_card}
                    </div>
                    <div className="text-xs font-medium text-slate-400 uppercase">
                      {c.cardholder_name}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Add Card Form */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg">
            <h2 className="flex items-center text-sm font-bold tracking-wide uppercase text-indigo-400 mb-4">
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
                <label className="block text-slate-400 mb-1">Cardholder Name</label>
                <input
                  type="text"
                  required
                  value={cardholderName}
                  onChange={(e) => setCardholderName(e.target.value)}
                  placeholder="e.g. SHASANK S"
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Card Number (16 Digits)</label>
                <input
                  type="text"
                  required
                  maxLength={16}
                  value={cardNumber}
                  onChange={(e) => setCardNumber(e.target.value)}
                  placeholder="4111222233334444"
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 p-2 font-mono text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-400 mb-1">Expiry Month</label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    required
                    value={expiryMonth}
                    onChange={(e) => setExpiryMonth(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Expiry Year</label>
                  <input
                    type="number"
                    min="2026"
                    max="2040"
                    required
                    value={expiryYear}
                    onChange={(e) => setExpiryYear(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white focus:border-indigo-500 focus:outline-none"
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

        {/* Center Column: Payment Simulation Terminal */}
        <section className="space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg">
            <h2 className="flex items-center text-sm font-bold tracking-wide uppercase text-indigo-400 mb-4">
              <Send className="mr-2 h-4 w-4" />
              FastAPI Payment Terminal
            </h2>
            <form onSubmit={handleProcessPayment} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Select Active Card</label>
                <select
                  value={selectedCardId}
                  onChange={(e) => setSelectedCardId(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white focus:border-indigo-500 focus:outline-none"
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
                <label className="block text-slate-400 mb-1">Merchant Name</label>
                <input
                  type="text"
                  required
                  value={merchantName}
                  onChange={(e) => setMerchantName(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Amount (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 p-2 font-mono text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">CVV (Simulated)</label>
                  <input
                    type="password"
                    maxLength={4}
                    required
                    value={cvv}
                    onChange={(e) => setCvv(e.target.value)}
                    placeholder="789"
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 p-2 font-mono text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="rounded-lg border border-slate-800 bg-slate-950 p-3 text-[11px] text-slate-400 space-y-1">
                <p className="font-semibold text-slate-300">Simulation Scenarios:</p>
                <p>• Standard input (e.g. CVV 789, ₹1,499) → <span className="text-emerald-400">SUCCESS</span></p>
                <p>• CVV <strong>000</strong> → <span className="text-rose-400">FAILS: Invalid CVV</span></p>
                <p>• Amount &gt; <strong>₹50,000</strong> → <span className="text-rose-400">FAILS: Limit Exceeded</span></p>
              </div>

              <button
                type="submit"
                disabled={processing || cards.length === 0}
                className="w-full rounded-lg bg-emerald-600 py-3 font-semibold text-white shadow-lg shadow-emerald-600/20 hover:bg-emerald-500 transition disabled:opacity-50"
              >
                {processing ? 'Authorizing with Gateway...' : `Authorize ₹${amount || '0'} Transaction`}
              </button>
            </form>

            {/* Live Gateway Receipt */}
            {paymentStatus && (
              <div className={`mt-4 rounded-xl border p-4 text-xs ${
                paymentStatus.status === 'SUCCESS'
                  ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
                  : 'border-rose-500/40 bg-rose-500/10 text-rose-300'
              }`}>
                <div className="flex items-center space-x-2 font-bold mb-1">
                  {paymentStatus.status === 'SUCCESS' ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  ) : (
                    <XCircle className="h-4 w-4 text-rose-400" />
                  )}
                  <span>Transaction {paymentStatus.status}</span>
                </div>
                {paymentStatus.reference_id && (
                  <p className="font-mono text-[11px] text-slate-400">Ref: {paymentStatus.reference_id}</p>
                )}
                {paymentStatus.failure_reason && (
                  <p className="mt-1 text-rose-300">{paymentStatus.failure_reason}</p>
                )}
              </div>
            )}
          </div>
        </section>

        {/* Right Column: Transaction History */}
        <section className="space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="flex items-center text-sm font-bold tracking-wide uppercase text-indigo-400">
                <RefreshCw className="mr-2 h-4 w-4" />
                Transaction Ledger
              </h2>
              <button
                onClick={fetchTransactions}
                className="text-xs text-indigo-400 hover:text-indigo-300 transition"
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
                    className="rounded-xl border border-slate-800 bg-slate-950 p-3 text-xs"
                  >
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-semibold text-slate-200">{t.merchant}</span>
                      <span className="font-mono font-bold text-slate-100">₹{t.amount.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between items-center text-[11px] text-slate-400">
                      <span className="font-mono">{t.reference_id}</span>
                      <span className={`font-semibold px-2 py-0.5 rounded ${
                        t.status === 'SUCCESS'
                          ? 'bg-emerald-500/10 text-emerald-400'
                          : 'bg-rose-500/10 text-rose-400'
                      }`}>
                        {t.status}
                      </span>
                    </div>
                    {t.failure_reason && (
                      <p className="mt-1 text-[10px] text-rose-400/80">{t.failure_reason}</p>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </section>

      </main>
    </div>
  );
}