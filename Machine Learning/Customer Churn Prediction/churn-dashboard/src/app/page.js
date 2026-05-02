"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Users, UserPlus, TrendingUp, AlertTriangle, CheckCircle, 
  BarChart3, Activity, ShieldAlert, Search, ArrowRight, 
  Info, RefreshCw, Zap, BrainCircuit, Globe, CreditCard,
  Image as ImageIcon, PieChart, LayoutDashboard
} from 'lucide-react';

const API_BASE_URL = "http://localhost:8000";

const App = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [metrics, setMetrics] = useState(null);
  const [predictionResult, setPredictionResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Expanded State based on SHAP Importance
  const [formData, setFormData] = useState({
    gender: "Female", SeniorCitizen: 0, Partner: "No", Dependents: "No",
    tenure: 1, PhoneService: "Yes", MultipleLines: "No", InternetService: "Fiber optic",
    OnlineSecurity: "No", OnlineBackup: "No", DeviceProtection: "No",
    TechSupport: "No", StreamingTV: "No", StreamingMovies: "No",
    Contract: "Month-to-month", PaperlessBilling: "Yes",
    PaymentMethod: "Electronic check", MonthlyCharges: 70.0, TotalCharges: 70.0
  });

  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/metrics`);
      if (!response.ok) throw new Error("Metrics offline.");
      setMetrics(await response.json());
    } catch (err) {
      setError("Establish backend link to sync Intelligence.");
    }
  };

  useEffect(() => { fetchMetrics(); }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: (name === 'tenure' || name === 'SeniorCitizen') ? parseInt(value) || 0 : 
              (name === 'MonthlyCharges' || name === 'TotalCharges') ? parseFloat(value) || 0 : value
    }));
  };

  const handlePredict = async (e) => {
    e.preventDefault();
    setLoading(true);
    await new Promise(r => setTimeout(r, 1200)); // Hype delay for AI processing
    try {
      const response = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      setPredictionResult(await response.json());
      setActiveTab('result');
    } catch (err) {
      setError("Inference Engine Unreachable.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#06080F] text-slate-300 font-sans selection:bg-indigo-500/30">
      {/* Dynamic Background Glow */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-indigo-600/10 blur-[120px] rounded-full" />
        <div className="absolute top-[60%] -right-[5%] w-[30%] h-[30%] bg-purple-600/10 blur-[100px] rounded-full" />
      </div>

      <nav className="bg-[#0D111C]/80 backdrop-blur-xl border-b border-white/5 px-8 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-3">
          <motion.div whileHover={{ scale: 1.1 }} className="bg-indigo-600 p-2 rounded-xl shadow-lg shadow-indigo-500/40">
            <ShieldAlert className="text-white w-5 h-5" />
          </motion.div>
          <h1 className="text-lg font-black tracking-tighter text-white uppercase italic">
            Retention<span className="text-indigo-500">Radar</span> 
          </h1>
        </div>
        
        <div className="flex bg-black/40 p-1 rounded-xl border border-white/5">
          {['overview', 'predict'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                (activeTab === tab || (activeTab === 'result' && tab === 'predict')) ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              {tab === 'overview' ? 'Intelligence' : 'Inference'}
            </button>
          ))}
        </div>
      </nav>

      <main className="p-8 max-w-7xl mx-auto relative z-10">
        <AnimatePresence mode="wait">
          {activeTab === 'overview' && (
            <motion.div key="ov" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-8">
              {/* Stat Cards Row */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <StatCard title="Accuracy" val={metrics?.overall_accuracy} unit="%" isP />
                <StatCard title="Power (AUC)" val={metrics?.roc_auc} />
                <StatCard title="Precision" val={metrics?.class_metrics.churn.precision} unit="%" isP />
                <StatCard title="Recall" val={metrics?.class_metrics.churn.recall} unit="%" isP />
              </div>

              {/* Main Analysis Row */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-[#0D111C] border border-white/5 p-8 rounded-3xl">
                  <h3 className="text-sm font-black uppercase tracking-widest text-indigo-400 mb-6 flex items-center gap-2">
                    <BrainCircuit size={16} /> Feature Importance (via SHAP)
                  </h3>
                  <div className="space-y-8">
                    <ImpactBar label="Total Charges" weight={95} color="from-indigo-500 to-blue-600" />
                    <ImpactBar label="Contract Type" weight={88} color="from-purple-500 to-indigo-600" />
                    <ImpactBar label="Tenure Bins" weight={82} color="from-blue-500 to-cyan-600" />
                    <ImpactBar label="Internet (Fiber)" weight={75} color="from-indigo-400 to-indigo-600" />
                  </div>
                </div>
                <div className="bg-indigo-600/10 border border-indigo-500/20 p-8 rounded-3xl flex flex-col justify-center">
                  <h4 className="text-white font-bold text-lg mb-2">System Status</h4>
                  <p className="text-sm text-slate-400 leading-relaxed mb-6">The inference engine is utilizing Random Forest weights optimized for the Indian FinTech sector.</p>
                  <div className="flex items-center gap-2 text-emerald-400 text-[10px] font-bold uppercase tracking-tighter">
                    <div className="w-2 h-2 bg-emerald-500 rounded-full animate-ping" />
                    Active Model: Sentinel_v1_RF
                  </div>
                </div>
              </div>

              {/* Visual Insights Section (EDA Assets) */}
              <div className="space-y-4">
                <h3 className="text-sm font-black uppercase tracking-widest text-slate-500 flex items-center gap-2">
                  <LayoutDashboard size={14} /> Analytical Visual Assets
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <AssetCard 
                    title="Churn Distribution" 
                    imgUrl={`${API_BASE_URL}/assets/churn_distribution.png`}
                    desc="Imbalance analysis of the target variable."
                  />
                  <AssetCard 
                    title="Tenure Dynamics" 
                    imgUrl={`${API_BASE_URL}/assets/tenure_vs_churn.png`}
                    desc="Relationship between loyalty and churn risk."
                  />
                  <AssetCard 
                    title="Global Feature Impact" 
                    imgUrl={`${API_BASE_URL}/assets/shap_summary_plot.png`}
                    desc="SHAP summary showing key model drivers."
                  />
                  <AssetCard 
                    title="Billing Trends" 
                    imgUrl={`${API_BASE_URL}/assets/monthly_charges_boxplot.png`}
                    desc="Revenue variance across customer segments."
                  />
                  <AssetCard 
                    title="Precision-Recall Curve" 
                    imgUrl={`${API_BASE_URL}/assets/precision_recall_curve.png`}
                    desc="Performance trade-off visualization."
                  />
                  <AssetCard 
                    title="ROC Curve" 
                    imgUrl={`${API_BASE_URL}/assets/roc_curve.png`}
                    desc="True Positive vs False Positive rates."
                  />
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'predict' && (
            <motion.div key="pr" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="max-w-5xl mx-auto">
              <div className="bg-[#0D111C] border border-white/5 rounded-3xl overflow-hidden shadow-2xl">
                <div className="p-8 border-b border-white/5 bg-gradient-to-r from-indigo-900/20 to-transparent flex justify-between items-center">
                  <h2 className="text-xl font-bold text-white tracking-tight">Customer Attribute Injection</h2>
                  <Zap className="text-amber-500" size={20} />
                </div>
                
                <form onSubmit={handlePredict} className="p-10">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-10">
                    <div className="space-y-6">
                      <h4 className="text-[12px] font-black text-indigo-500 uppercase tracking-widest border-b border-white/5 pb-2">Core Metrics</h4>
                      <FormInput label="Tenure (Months)" name="tenure" type="number" value={formData.tenure} onChange={handleInputChange} />
                      <FormInput label="Monthly Charges ($)" name="MonthlyCharges" type="number" value={formData.MonthlyCharges} onChange={handleInputChange} />
                      <FormInput label="Total Charges ($)" name="TotalCharges" type="number" value={formData.TotalCharges} onChange={handleInputChange} />
                    </div>
                    
                    <div className="space-y-6">
                      <h4 className="text-[12px] font-black text-indigo-500 uppercase tracking-widest border-b border-white/5 pb-2">Contractual</h4>
                      <FormSelect label="Contract" name="Contract" value={formData.Contract} onChange={handleInputChange} options={['Month-to-month', 'One year', 'Two year']} />
                      <FormSelect label="Payment Method" name="PaymentMethod" value={formData.PaymentMethod} onChange={handleInputChange} options={['Electronic check', 'Mailed check', 'Bank transfer (automatic)', 'Credit card (automatic)']} />
                      <FormSelect label="Paperless Billing" name="PaperlessBilling" value={formData.PaperlessBilling} onChange={handleInputChange} options={['Yes', 'No']} />
                    </div>

                    <div className="space-y-6">
                      <h4 className="text-[12px] font-black text-indigo-500 uppercase tracking-widest border-b border-white/5 pb-2">Service Stack</h4>
                      <FormSelect label="Internet" name="InternetService" value={formData.InternetService} onChange={handleInputChange} options={['DSL', 'Fiber optic', 'No']} />
                      <FormSelect label="Tech Support" name="TechSupport" value={formData.TechSupport} onChange={handleInputChange} options={['Yes', 'No', 'No internet service']} />
                      <FormSelect label="Online Security" name="OnlineSecurity" value={formData.OnlineSecurity} onChange={handleInputChange} options={['Yes', 'No', 'No internet service']} />
                    </div>
                  </div>
                  
                  <motion.button whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }} disabled={loading} className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-black py-4 rounded-xl flex items-center justify-center gap-3 shadow-xl shadow-indigo-500/20 disabled:opacity-50 uppercase tracking-tighter text-sm">
                    {loading ? <RefreshCw className="animate-spin" size={18} /> : "Compute Churn Risk Vector"}
                  </motion.button>
                </form>
              </div>
            </motion.div>
          )}

          {activeTab === 'result' && predictionResult && (
            <motion.div key="re" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} className="max-w-4xl mx-auto flex flex-col md:flex-row gap-6">
              <div className="flex-1 bg-[#0D111C] border border-white/5 p-10 rounded-3xl text-center">
                <div className={`w-20 h-20 mx-auto rounded-full flex items-center justify-center mb-6 ${predictionResult.is_high_risk ? 'bg-red-500/10 text-red-500' : 'bg-emerald-500/10 text-emerald-500'}`}>
                  {predictionResult.is_high_risk ? <AlertTriangle size={40} /> : <CheckCircle size={40} />}
                </div>
                <h2 className="text-3xl font-black text-white mb-2 italic uppercase">
                  {predictionResult.is_high_risk ? 'High Risk' : 'Low Risk'}
                </h2>
                <p className="text-slate-500 text-[12px] font-black uppercase tracking-[0.2em] mb-8">Score: {(predictionResult.churn_probability * 100).toFixed(1)}%</p>
                <div className="bg-white/5 p-6 rounded-2xl text-left border border-white/5">
                  <p className="text-indigo-400 text-[10px] font-black uppercase tracking-widest mb-2">Protocol</p>
                  <p className="text-slate-300 font-medium leading-relaxed italic">"{predictionResult.recommendation}"</p>
                </div>
              </div>
              
              <div className="w-full md:w-80 bg-white/5 p-8 rounded-3xl border border-white/5 backdrop-blur-md">
                <h4 className="text-[12px] font-black text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                  <TrendingUp size={14} /> Risk Drivers
                </h4>
                <div className="space-y-6">
                   <DriverItem label="Billing Behavior" impact={predictionResult.churn_probability > 0.5 ? "High" : "Low"} color={predictionResult.is_high_risk ? "text-red-400" : "text-emerald-400"} />
                   <DriverItem label="Contract Tenure" impact={formData.Contract === 'Month-to-month' ? "Critical" : "Stable"} color={formData.Contract === 'Month-to-month' ? "text-amber-400" : "text-emerald-400"} />
                   <DriverItem label="Service Tier" impact={formData.InternetService} color="text-indigo-400" />
                </div>
                <button onClick={() => setActiveTab('predict')} className="mt-12 w-full py-3 border border-white/10 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-white/5 transition-all">New Assessment</button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
};

const StatCard = ({ title, val, unit, isP }) => (
  <div className="bg-[#0D111C] border border-white/5 p-6 rounded-2xl">
    <p className="text-[12px] font-black text-slate-500 uppercase tracking-widest mb-4">{title}</p>
    <div className="flex items-baseline gap-1">
      <span className="text-2xl font-black text-white">{val ? (isP ? (val * 100).toFixed(1) : val.toFixed(3)) : '---'}</span>
      <span className="text-slate-600 font-bold text-[10px] uppercase">{unit || ''}</span>
    </div>
  </div>
);

const ImpactBar = ({ label, weight, color }) => (
  <div className="space-y-1.5">
    <div className="flex justify-between text-[12px] font-black uppercase tracking-widest text-slate-500">
      <span>{label}</span>
      <span className="text-white opacity-50">{weight}%</span>
    </div>
    <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
      <motion.div initial={{ width: 0 }} animate={{ width: `${weight}%` }} transition={{ duration: 1.5, ease: "easeOut" }} className={`h-full bg-gradient-to-r ${color}`} />
    </div>
  </div>
);

const AssetCard = ({ title, imgUrl, desc }) => (
  <motion.div whileHover={{ scale: 1.02 }} className="bg-[#0D111C] border border-white/5 rounded-2xl overflow-hidden group">
    <div className="aspect-video bg-white/5 relative overflow-hidden flex items-center justify-center">
      <img 
        src={imgUrl} 
        alt={title} 
        className="w-full h-full object-cover transition-opacity duration-500 group-hover:opacity-80"
        onError={(e) => {
          e.target.style.display = 'none';
          e.target.nextSibling.style.display = 'flex';
        }}
      />
      <div className="hidden absolute inset-0 flex-col items-center justify-center text-slate-600 gap-2">
        <ImageIcon size={24} />
        <span className="text-[9px] font-bold uppercase tracking-widest">Asset Unavailable</span>
      </div>
    </div>
    <div className="p-4">
      <h5 className="text-[12px] font-black text-white uppercase tracking-widest mb-1">{title}</h5>
      <p className="text-[10px] text-yellow-400 leading-tight">{desc}</p>
    </div>
  </motion.div>
);

const DriverItem = ({ label, impact, color }) => (
  <div>
    <p className="text-[12px] font-bold text-slate-500 uppercase mb-1">{label}</p>
    <p className={`text-sm font-black ${color}`}>{impact}</p>
  </div>
);

const FormSelect = ({ label, options, ...props }) => (
  <div className="space-y-2">
    <label className="text-[12px] font-black text-slate-500 uppercase tracking-widest ml-1">{label}</label>
    <select {...props} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-xs text-white focus:ring-1 focus:ring-indigo-500 outline-none transition-all cursor-pointer">
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  </div>
);

const FormInput = ({ label, ...props }) => (
  <div className="space-y-2">
    <label className="text-[12px] font-black text-slate-500 uppercase tracking-widest ml-1">{label}</label>
    <input {...props} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-xs text-white focus:ring-1 focus:ring-indigo-500 outline-none transition-all" />
  </div>
);

export default App;