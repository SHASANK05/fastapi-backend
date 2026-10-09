import React, { useEffect, useState } from 'react';
import { getFlaggedTransactions, reviewTransaction } from '../api';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';

export default function AdminFraudDashboard() {
  const { user } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processingId, setProcessingId] = useState(null);
  const [reviewNote, setReviewNote] = useState('');
  const [selectedTxn, setSelectedTxn] = useState(null);

  const fetchFlagged = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getFlaggedTransactions();
      setTransactions(data.transactions || []);
      setTotalCount(data.total_count || 0);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load flagged transactions.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFlagged();
  }, []);

  const handleReview = async (transactionId, action) => {
    try {
      setProcessingId(transactionId);
      await reviewTransaction(transactionId, action, reviewNote);
      setSelectedTxn(null);
      setReviewNote('');
      await fetchFlagged();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to submit review.');
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Fraud Detection & Audit</h1>
              <span className="text-xs uppercase px-2.5 py-0.5 rounded-full font-semibold bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400">
                Admin Center
              </span>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Logged in as <strong className="text-slate-700 dark:text-slate-200">{user?.username}</strong> ({user?.role})
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={fetchFlagged}
              className="px-4 py-2 text-sm font-medium rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 transition"
            >
              Refresh
            </button>
            <Link
              to="/"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-5 rounded-xl shadow-sm">
            <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">Flagged Queue</span>
            <div className="text-3xl font-extrabold text-red-600 dark:text-red-400 mt-1">{totalCount}</div>
            <p className="text-xs text-slate-500 mt-1">Requires manual audit or confirmation</p>
          </div>
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-5 rounded-xl shadow-sm">
            <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">Velocity Rules</span>
            <div className="text-2xl font-bold text-slate-800 dark:text-slate-200 mt-1">Active</div>
            <p className="text-xs text-slate-500 mt-1">Max 3 attempts / 2 min window</p>
          </div>
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-5 rounded-xl shadow-sm">
            <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">Single Ticket Ceiling</span>
            <div className="text-2xl font-bold text-slate-800 dark:text-slate-200 mt-1">₹50,000</div>
            <p className="text-xs text-slate-500 mt-1">Auto-blocks high single-value bursts</p>
          </div>
        </div>

        {/* Content Section */}
        {error && (
          <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12 text-slate-500">Loading flagged transactions...</div>
        ) : transactions.length === 0 ? (
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-12 text-center">
            <p className="text-lg font-semibold text-slate-700 dark:text-slate-300">Clean Queue</p>
            <p className="text-sm text-slate-500 mt-1">No pending flagged transactions found.</p>
          </div>
        ) : (
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-100 dark:bg-slate-800/80 text-slate-600 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="py-3 px-4">Txn ID</th>
                    <th className="py-3 px-4">Merchant</th>
                    <th className="py-3 px-4">Amount</th>
                    <th className="py-3 px-4">Reason / Guard Trigger</th>
                    <th className="py-3 px-4">Timestamp</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700/60">
                  {transactions.map((txn) => (
                    <tr key={txn.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
                      <td className="py-3 px-4 font-mono font-medium">#{txn.id}</td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900 dark:text-slate-100">{txn.merchant_name}</div>
                        <div className="text-xs text-slate-400 font-mono">{txn.transaction_reference}</div>
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-900 dark:text-slate-100">
                        ₹{Number(txn.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 max-w-xs">
                        <span className="inline-block px-2.5 py-1 text-xs rounded-md bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 font-medium border border-amber-200 dark:border-amber-900/50">
                          {txn.failure_reason || 'Anomaly Detected'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-xs text-slate-500 whitespace-nowrap">
                        {new Date(txn.created_at).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <button
                          onClick={() => setSelectedTxn(txn)}
                          className="px-3 py-1.5 text-xs font-semibold rounded-md bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 hover:opacity-90 transition"
                        >
                          Review
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Review Modal */}
        {selectedTxn && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
              <div className="flex justify-between items-start">
                <h3 className="text-lg font-bold">Review Transaction #{selectedTxn.id}</h3>
                <button
                  onClick={() => setSelectedTxn(null)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-lg leading-none"
                >
                  ✕
                </button>
              </div>

              <div className="text-sm space-y-2 bg-slate-50 dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
                <div><span className="text-slate-400">Merchant:</span> <strong>{selectedTxn.merchant_name}</strong></div>
                <div><span className="text-slate-400">Amount:</span> <strong>₹{selectedTxn.amount.toLocaleString('en-IN')}</strong></div>
                <div><span className="text-slate-400">Flag Reason:</span> <span className="text-red-500">{selectedTxn.failure_reason}</span></div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-1">
                  Audit Notes
                </label>
                <textarea
                  value={reviewNote}
                  onChange={(e) => setReviewNote(e.target.value)}
                  placeholder="e.g., Verified cardholder identity via OTP / manual confirmation"
                  className="w-full text-sm p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  rows="3"
                />
              </div>

              <div className="flex gap-2 justify-end pt-2">
                <button
                  disabled={processingId === selectedTxn.id}
                  onClick={() => handleReview(selectedTxn.id, 'CONFIRMED_FRAUD')}
                  className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-red-600 hover:bg-red-700 text-white transition disabled:opacity-50"
                >
                  Confirm Fraud
                </button>
                <button
                  disabled={processingId === selectedTxn.id}
                  onClick={() => handleReview(selectedTxn.id, 'RESOLVED')}
                  className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition disabled:opacity-50"
                >
                  Resolve (Allow)
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}