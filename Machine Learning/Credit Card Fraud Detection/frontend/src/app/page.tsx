"use client";

import React, { useState, useRef } from "react";
import { 
  ShieldCheck, 
  AlertTriangle, 
  Activity, 
  BarChart3, 
  Settings,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Upload
} from "lucide-react";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer
} from "recharts";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import axios from "axios";
import { Loader2 } from "lucide-react";

const featureImportance = [
  { name: "V17", value: 85, color: "#ef4444" },
  { name: "V14", value: 78, color: "#f87171" },
  { name: "V12", value: 72, color: "#fb923c" },
  { name: "Amount", value: 65, color: "#fbbf24" },
  { name: "hour", value: 58, color: "#fcd34d" },
];

export default function Dashboard() {
  const [threshold, setThreshold] = useState(0.5);
  const [activeTab, setActiveTab] = useState("Overview");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Backend state
  const [summary, setSummary] = useState({ total_transactions: 0, fraud_flags: 0 });
  const [recentAlerts, setRecentAlerts] = useState<any[]>([]);
  const [fraudTrends, setFraudTrends] = useState([
    { time: "00:00", volume: 0, fraud: 0 },
  ]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setIsAnalyzing(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(`http://localhost:8000/score/batch?threshold=${threshold}`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      
      const { summary: apiSummary, alerts, trends } = response.data;
      
      setSummary(apiSummary);
      setRecentAlerts(alerts);
      setFraudTrends(trends);

    } catch (error: any) {
      console.error("Error scoring batch:", error);
      const errorMsg = error.response?.data?.detail || "Failed to process the dataset. Ensure backend is running.";
      alert(errorMsg);
    } finally {
      setIsUploading(false);
      setIsAnalyzing(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-slate-200 font-sans selection:bg-red-500/30">
      <AnimatePresence>
        {isAnalyzing && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-[#050505]/95 backdrop-blur-xl"
          >
            <div className="relative w-64 h-64 mb-12">
              {/* Radar Circles */}
              <motion.div 
                animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeOut" }}
                className="absolute inset-0 border-2 border-red-500/50 rounded-full"
              />
              <motion.div 
                animate={{ scale: [1, 1.8], opacity: [0.3, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeOut", delay: 0.5 }}
                className="absolute inset-0 border-2 border-red-500/30 rounded-full"
              />
              
              {/* Central Shield */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-24 h-24 bg-gradient-to-br from-red-500 to-orange-600 rounded-2xl flex items-center justify-center shadow-[0_0_50px_rgba(239,68,68,0.4)]">
                  <ShieldCheck className="text-white w-12 h-12" />
                </div>
              </div>
              
              {/* Scanning Beam */}
              <motion.div 
                animate={{ rotate: 360 }}
                transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                className="absolute inset-0 border-t-2 border-red-500/50 rounded-full origin-center"
                style={{ clipPath: "polygon(50% 50%, 50% 0, 100% 0, 100% 50%)" }}
              />
            </div>

            <motion.div 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="text-center"
            >
              <h2 className="text-3xl font-bold text-white mb-2 tracking-tight">Analyzing Patterns</h2>
              <div className="flex items-center gap-3 text-slate-400 font-medium">
                <Loader2 className="w-5 h-5 animate-spin text-red-500" />
                <span>Sentinel-ML Engine is scanning for anomalies...</span>
              </div>
            </motion.div>
            
            {/* Progress Bar */}
            <div className="w-80 h-1.5 bg-slate-900 rounded-full mt-12 overflow-hidden border border-slate-800">
              <motion.div 
                initial={{ width: "0%" }}
                animate={{ width: "100%" }}
                transition={{ duration: 2.5, ease: "easeInOut" }}
                className="h-full bg-gradient-to-r from-red-500 to-orange-600 shadow-[0_0_15px_rgba(239,68,68,0.5)]"
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <aside className={cn(
        "fixed left-0 top-0 h-full bg-[#0a0a0a] border-r border-slate-800 transition-all duration-300 z-50",
        isSidebarOpen ? "w-64" : "w-20"
      )}>
        <div className="p-6 flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-orange-600 rounded-xl flex items-center justify-center shadow-lg shadow-red-900/20">
            <ShieldCheck className="text-white w-6 h-6" />
          </div>
          {isSidebarOpen && (
            <span className="font-bold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
              Sentinel-ML
            </span>
          )}
        </div>

        <nav className="mt-8 px-4 space-y-2">
          {[
            { icon: Activity, label: "Overview" },
            { icon: AlertTriangle, label: "Alert Engine" },
            { icon: BarChart3, label: "Analytics" },
            { icon: Settings, label: "Configurations" },
          ].map((item, idx) => (
            <button 
              key={idx} 
              onClick={() => setActiveTab(item.label)}
              className={cn(
              "w-full flex items-center gap-4 p-3 rounded-lg transition-all group",
              activeTab === item.label ? "bg-red-500/10 text-red-500" : "hover:bg-slate-800/50 text-slate-500 hover:text-slate-300"
            )}>
              <item.icon className="w-5 h-5" />
              {isSidebarOpen && <span className="font-medium">{item.label}</span>}
            </button>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main className={cn(
        "transition-all duration-300 min-h-screen",
        isSidebarOpen ? "pl-64" : "pl-20"
      )}>
        {/* Header */}
        <header className="h-20 border-b border-slate-800 flex items-center justify-between px-8 bg-[#050505]/80 backdrop-blur-md sticky top-0 z-40">
          <h2 className="text-xl font-semibold text-white">Dashboard</h2>
          
          <div className="flex items-center gap-4">
            <input 
              type="file" 
              accept=".csv" 
              className="hidden" 
              ref={fileInputRef}
              onChange={handleFileUpload}
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white px-4 py-2 rounded-lg font-medium transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50"
            >
              <Upload className="w-4 h-4" />
              {isUploading ? "Processing..." : "Upload Dataset"}
            </button>
          </div>
        </header>

        <div className="p-8">
          {activeTab === "Overview" && (
            <>
              {/* Hero Section / Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <StatCard 
              label="Total Transactions" 
              value={summary.total_transactions.toLocaleString()} 
              change="+0%" 
              trend="up" 
              icon={Activity} 
            />
            <StatCard 
              label="Fraud Flags" 
              value={summary.fraud_flags.toLocaleString()} 
              change="+0%" 
              trend="up" 
              icon={AlertTriangle} 
              color="text-red-500"
            />
            <StatCard 
              label="Model Precision" 
              value="76.0%" 
              change="+0%" 
              trend="up" 
              icon={BarChart3} 
              color="text-emerald-500"
            />
            <StatCard 
              label="Avg Response Time" 
              value="85ms" 
              change="-5ms" 
              trend="up" 
              icon={Clock} 
              color="text-blue-500"
            />
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
            {/* Main Chart */}
            <div className="xl:col-span-2 bg-[#0a0a0a] border border-slate-800 rounded-2xl p-6 shadow-2xl">
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h3 className="text-lg font-semibold text-white">Fraud Detection Trends</h3>
                  <p className="text-xs text-slate-500 mt-1">Monitoring of flagged vs total transactions</p>
                </div>
              </div>
              <div className="h-[350px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={fraudTrends}>
                    <defs>
                      <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorFraud" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2}/>
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis dataKey="time" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "12px", color: "#f1f5f9" }}
                      itemStyle={{ fontSize: "12px" }}
                    />
                    <Area type="monotone" dataKey="volume" stroke="#3b82f6" fillOpacity={1} fill="url(#colorVolume)" strokeWidth={2} />
                    <Area type="monotone" dataKey="fraud" stroke="#ef4444" fillOpacity={1} fill="url(#colorFraud)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Feature Impact */}
            <div className="bg-[#0a0a0a] border border-slate-800 rounded-2xl p-6">
              <h3 className="text-lg font-semibold text-white mb-6">Engine Logic: Feature Impact</h3>
              <div className="space-y-6">
                {featureImportance.map((feature, idx) => (
                  <div key={idx} className="space-y-2">
                    <div className="flex justify-between items-end">
                      <span className="text-sm font-medium text-slate-400">{feature.name}</span>
                      <span className="text-xs font-bold text-slate-200">{feature.value}%</span>
                    </div>
                    <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${feature.value}%` }}
                        transition={{ duration: 1, delay: idx * 0.1 }}
                        className="h-full rounded-full" 
                        style={{ backgroundColor: feature.color }}
                      ></motion.div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Alerts Feed */}
          <div className="mt-8 bg-[#0a0a0a] border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-white">Alert Stream (Top 50)</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-[#050505] text-slate-500 text-xs uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-4 font-semibold">Transaction ID</th>
                    <th className="px-6 py-4 font-semibold">Amount</th>
                    <th className="px-6 py-4 font-semibold">Fraud Probability</th>
                    <th className="px-6 py-4 font-semibold">Risk Level</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {recentAlerts.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                        No alerts generated. Upload a dataset to view alerts.
                      </td>
                    </tr>
                  ) : (
                    recentAlerts.map((tx, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/30 transition-colors group">
                        <td className="px-6 py-4 text-sm font-medium text-slate-300">{tx.id}</td>
                        <td className="px-6 py-4 text-sm font-semibold text-white">{tx.amount}</td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-slate-900 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-red-500" 
                                style={{ width: `${tx.probability * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-xs text-slate-400">{(tx.probability * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={cn(
                            "px-2 py-1 rounded-md text-[10px] font-bold uppercase",
                            tx.status === "High" ? "bg-red-500/10 text-red-500" : 
                            tx.status === "Medium" ? "bg-orange-500/10 text-orange-500" : "bg-blue-500/10 text-blue-500"
                          )}>
                            {tx.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
          </>)}

          {activeTab === "Alert Engine" && <AlertEngineTab />}
          {activeTab === "Analytics" && <AnalyticsTab />}
          {activeTab === "Configurations" && <ConfigurationsTab threshold={threshold} setThreshold={setThreshold} />}
        </div>
      </main>
    </div>
  );
}

function StatCard({ label, value, change, trend, icon: Icon, color = "text-blue-500" }: any) {
  return (
    <div className="bg-[#0a0a0a] border border-slate-800 p-6 rounded-2xl hover:border-slate-700 transition-all hover:shadow-xl hover:shadow-slate-900/20 group">
      <div className="flex justify-between items-start mb-4">
        <div className={cn("p-2 rounded-xl bg-slate-900 group-hover:scale-110 transition-transform", color)}>
          <Icon className="w-5 h-5" />
        </div>
        <div className={cn(
          "flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full",
          trend === "up" ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
        )}>
          {trend === "up" ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
          {change}
        </div>
      </div>
      <h4 className="text-2xl font-bold text-white mb-1 tracking-tight">{value}</h4>
      <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">{label}</p>
    </div>
  );
}

function AlertEngineTab() {
  const [jsonInput, setJsonInput] = useState("{\n  \"Time\": 0,\n  \"V1\": 0,\n  \"V2\": 0,\n  \"V3\": 0,\n  \"V4\": 0,\n  \"V5\": 0,\n  \"V6\": 0,\n  \"V7\": 0,\n  \"V8\": 0,\n  \"V9\": 0,\n  \"V10\": 0,\n  \"V11\": 0,\n  \"V12\": 0,\n  \"V13\": 0,\n  \"V14\": 0,\n  \"V15\": 0,\n  \"V16\": 0,\n  \"V17\": 0,\n  \"V18\": 0,\n  \"V19\": 0,\n  \"V20\": 0,\n  \"V21\": 0,\n  \"V22\": 0,\n  \"V23\": 0,\n  \"V24\": 0,\n  \"V25\": 0,\n  \"V26\": 0,\n  \"V27\": 0,\n  \"V28\": 0,\n  \"Amount\": 100.0\n}");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handlePredict = async () => {
    try {
      setLoading(true);
      const data = JSON.parse(jsonInput);
      const response = await axios.post("http://localhost:8000/score/streaming", data);
      setResult(response.data);
    } catch (e: any) {
      alert("Error: " + (e.response?.data?.detail || e.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#0a0a0a] border border-slate-800 p-6 rounded-2xl shadow-2xl max-w-4xl mx-auto">
      <h3 className="text-xl font-semibold text-white mb-4">Manual Prediction Engine</h3>
      <p className="text-sm text-slate-400 mb-6">Enter transaction data in JSON format to score it in real-time.</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <textarea 
            value={jsonInput}
            onChange={(e) => setJsonInput(e.target.value)}
            className="w-full h-96 bg-[#050505] text-slate-300 font-mono text-xs p-4 rounded-xl border border-slate-800 focus:border-blue-500 focus:outline-none transition-colors"
          />
          <button 
            onClick={handlePredict}
            disabled={loading}
            className="mt-4 w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white py-3 rounded-lg font-medium transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50"
          >
            {loading ? "Processing..." : "Predict Fraud"}
          </button>
        </div>
        
        <div className="bg-[#050505] border border-slate-800 rounded-xl p-6 flex flex-col items-center justify-center min-h-[300px]">
          {result ? (
            <div className="text-center w-full">
              <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Prediction Result</h4>
              <div className={cn(
                "text-4xl font-bold mb-4",
                result.is_fraud ? "text-red-500" : "text-emerald-500"
              )}>
                {result.is_fraud ? "FRAUD DETECTED" : "SAFE"}
              </div>
              <div className="bg-slate-900 rounded-xl p-4 inline-block w-full text-left">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-slate-400">Probability Score</span>
                  <span className="text-sm font-bold text-white">{(result.probability * 100).toFixed(2)}%</span>
                </div>
                <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div 
                    className={cn("h-full", result.is_fraud ? "bg-red-500" : "bg-emerald-500")} 
                    style={{ width: `${result.probability * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-slate-500 text-sm text-center flex flex-col items-center gap-3">
              <ShieldCheck className="w-12 h-12 opacity-50" />
              Awaiting transaction data...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AnalyticsTab() {
  const images = [
    { src: "/Images/class_distribution.png", title: "Class Distribution" },
    { src: "/Images/amount_distribution.png", title: "Amount Distribution" },
    { src: "/Images/hour_distribution.png", title: "Transactions by Hour" },
    { src: "/Images/correlation_heatmap.png", title: "Correlation Heatmap" },
    { src: "/Images/precision_recall_curve.png", title: "Precision-Recall Curve" }
  ];

  return (
    <div className="space-y-8">
      <h3 className="text-2xl font-bold text-white mb-2">Exploratory Data Analysis</h3>
      <p className="text-slate-400 text-sm">Visual insights from the credit card fraud dataset.</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {images.map((img, idx) => (
          <div key={idx} className="bg-[#0a0a0a] border border-slate-800 p-4 rounded-2xl shadow-xl flex flex-col">
            <h4 className="text-white font-semibold mb-4 ml-2">{img.title}</h4>
            <div className="bg-[#050505] rounded-xl overflow-hidden flex-1 flex items-center justify-center p-2 border border-slate-800/50">
              <img src={img.src} alt={img.title} className="max-w-full h-auto object-contain rounded-lg" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ConfigurationsTab({ threshold, setThreshold }: any) {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="bg-[#0a0a0a] border border-slate-800 p-8 rounded-2xl shadow-2xl">
        <div className="flex items-center gap-3 mb-6">
          <Settings className="w-6 h-6 text-blue-500" />
          <h3 className="text-xl font-bold text-white">Model Parameters</h3>
        </div>
        
        <div className="bg-gradient-to-br from-slate-900 to-[#050505] border border-slate-800 p-6 rounded-xl">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-md font-semibold text-white">Probability Threshold</h4>
            <span className="text-sm font-bold bg-red-500/20 text-red-400 px-3 py-1 rounded-md">{threshold.toFixed(2)}</span>
          </div>
          <input 
            type="range" 
            min="0" 
            max="1" 
            step="0.01" 
            value={threshold} 
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-red-500 mb-6"
          />
          <div className="text-sm text-slate-400 space-y-2 leading-relaxed">
            <p><strong>Impact:</strong> Adjusting the threshold directly impacts the Precision-Recall trade-off.</p>
            <ul className="list-disc pl-5 space-y-1">
              <li><strong>Lower threshold (e.g., 0.3):</strong> Increases Recall (catches more fraud) but may lead to more False Positives.</li>
              <li><strong>Higher threshold (e.g., 0.8):</strong> Increases Precision (fewer false alarms) but may miss some actual fraud.</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="bg-[#0a0a0a] border border-slate-800 p-8 rounded-2xl shadow-2xl">
        <h3 className="text-xl font-bold text-white mb-6">Dataset Schema Requirements</h3>
        <p className="text-sm text-slate-400 mb-6">
          When uploading a CSV dataset for batch processing, ensure it adheres to the exact schema below. The model expects 30 specific columns.
        </p>
        
        <div className="overflow-x-auto bg-[#050505] border border-slate-800 rounded-xl">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900 text-slate-300">
              <tr>
                <th className="px-6 py-4 font-semibold">Column Name</th>
                <th className="px-6 py-4 font-semibold">Data Type</th>
                <th className="px-6 py-4 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-400">
              <tr>
                <td className="px-6 py-3 font-mono text-white">Time</td>
                <td className="px-6 py-3">Float</td>
                <td className="px-6 py-3">Seconds elapsed between this transaction and the first transaction in the dataset.</td>
              </tr>
              <tr>
                <td className="px-6 py-3 font-mono text-white">V1 ... V28</td>
                <td className="px-6 py-3">Float</td>
                <td className="px-6 py-3">Principal components obtained with PCA (anonymized features).</td>
              </tr>
              <tr>
                <td className="px-6 py-3 font-mono text-white">Amount</td>
                <td className="px-6 py-3">Float</td>
                <td className="px-6 py-3">Transaction amount in dollars. Will be internally scaled by the pipeline.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
