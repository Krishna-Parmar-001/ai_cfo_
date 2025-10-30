import { X, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';
import { MockFinancials } from '../types';
import { mockEngine } from '../mockEngine';

interface FundingModalProps {
  financials: MockFinancials;
  onClose: () => void;
}

export default function FundingModal({ financials, onClose }: FundingModalProps) {
  const readiness = mockEngine.getFundingReadiness(financials);

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-6 animate-fadeIn">
      <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-auto animate-scaleIn">
        <div className="sticky top-0 bg-white/95 backdrop-blur-xl border-b border-gray-200 p-6 flex items-center justify-between rounded-t-3xl">
          <div>
            <h2 className="text-2xl font-bold text-[#2E2E2E] font-['Space_Grotesk']">
              Funding Readiness
            </h2>
            <p className="text-sm text-gray-600 mt-1">Dynamic assessment & raise recommendations</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-xl transition-all duration-200 hover:rotate-90"
          >
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="flex items-center justify-center">
            <ReadinessDial score={readiness.score} />
          </div>

          <div className="bg-gradient-to-br from-[#58C5B0]/10 to-[#58C5B0]/5 rounded-2xl p-6">
            <div className="flex items-start gap-3">
              <TrendingUp className="w-6 h-6 text-[#58C5B0] mt-1" />
              <div>
                <h3 className="text-lg font-bold text-[#2E2E2E] mb-2 font-['Space_Grotesk']">
                  AI Recommendation
                </h3>
                <p className="text-gray-700">{readiness.recommendation}</p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-bold text-[#2E2E2E] font-['Space_Grotesk']">
              Readiness Factors
            </h3>
            {readiness.factors.map((factor, i) => (
              <ReadinessFactor key={i} factor={factor} />
            ))}
          </div>

          <div className="grid grid-cols-2 gap-6">
            <InsightCard
              title="Optimal Timing"
              description="Based on current trajectory, Q1 2026 offers best valuation multiple"
              highlight="3-4 months"
            />
            <InsightCard
              title="Target Raise"
              description="Recommended raise amount to achieve 18-month runway"
              highlight="$2.5-3M"
            />
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-md">
            <h3 className="text-lg font-bold text-[#2E2E2E] mb-4 font-['Space_Grotesk']">
              Pre-Raise Checklist
            </h3>
            <div className="space-y-3">
              <ChecklistItem text="Financial records organized and audit-ready" completed={true} />
              <ChecklistItem text="Growth metrics trending positively" completed={true} />
              <ChecklistItem text="Competitive positioning documented" completed={true} />
              <ChecklistItem text="Pitch deck finalized" completed={false} />
              <ChecklistItem text="Investor target list prepared" completed={false} />
              <ChecklistItem text="Legal documents reviewed" completed={false} />
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-6 py-3 bg-[#58C5B0] text-white rounded-xl hover:bg-[#4AB39F] transition-all duration-200 hover:shadow-lg font-medium"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ReadinessDial({ score }: { score: number }) {
  const percentage = score;
  const rotation = (percentage / 100) * 180 - 90;

  const getColor = (score: number) => {
    if (score >= 80) return '#58C5B0';
    if (score >= 60) return '#F59E0B';
    return '#EF4444';
  };

  const color = getColor(score);

  return (
    <div className="relative">
      <svg width="280" height="180" viewBox="0 0 280 180">
        <defs>
          <linearGradient id="dialGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#EF4444" />
            <stop offset="50%" stopColor="#F59E0B" />
            <stop offset="100%" stopColor="#58C5B0" />
          </linearGradient>
        </defs>

        <path
          d="M 40 140 A 100 100 0 0 1 240 140"
          stroke="url(#dialGradient)"
          strokeWidth="24"
          fill="none"
          strokeLinecap="round"
          className="opacity-30"
        />

        <path
          d="M 40 140 A 100 100 0 0 1 240 140"
          stroke={color}
          strokeWidth="24"
          fill="none"
          strokeLinecap="round"
          strokeDasharray="314"
          strokeDashoffset={314 - (314 * percentage) / 100}
          className="transition-all duration-1000"
        />

        <line
          x1="140"
          y1="140"
          x2="140"
          y2="60"
          stroke={color}
          strokeWidth="4"
          strokeLinecap="round"
          style={{
            transformOrigin: '140px 140px',
            transform: `rotate(${rotation}deg)`,
            transition: 'transform 1s ease-out',
          }}
        />
        <circle cx="140" cy="140" r="12" fill={color} />
      </svg>

      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 text-center">
        <div className="text-5xl font-bold" style={{ color }}>
          {score}%
        </div>
        <div className="text-sm text-gray-600 mt-1">Funding Ready</div>
      </div>
    </div>
  );
}

function ReadinessFactor({
  factor,
}: {
  factor: { name: string; score: number; status: 'good' | 'warning' | 'critical' };
}) {
  const Icon =
    factor.status === 'good' ? CheckCircle : factor.status === 'warning' ? AlertCircle : AlertCircle;

  const colors = {
    good: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-700',
      icon: 'text-green-600',
      bar: 'bg-green-500',
    },
    warning: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      text: 'text-yellow-700',
      icon: 'text-yellow-600',
      bar: 'bg-yellow-500',
    },
    critical: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-700',
      icon: 'text-red-600',
      bar: 'bg-red-500',
    },
  };

  const colorSet = colors[factor.status];

  return (
    <div
      className={`${colorSet.bg} ${colorSet.border} border rounded-xl p-4 hover:shadow-md transition-all duration-200`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <Icon className={`w-5 h-5 ${colorSet.icon}`} />
          <span className={`font-semibold ${colorSet.text}`}>{factor.name}</span>
        </div>
        <span className={`text-lg font-bold ${colorSet.text}`}>{factor.score}/100</span>
      </div>
      <div className="h-2 bg-white/50 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorSet.bar} transition-all duration-500 rounded-full`}
          style={{ width: `${factor.score}%` }}
        />
      </div>
    </div>
  );
}

function InsightCard({
  title,
  description,
  highlight,
}: {
  title: string;
  description: string;
  highlight: string;
}) {
  return (
    <div className="bg-white rounded-2xl p-5 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-[1.02]">
      <h4 className="text-sm font-bold text-gray-600 mb-2">{title}</h4>
      <p className="text-sm text-gray-700 mb-3">{description}</p>
      <div className="text-2xl font-bold text-[#58C5B0]">{highlight}</div>
    </div>
  );
}

function ChecklistItem({ text, completed }: { text: string; completed: boolean }) {
  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors duration-200">
      <div
        className={`w-5 h-5 rounded-full flex items-center justify-center ${
          completed ? 'bg-green-500' : 'bg-gray-300'
        }`}
      >
        {completed && <CheckCircle className="w-4 h-4 text-white" />}
      </div>
      <span className={`text-sm ${completed ? 'text-gray-700' : 'text-gray-500'}`}>{text}</span>
    </div>
  );
}
