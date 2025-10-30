import { X } from 'lucide-react';
import { WhatIfParams, MockFinancials } from '../types';
import { mockEngine } from '../mockEngine';

interface WhatIfModalProps {
  params: WhatIfParams;
  onParamsChange: (params: WhatIfParams) => void;
  financials: MockFinancials;
  onClose: () => void;
}

export default function WhatIfModal({ params, onParamsChange, financials, onClose }: WhatIfModalProps) {
  const baseFinancials = mockEngine.applyWhatIf({ spendChange: 0, hiringRate: 0, revenueGrowth: 0 });

  const handleChange = (field: keyof WhatIfParams, value: number) => {
    onParamsChange({ ...params, [field]: value });
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-6 animate-fadeIn">
      <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-auto animate-scaleIn">
        <div className="sticky top-0 bg-white/95 backdrop-blur-xl border-b border-gray-200 p-6 flex items-center justify-between rounded-t-3xl">
          <div>
            <h2 className="text-2xl font-bold text-[#2E2E2E] font-['Space_Grotesk']">
              What-if Sandbox
            </h2>
            <p className="text-sm text-gray-600 mt-1">Simulate financial scenarios in real-time</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-xl transition-all duration-200 hover:rotate-90"
          >
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-3 gap-6">
            <SliderControl
              label="Spend Change"
              value={params.spendChange}
              onChange={(v) => handleChange('spendChange', v)}
              min={-50}
              max={100}
              suffix="%"
              color="#58C5B0"
            />
            <SliderControl
              label="Hiring Rate"
              value={params.hiringRate}
              onChange={(v) => handleChange('hiringRate', v)}
              min={0}
              max={10}
              suffix=" people"
              color="#58C5B0"
            />
            <SliderControl
              label="Revenue Growth"
              value={params.revenueGrowth}
              onChange={(v) => handleChange('revenueGrowth', v)}
              min={-20}
              max={50}
              suffix="%"
              color="#58C5B0"
            />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <ComparisonCard
              title="Monthly Burn"
              before={baseFinancials.burn}
              after={financials.burn}
              format="currency"
            />
            <ComparisonCard
              title="Runway"
              before={baseFinancials.runway}
              after={financials.runway}
              format="months"
            />
            <ComparisonCard
              title="Growth Rate"
              before={baseFinancials.growth}
              after={financials.growth}
              format="percentage"
            />
            <ComparisonCard
              title="MRR"
              before={baseFinancials.mrr}
              after={financials.mrr}
              format="currency"
            />
          </div>

          <div className="bg-gradient-to-br from-[#58C5B0]/10 to-[#58C5B0]/5 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-[#2E2E2E] mb-4 font-['Space_Grotesk']">
              Scenario Impact Summary
            </h3>
            <div className="space-y-3">
              <ImpactRow
                label="Engineering Spend"
                value={`$${Math.round(financials.expenses.engineering).toLocaleString()}/mo`}
                change={
                  ((financials.expenses.engineering - baseFinancials.expenses.engineering) /
                    baseFinancials.expenses.engineering) *
                  100
                }
              />
              <ImpactRow
                label="Marketing Spend"
                value={`$${Math.round(financials.expenses.marketing).toLocaleString()}/mo`}
                change={
                  ((financials.expenses.marketing - baseFinancials.expenses.marketing) /
                    baseFinancials.expenses.marketing) *
                  100
                }
              />
              <ImpactRow
                label="AWS Costs"
                value={`$${Math.round(financials.expenses.aws).toLocaleString()}/mo`}
                change={
                  ((financials.expenses.aws - baseFinancials.expenses.aws) /
                    baseFinancials.expenses.aws) *
                  100
                }
              />
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() =>
                onParamsChange({ spendChange: 0, hiringRate: 0, revenueGrowth: 0 })
              }
              className="flex-1 px-6 py-3 bg-gray-100 text-[#2E2E2E] rounded-xl hover:bg-gray-200 transition-all duration-200 font-medium"
            >
              Reset to Baseline
            </button>
            <button
              onClick={onClose}
              className="flex-1 px-6 py-3 bg-[#58C5B0] text-white rounded-xl hover:bg-[#4AB39F] transition-all duration-200 hover:shadow-lg font-medium"
            >
              Apply Scenario
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function SliderControl({
  label,
  value,
  onChange,
  min,
  max,
  suffix,
  color,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  suffix: string;
  color: string;
}) {
  return (
    <div className="bg-white rounded-2xl p-4 shadow-md hover:shadow-lg transition-shadow duration-300">
      <div className="flex items-center justify-between mb-3">
        <label className="text-sm font-semibold text-[#2E2E2E]">{label}</label>
        <span className="text-lg font-bold text-[#58C5B0]">
          {value > 0 ? '+' : ''}
          {value}
          {suffix}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
        style={{
          background: `linear-gradient(to right, ${color} 0%, ${color} ${((value - min) / (max - min)) * 100}%, #E5E7EB ${((value - min) / (max - min)) * 100}%, #E5E7EB 100%)`,
        }}
      />
      <div className="flex justify-between mt-2 text-xs text-gray-500">
        <span>{min}{suffix}</span>
        <span>{max}{suffix}</span>
      </div>
    </div>
  );
}

function ComparisonCard({
  title,
  before,
  after,
  format,
}: {
  title: string;
  before: number;
  after: number;
  format: 'currency' | 'months' | 'percentage';
}) {
  const formatValue = (value: number) => {
    if (format === 'currency') return `$${Math.round(value / 1000)}K`;
    if (format === 'months') return `${value.toFixed(1)}mo`;
    return `${value.toFixed(1)}%`;
  };

  const change = ((after - before) / before) * 100;
  const isPositive = format === 'months' || format === 'percentage' ? change > 0 : change < 0;

  return (
    <div className="bg-white rounded-2xl p-5 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-[1.02]">
      <h4 className="text-sm font-semibold text-gray-600 mb-3">{title}</h4>
      <div className="flex items-end justify-between">
        <div>
          <div className="text-xs text-gray-500 mb-1">Before</div>
          <div className="text-xl font-bold text-gray-400">{formatValue(before)}</div>
        </div>
        <div className="text-2xl text-gray-300 mb-2">→</div>
        <div>
          <div className="text-xs text-gray-500 mb-1">After</div>
          <div className="text-xl font-bold text-[#2E2E2E]">{formatValue(after)}</div>
        </div>
      </div>
      <div
        className={`mt-3 text-xs font-semibold ${
          isPositive ? 'text-green-600' : 'text-orange-600'
        }`}
      >
        {change > 0 ? '+' : ''}
        {change.toFixed(1)}% {isPositive ? 'improvement' : 'impact'}
      </div>
    </div>
  );
}

function ImpactRow({ label, value, change }: { label: string; value: string; change: number }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-700">{label}</span>
      <div className="flex items-center gap-3">
        <span className="text-sm font-semibold text-[#2E2E2E]">{value}</span>
        <span
          className={`text-xs font-semibold px-2 py-1 rounded-full ${
            Math.abs(change) < 1
              ? 'bg-gray-100 text-gray-600'
              : change > 0
              ? 'bg-orange-100 text-orange-700'
              : 'bg-green-100 text-green-700'
          }`}
        >
          {change > 0 ? '+' : ''}
          {change.toFixed(1)}%
        </span>
      </div>
    </div>
  );
}
