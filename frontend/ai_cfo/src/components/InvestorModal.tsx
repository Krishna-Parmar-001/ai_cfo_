import { X, FileText, Calendar, Download } from 'lucide-react';
import { MockFinancials } from '../types';
import { useState } from 'react';

interface InvestorModalProps {
  financials: MockFinancials;
  onClose: () => void;
}

export default function InvestorModal({ financials, onClose }: InvestorModalProps) {
  const [autoUpdateInterval, setAutoUpdateInterval] = useState<string>('weekly');

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-6 animate-fadeIn">
      <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-auto animate-scaleIn">
        <div className="sticky top-0 bg-white/95 backdrop-blur-xl border-b border-gray-200 p-6 flex items-center justify-between rounded-t-3xl">
          <div>
            <h2 className="text-2xl font-bold text-[#2E2E2E] font-['Space_Grotesk']">
              Investor Sync
            </h2>
            <p className="text-sm text-gray-600 mt-1">Auto-generated investor reports & updates</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-xl transition-all duration-200 hover:rotate-90"
          >
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-3 gap-4">
            <MetricCard
              title="Current MRR"
              value={`$${Math.round(financials.mrr / 1000)}K`}
              subtitle={`+${financials.growth.toFixed(1)}% growth`}
            />
            <MetricCard
              title="Burn Rate"
              value={`$${Math.round(financials.burn / 1000)}K`}
              subtitle="per month"
            />
            <MetricCard
              title="Runway"
              value={`${financials.runway.toFixed(1)} months`}
              subtitle={financials.runway < 6 ? 'Needs attention' : 'Healthy'}
            />
          </div>

          <div className="bg-gradient-to-br from-white to-gray-50 rounded-2xl p-6 shadow-md">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-red-100 rounded-xl">
                <FileText className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-[#2E2E2E] font-['Space_Grotesk']">
                  Investor Summary (October 2025)
                </h3>
                <p className="text-sm text-gray-600">Generated from live financial data</p>
              </div>
            </div>

            <div className="space-y-4">
              <SummarySection
                title="Financial Snapshot"
                items={[
                  `Monthly Recurring Revenue: $${Math.round(financials.mrr).toLocaleString()}`,
                  `Growth Rate: ${financials.growth.toFixed(1)}% MoM`,
                  `Cash Position: $${Math.round(financials.cash).toLocaleString()}`,
                  `Monthly Burn: $${Math.round(financials.burn).toLocaleString()}`,
                  `Runway: ${financials.runway.toFixed(1)} months`,
                ]}
              />

              <SummarySection
                title="Key Metrics"
                items={[
                  `Engineering: $${Math.round(financials.expenses.engineering).toLocaleString()}/mo`,
                  `Marketing: $${Math.round(financials.expenses.marketing).toLocaleString()}/mo`,
                  `Sales: $${Math.round(financials.expenses.sales).toLocaleString()}/mo`,
                  `Infrastructure: $${Math.round(financials.expenses.aws).toLocaleString()}/mo`,
                ]}
              />

              <SummarySection
                title="Strategic Highlights"
                items={[
                  'Product velocity increasing with new engineering hires',
                  'Customer acquisition efficiency improving quarter-over-quarter',
                  'Infrastructure costs optimized with 15% reduction planned',
                  'Series A preparation underway for Q1 2026',
                ]}
              />
            </div>

            <div className="flex gap-3 mt-6">
              <button className="flex-1 px-4 py-3 bg-[#58C5B0] text-white rounded-xl hover:bg-[#4AB39F] transition-all duration-200 hover:shadow-lg flex items-center justify-center gap-2 font-medium">
                <Download className="w-5 h-5" />
                Download PDF
              </button>
              <button className="flex-1 px-4 py-3 bg-white text-[#2E2E2E] border border-gray-200 rounded-xl hover:bg-gray-50 transition-all duration-200 flex items-center justify-center gap-2 font-medium">
                <Download className="w-5 h-5" />
                Export Full Package (ZIP)
              </button>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-md">
            <div className="flex items-center gap-3 mb-4">
              <Calendar className="w-6 h-6 text-[#58C5B0]" />
              <h3 className="text-lg font-bold text-[#2E2E2E] font-['Space_Grotesk']">
                Auto-Update Schedule
              </h3>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <ScheduleOption
                label="Weekly"
                selected={autoUpdateInterval === 'weekly'}
                onClick={() => setAutoUpdateInterval('weekly')}
              />
              <ScheduleOption
                label="Bi-weekly"
                selected={autoUpdateInterval === 'biweekly'}
                onClick={() => setAutoUpdateInterval('biweekly')}
              />
              <ScheduleOption
                label="Monthly"
                selected={autoUpdateInterval === 'monthly'}
                onClick={() => setAutoUpdateInterval('monthly')}
              />
            </div>

            <div className="mt-4 p-4 bg-[#58C5B0]/10 rounded-xl">
              <p className="text-sm text-gray-700">
                <span className="font-semibold">Next Update:</span> October 23, 2025 at 9:00 AM
              </p>
              <p className="text-xs text-gray-600 mt-1">
                Reports will be automatically generated and emailed to your investor list
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-6 py-3 bg-[#58C5B0] text-white rounded-xl hover:bg-[#4AB39F] transition-all duration-200 hover:shadow-lg font-medium"
            >
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, subtitle }: { title: string; value: string; subtitle: string }) {
  return (
    <div className="bg-white rounded-2xl p-4 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105">
      <div className="text-sm text-gray-600 mb-1">{title}</div>
      <div className="text-2xl font-bold text-[#2E2E2E] mb-1">{value}</div>
      <div className="text-xs text-gray-500">{subtitle}</div>
    </div>
  );
}

function SummarySection({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="border-t border-gray-200 pt-4">
      <h4 className="text-sm font-bold text-[#2E2E2E] mb-3">{title}</h4>
      <div className="space-y-2">
        {items.map((item, i) => (
          <div key={i} className="flex items-start gap-2 text-sm text-gray-700">
            <div className="w-1.5 h-1.5 bg-[#58C5B0] rounded-full mt-2 flex-shrink-0" />
            <span>{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ScheduleOption({
  label,
  selected,
  onClick,
}: {
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-3 rounded-xl font-medium transition-all duration-200 ${
        selected
          ? 'bg-[#58C5B0] text-white shadow-lg scale-105'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
    >
      {label}
    </button>
  );
}
