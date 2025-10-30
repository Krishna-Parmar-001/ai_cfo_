import { MockFinancials } from '../types';
import { TrendingUp, AlertTriangle, DollarSign, Calendar } from 'lucide-react';
import { mockEngine } from '../mockEngine';
import CreditScore from './CreditScore';
import Chart from './Chart';

interface CenterPanelProps {
  financials: MockFinancials;
  chatMode: boolean;
  currentFile: { type: string; name: string } | null;
  onViewAnalytics: () => void;
}

export default function CenterPanel({ financials, chatMode, currentFile, onViewAnalytics }: CenterPanelProps) {
  const creditScore = mockEngine.calculateCreditScore(financials);

  if (chatMode && currentFile) {
    return (
      <div className="flex-1 h-full flex flex-col bg-gradient-to-br from-white/40 to-gray-50/40 backdrop-blur-sm">
        <div className="p-6 border-b border-gray-200/50 flex items-center justify-between bg-white/60 backdrop-blur-md">
          <h2 className="text-lg font-semibold text-[#2E2E2E] font-['Space_Grotesk']">Chat Workspace</h2>
          <button
            onClick={onViewAnalytics}
            className="px-4 py-2 bg-[#58C5B0] text-white rounded-lg hover:bg-[#4AB39F] transition-all duration-200 hover:shadow-lg text-sm font-medium"
          >
            View Analytics
          </button>
        </div>

        <div className="flex-1 p-6 overflow-auto">
          <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-lg p-6 max-w-4xl mx-auto">
            {currentFile.type === 'pdf' && (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-red-100 rounded-lg">
                    <svg className="w-6 h-6 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-[#2E2E2E]">{currentFile.name}</h3>
                    <p className="text-sm text-gray-600">PDF Document • 3 pages</p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mt-6">
                  <div className="bg-gradient-to-br from-[#58C5B0]/10 to-[#58C5B0]/5 rounded-xl p-4">
                    <div className="text-2xl font-bold text-[#2E2E2E]">${Math.round(financials.mrr / 1000)}K</div>
                    <div className="text-sm text-gray-600">MRR</div>
                  </div>
                  <div className="bg-gradient-to-br from-[#58C5B0]/10 to-[#58C5B0]/5 rounded-xl p-4">
                    <div className="text-2xl font-bold text-[#2E2E2E]">{financials.growth.toFixed(1)}%</div>
                    <div className="text-sm text-gray-600">Growth</div>
                  </div>
                  <div className="bg-gradient-to-br from-[#58C5B0]/10 to-[#58C5B0]/5 rounded-xl p-4">
                    <div className="text-2xl font-bold text-[#2E2E2E]">{financials.runway.toFixed(1)}mo</div>
                    <div className="text-sm text-gray-600">Runway</div>
                  </div>
                </div>

                <div className="mt-6 space-y-3">
                  <button className="w-full px-4 py-3 bg-[#58C5B0] text-white rounded-lg hover:bg-[#4AB39F] transition-all duration-200 hover:shadow-lg font-medium">
                    Download PDF
                  </button>
                  <button className="w-full px-4 py-3 bg-white text-[#2E2E2E] border border-gray-200 rounded-lg hover:bg-gray-50 transition-all duration-200 font-medium">
                    Export Full Package (ZIP)
                  </button>
                </div>
              </div>
            )}

            {currentFile.type === 'csv' && (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-green-100 rounded-lg">
                    <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-[#2E2E2E]">{currentFile.name}</h3>
                    <p className="text-sm text-gray-600">CSV File • 124 rows</p>
                  </div>
                </div>

                <div className="overflow-x-auto mt-6">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-100 rounded-lg">
                      <tr>
                        <th className="px-4 py-3 text-left font-semibold text-[#2E2E2E]">Date</th>
                        <th className="px-4 py-3 text-left font-semibold text-[#2E2E2E]">Vendor</th>
                        <th className="px-4 py-3 text-left font-semibold text-[#2E2E2E]">Amount</th>
                        <th className="px-4 py-3 text-left font-semibold text-[#2E2E2E]">Category</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {Array.from({ length: 8 }).map((_, i) => (
                        <tr key={i} className="hover:bg-gray-50 transition-colors">
                          <td className="px-4 py-3">Oct {16 - i}, 2025</td>
                          <td className="px-4 py-3">AWS Services</td>
                          <td className="px-4 py-3">${(Math.random() * 500 + 100).toFixed(2)}</td>
                          <td className="px-4 py-3">Infrastructure</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <button className="w-full px-4 py-3 bg-[#58C5B0] text-white rounded-lg hover:bg-[#4AB39F] transition-all duration-200 hover:shadow-lg font-medium mt-6">
                  Download CSV
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 h-full overflow-auto bg-gradient-to-br from-white/40 to-gray-50/40 backdrop-blur-sm relative">
      <div className="absolute inset-0 opacity-30 pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-[#58C5B0]/10 rounded-full filter blur-3xl animate-float" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-200/20 rounded-full filter blur-3xl animate-float-delay" />
      </div>

      <div className="relative z-10 p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[#2E2E2E] font-['Space_Grotesk']">
              AI-CFO Console — ZypherY
            </h1>
            <p className="text-sm text-gray-600 mt-1">Last updated: 2 minutes ago</p>
          </div>
          <CreditScore score={creditScore.score} breakdown={creditScore.breakdown} />
        </div>

        <div className="grid grid-cols-4 gap-4">
          <InsightCard
            icon={DollarSign}
            title="MRR"
            value={`$${Math.round(financials.mrr / 1000)}K`}
            change={`+${financials.growth.toFixed(1)}%`}
            positive={true}
          />
          <InsightCard
            icon={TrendingUp}
            title="Burn Rate"
            value={`$${Math.round(financials.burn / 1000)}K`}
            change="per month"
            positive={false}
          />
          <InsightCard
            icon={Calendar}
            title="Runway"
            value={`${financials.runway.toFixed(1)}mo`}
            change={financials.runway < 6 ? 'Critical' : 'Healthy'}
            positive={financials.runway >= 6}
          />
          <InsightCard
            icon={TrendingUp}
            title="Growth"
            value={`${financials.growth.toFixed(1)}%`}
            change="MoM"
            positive={true}
          />
        </div>

        <div className="grid grid-cols-2 gap-6">
          <Chart
            title="Monthly Recurring Revenue"
            data={generateMRRData(financials.mrr, financials.growth)}
            color="#58C5B0"
          />
          <Chart title="Burn Rate Trend" data={generateBurnData(financials.burn)} color="#FF6B6B" />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <AlertCard
            icon={AlertTriangle}
            title="AWS spend up 30%, user growth flat"
            severity="warning"
          />
          <AlertCard
            icon={AlertTriangle}
            title={`Runway drops below 6 months — raise soon`}
            severity={financials.runway < 6 ? 'critical' : 'info'}
          />
        </div>

        <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-[#2E2E2E] mb-4 font-['Space_Grotesk']">
            Weekly Founder Digest
          </h3>
          <div className="space-y-3">
            <DigestItem text="Engineering spend increased 12% — new hires onboarding" />
            <DigestItem text="CAC trending down 8% — marketing efficiency improving" />
            <DigestItem text="Treasury Agent recommends Series A preparation in Q1 2026" />
          </div>
        </div>
      </div>
    </div>
  );
}

function InsightCard({
  icon: Icon,
  title,
  value,
  change,
  positive,
}: {
  icon: any;
  title: string;
  value: string;
  change: string;
  positive: boolean;
}) {
  return (
    <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-lg p-4 hover:scale-[1.02] transition-all duration-300 hover:shadow-xl group">
      <div className="flex items-center justify-between mb-2">
        <Icon className="w-5 h-5 text-[#58C5B0] group-hover:animate-bounce" />
        <span
          className={`text-xs font-medium px-2 py-1 rounded-full ${
            positive ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'
          }`}
        >
          {change}
        </span>
      </div>
      <div className="text-2xl font-bold text-[#2E2E2E]">{value}</div>
      <div className="text-sm text-gray-600">{title}</div>
    </div>
  );
}

function AlertCard({ icon: Icon, title, severity }: { icon: any; title: string; severity: string }) {
  const colors = {
    warning: 'bg-orange-50 border-orange-200 text-orange-700',
    critical: 'bg-red-50 border-red-200 text-red-700',
    info: 'bg-blue-50 border-blue-200 text-blue-700',
  };

  return (
    <div
      className={`${colors[severity as keyof typeof colors]} border rounded-xl p-4 hover:scale-[1.02] transition-all duration-200`}
    >
      <div className="flex items-start gap-3">
        <Icon className="w-5 h-5 mt-0.5" />
        <p className="text-sm font-medium">{title}</p>
      </div>
    </div>
  );
}

function DigestItem({ text }: { text: string }) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors duration-200">
      <div className="w-2 h-2 bg-[#58C5B0] rounded-full mt-2 animate-pulse" />
      <p className="text-sm text-gray-700">{text}</p>
    </div>
  );
}

function generateMRRData(mrr: number, growth: number) {
  const data = [];
  let current = mrr * 0.7;
  for (let i = 0; i < 12; i++) {
    data.push(Math.round(current));
    current *= 1 + growth / 100;
  }
  return data;
}

function generateBurnData(burn: number) {
  const data = [];
  const base = burn * 0.85;
  for (let i = 0; i < 12; i++) {
    data.push(Math.round(base + Math.random() * burn * 0.3));
  }
  return data;
}
