import React, { useState } from 'react';
import { PiggyBank, HelpCircle, ChevronDown } from 'lucide-react';
import type { DeploymentRecommendation } from '../types';

interface CostCardProps {
  recommendation: DeploymentRecommendation;
}

export const CostCard: React.FC<CostCardProps> = ({ recommendation }) => {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annually'>('monthly');
  const usdTotal = recommendation.estimated_monthly_cost;
  
  // Exchange rate to convert USD to INR
  const EXCHANGE_RATE = 83.33;

  // Convert USD breakdown values to INR
  const getInrValue = (usdVal: number) => {
    const rawInr = usdVal * EXCHANGE_RATE;
    // Round to nearest 10 for clean UX, except if it's small
    if (rawInr === 0) return 0;
    if (rawInr < 50) return Math.round(rawInr / 5) * 5;
    return Math.round(rawInr / 10) * 10;
  };

  const computeInr = getInrValue(recommendation.cost_breakdown.compute);
  const dbInr = getInrValue(recommendation.cost_breakdown.database || 0);
  const storageInr = getInrValue(recommendation.cost_breakdown.storage);
  const transferInr = getInrValue(recommendation.cost_breakdown.data_transfer);
  
  // Sum INR components for visual consistency
  const totalInr = computeInr + dbInr + storageInr + transferInr;
  
  // Adjust period multiplier
  const multiplier = billingPeriod === 'annually' ? 12 : 1;
  const displayTotalInr = totalInr * multiplier;
  const displayTotalUsd = usdTotal * multiplier;

  // Cost status label
  const getCostGrade = (monthlyUsd: number) => {
    if (monthlyUsd < 15) return { label: 'Low Cost', class: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/10' };
    if (monthlyUsd < 50) return { label: 'Moderate Cost', class: 'bg-blue-500/10 text-blue-400 border-blue-500/10' };
    return { label: 'Enterprise Grade', class: 'bg-amber-500/10 text-aws-orange border-aws-orange/10' };
  };

  const costGrade = getCostGrade(usdTotal);

  return (
    <div className="glass-panel p-6 rounded-2xl glow-orange flex flex-col h-full">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h4 className="text-base font-bold text-white flex items-center gap-2">
          <PiggyBank className="w-5 h-5 text-aws-orange" />
          Estimated Cost
        </h4>
        
        {/* Custom Dropdown */}
        <div className="relative">
          <select 
            value={billingPeriod}
            onChange={(e) => setBillingPeriod(e.target.value as any)}
            className="appearance-none bg-slate-900 border border-slate-800 text-slate-300 text-xs font-semibold px-3 py-1.5 pr-8 rounded-lg cursor-pointer focus:outline-none focus:border-slate-700"
          >
            <option value="monthly">Monthly</option>
            <option value="annually">Annually</option>
          </select>
          <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
        </div>
      </div>

      {/* Main Pricing Display */}
      <div className="mb-6">
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-white tracking-tight">
            ₹{displayTotalInr.toLocaleString('en-IN')}
          </span>
          <span className="text-slate-400 text-sm font-semibold">
            /{billingPeriod === 'annually' ? 'year' : 'month'}
          </span>
          <span className={`ml-3 px-2 py-0.5 rounded text-[9px] font-extrabold uppercase border ${costGrade.class}`}>
            {costGrade.label}
          </span>
        </div>
        <p className="text-xs text-slate-500 font-semibold mt-1">
          ~ ${displayTotalUsd.toFixed(1)} USD
        </p>
      </div>

      {/* Pricing Breakdown List */}
      <div className="flex-1 space-y-3.5">
        {/* Compute Resource */}
        <div className="flex justify-between items-center text-xs">
          <span className="text-slate-400 font-medium flex items-center gap-1.5">
            {recommendation.target}
            <HelpCircle size={12} className="text-slate-600 hover:text-slate-400 cursor-pointer" />
          </span>
          <span className="font-bold text-slate-200">
            ₹{(computeInr * multiplier).toLocaleString('en-IN')}
          </span>
        </div>

        {/* Database Resource (Only if greater than 0) */}
        {dbInr > 0 && (
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400 font-medium">RDS Database Instance</span>
            <span className="font-bold text-slate-200">
              ₹{(dbInr * multiplier).toLocaleString('en-IN')}
            </span>
          </div>
        )}

        {/* S3 Storage */}
        <div className="flex justify-between items-center text-xs">
          <span className="text-slate-400 font-medium">Amazon S3 Storage</span>
          <span className="font-bold text-slate-200">
            ₹{(storageInr * multiplier).toLocaleString('en-IN')}
          </span>
        </div>

        {/* Data Transfer */}
        <div className="flex justify-between items-center text-xs">
          <span className="text-slate-400 font-medium">Data Transfer (Out)</span>
          <span className="font-bold text-slate-200">
            ₹{(transferInr * multiplier).toLocaleString('en-IN')}
          </span>
        </div>

        {/* Divider */}
        <div className="border-t border-slate-800/40 my-3" />

        {/* Total Estimated */}
        <div className="flex justify-between items-center text-xs font-bold">
          <span className="text-white">Total Estimated</span>
          <span className="text-white text-sm">
            ₹{displayTotalInr.toLocaleString('en-IN')}
          </span>
        </div>
      </div>

      {/* Footer disclaimer */}
      <div className="mt-5 text-[10px] text-slate-500 font-medium leading-normal flex items-start gap-1">
        <span>&middot;</span>
        <span>Costs are AWS estimations based on idle resources and standard light-tier workloads. Actual costs may vary depending on runtime resource requests.</span>
      </div>
    </div>
  );
};
