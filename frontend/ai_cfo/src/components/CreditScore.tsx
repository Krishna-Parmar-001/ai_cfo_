import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { CreditScoreBreakdown } from '../types';

interface CreditScoreProps {
  score: number;
  breakdown: CreditScoreBreakdown;
}

export default function CreditScore({ score, breakdown }: CreditScoreProps) {
  const [expanded, setExpanded] = useState(false);

  const getColor = (score: number) => {
    if (score >= 750) return 'text-green-600';
    if (score >= 600) return 'text-yellow-600';
    return 'text-orange-600';
  };

  const percentage = (score / 1000) * 100;

  return (
    <div className="relative">
      <button
        onClick={() => setExpanded(!expanded)}
        className="bg-white/80 backdrop-blur-md rounded-2xl shadow-lg p-4 hover:shadow-xl transition-all duration-300 hover:scale-105 group"
      >
        <div className="flex items-center gap-4">
          <div className="relative w-16 h-16">
            <svg className="w-16 h-16 transform -rotate-90">
              <circle
                cx="32"
                cy="32"
                r="28"
                stroke="currentColor"
                strokeWidth="6"
                fill="transparent"
                className="text-gray-200"
              />
              <circle
                cx="32"
                cy="32"
                r="28"
                stroke="currentColor"
                strokeWidth="6"
                fill="transparent"
                strokeDasharray={`${2 * Math.PI * 28}`}
                strokeDashoffset={`${2 * Math.PI * 28 * (1 - percentage / 100)}`}
                className="text-[#58C5B0] transition-all duration-1000"
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-lg font-bold ${getColor(score)}`}>{score}</span>
            </div>
          </div>
          <div className="text-left">
            <div className="text-sm font-semibold text-[#2E2E2E]">Credit Score</div>
            <div className="text-xs text-gray-600">out of 1000</div>
          </div>
          {expanded ? (
            <ChevronUp className="w-5 h-5 text-gray-600 group-hover:text-[#58C5B0] transition-colors" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-600 group-hover:text-[#58C5B0] transition-colors" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="absolute right-0 top-full mt-2 w-96 bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl p-6 z-50 animate-slideDown border border-gray-200">
          <h3 className="text-lg font-bold text-[#2E2E2E] mb-4 font-['Space_Grotesk']">
            Score Breakdown
          </h3>

          <div className="space-y-3">
            <BreakdownRow label="Revenue Growth Rate" value={breakdown.revenueGrowth} weight={25} />
            <BreakdownRow label="Burn Rate Stability" value={breakdown.burnStability} weight={15} />
            <BreakdownRow label="Cash Runway" value={breakdown.cashRunway} weight={20} />
            <BreakdownRow label="Debt Ratio" value={breakdown.debtRatio} weight={10} />
            <BreakdownRow label="Payment Reliability" value={breakdown.paymentReliability} weight={10} />
            <BreakdownRow label="Profitability Index" value={breakdown.profitabilityIndex} weight={10} />
            <BreakdownRow label="Liquidity Index" value={breakdown.liquidityIndex} weight={10} />
          </div>

          <div className="mt-6 pt-4 border-t border-gray-200 flex items-center justify-between">
            <span className="text-sm font-semibold text-[#2E2E2E]">Total Score</span>
            <span className={`text-2xl font-bold ${getColor(score)}`}>{score}</span>
          </div>
        </div>
      )}
    </div>
  );
}

function BreakdownRow({ label, value, weight }: { label: string; value: number; weight: number }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-700">{label}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{weight}%</span>
          <span className="font-semibold text-[#2E2E2E]">{value}</span>
        </div>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-[#58C5B0] to-[#4AB39F] transition-all duration-500 rounded-full"
          style={{ width: `${(value / (1000 * (weight / 100))) * 100}%` }}
        />
      </div>
    </div>
  );
}
