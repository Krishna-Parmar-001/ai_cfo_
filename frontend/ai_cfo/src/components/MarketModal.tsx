import { useState } from 'react';
import { X, Filter } from 'lucide-react';
import { MockFinancials, Competitor } from '../types';
import { mockEngine } from '../mockEngine';

interface MarketModalProps {
  financials: MockFinancials;
  onClose: () => void;
}

export default function MarketModal({ financials, onClose }: MarketModalProps) {
  const [competitors] = useState<Competitor[]>(mockEngine.getCompetitors());
  const [selectedCompetitor, setSelectedCompetitor] = useState<Competitor | null>(null);
  const [filters, setFilters] = useState({
    stage: 'all',
    region: 'all',
    sector: 'all',
  });

  const filteredCompetitors = competitors.filter((c) => {
    if (filters.stage !== 'all' && c.stage !== filters.stage) return false;
    if (filters.region !== 'all' && c.region !== filters.region) return false;
    if (filters.sector !== 'all' && c.sector !== filters.sector) return false;
    return true;
  });

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-6 animate-fadeIn">
      <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl w-full max-w-7xl h-[85vh] overflow-hidden animate-scaleIn">
        <div className="bg-white/95 backdrop-blur-xl border-b border-gray-200 p-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-[#2E2E2E] font-['Space_Grotesk']">
              Market Radar
            </h2>
            <p className="text-sm text-gray-600 mt-1">Live competitor positioning & market intelligence</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-xl transition-all duration-200 hover:rotate-90"
          >
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        <div className="flex h-[calc(100%-88px)]">
          <div className="w-80 border-r border-gray-200 p-6 space-y-6 overflow-auto bg-gray-50/50">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Filter className="w-4 h-4 text-gray-600" />
                <h3 className="text-sm font-bold text-[#2E2E2E]">Filters</h3>
              </div>

              <div className="space-y-4">
                <FilterGroup
                  label="Funding Stage"
                  options={['all', 'Seed', 'Series A', 'Series B']}
                  value={filters.stage}
                  onChange={(v) => setFilters({ ...filters, stage: v })}
                />
                <FilterGroup
                  label="Region"
                  options={['all', 'US West', 'US East', 'EU']}
                  value={filters.region}
                  onChange={(v) => setFilters({ ...filters, region: v })}
                />
                <FilterGroup
                  label="Sector"
                  options={['all', 'Analytics', 'SaaS', 'FinTech']}
                  value={filters.sector}
                  onChange={(v) => setFilters({ ...filters, sector: v })}
                />
              </div>
            </div>

            <div className="pt-4 border-t border-gray-200">
              <h3 className="text-sm font-bold text-[#2E2E2E] mb-3">Companies ({filteredCompetitors.length})</h3>
              <div className="space-y-2">
                {filteredCompetitors.map((comp) => (
                  <button
                    key={comp.id}
                    onClick={() => setSelectedCompetitor(comp)}
                    className={`w-full text-left p-3 rounded-xl transition-all duration-200 ${
                      selectedCompetitor?.id === comp.id
                        ? 'bg-[#58C5B0]/20 shadow-md'
                        : 'bg-white hover:bg-gray-100'
                    }`}
                  >
                    <div className="font-semibold text-sm text-[#2E2E2E] mb-1">{comp.name}</div>
                    <div className="text-xs text-gray-600">{comp.stage}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="flex-1 p-6 overflow-auto">
            <div className="relative bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-lg p-8 h-[500px] mb-6">
              <div className="absolute inset-0 opacity-10">
                <svg className="w-full h-full">
                  <defs>
                    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#58C5B0" strokeWidth="0.5" />
                    </pattern>
                  </defs>
                  <rect width="100%" height="100%" fill="url(#grid)" />
                </svg>
              </div>

              <div className="relative h-full">
                {filteredCompetitors.map((comp) => (
                  <button
                    key={comp.id}
                    onClick={() => setSelectedCompetitor(comp)}
                    className="absolute transform -translate-x-1/2 -translate-y-1/2 group"
                    style={{
                      left: `${comp.x * 100}%`,
                      top: `${comp.y * 100}%`,
                    }}
                  >
                    <div
                      className={`relative transition-all duration-300 ${
                        selectedCompetitor?.id === comp.id
                          ? 'scale-125'
                          : 'group-hover:scale-110'
                      }`}
                    >
                      <div
                        className={`w-16 h-16 rounded-full flex items-center justify-center shadow-lg transition-all duration-300 ${
                          comp.name === 'ZypherY'
                            ? 'bg-[#58C5B0] animate-pulse'
                            : 'bg-white hover:shadow-xl'
                        }`}
                      >
                        <span className="text-xs font-bold text-center px-2">
                          {comp.name === 'ZypherY' ? '🎯' : comp.name.slice(0, 2).toUpperCase()}
                        </span>
                      </div>
                      {comp.name !== 'ZypherY' && (
                        <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-ping opacity-75" />
                      )}
                    </div>
                    <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 whitespace-nowrap">
                      <div className="bg-white/95 backdrop-blur-md px-3 py-1 rounded-lg shadow-md text-xs font-semibold text-[#2E2E2E]">
                        {comp.name}
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              <div className="absolute bottom-4 left-4 text-xs text-gray-600">
                <div className="font-semibold mb-1">Legend:</div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-[#58C5B0] rounded-full" />
                    <span>Your Company</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-white border-2 border-gray-300 rounded-full" />
                    <span>Competitors</span>
                  </div>
                </div>
              </div>
            </div>

            {selectedCompetitor && (
              <div className="bg-white rounded-2xl shadow-lg p-6 animate-slideUp">
                <h3 className="text-xl font-bold text-[#2E2E2E] mb-4 font-['Space_Grotesk']">
                  {selectedCompetitor.name}
                </h3>

                <div className="grid grid-cols-4 gap-4 mb-6">
                  <MetricBox
                    label="Funding Stage"
                    value={selectedCompetitor.stage}
                  />
                  <MetricBox
                    label="Valuation"
                    value={`$${(selectedCompetitor.valuation / 1000000).toFixed(1)}M`}
                  />
                  <MetricBox
                    label="Growth"
                    value={`${selectedCompetitor.growth.toFixed(1)}%`}
                  />
                  <MetricBox
                    label="Burn Rate"
                    value={`$${Math.round(selectedCompetitor.burn / 1000)}K`}
                  />
                </div>

                {selectedCompetitor.name === 'ZypherY' ? (
                  <div className="bg-gradient-to-br from-[#58C5B0]/10 to-[#58C5B0]/5 rounded-xl p-4">
                    <p className="text-sm text-gray-700">
                      This is your company. You're positioned in the mid-growth segment with competitive burn rates. Focus on accelerating growth to move toward top performers.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="bg-gray-50 rounded-xl p-4">
                      <h4 className="text-sm font-bold text-[#2E2E2E] mb-2">Competitive Analysis</h4>
                      <p className="text-sm text-gray-700">
                        {selectedCompetitor.growth > financials.growth
                          ? `${selectedCompetitor.name} is growing ${(selectedCompetitor.growth - financials.growth).toFixed(1)}% faster than ZypherY. Consider their growth strategies.`
                          : `ZypherY is outpacing ${selectedCompetitor.name} by ${(financials.growth - selectedCompetitor.growth).toFixed(1)}%. Maintain momentum.`}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-xl p-4">
                      <h4 className="text-sm font-bold text-[#2E2E2E] mb-2">Market Position</h4>
                      <p className="text-sm text-gray-700">
                        Sector: {selectedCompetitor.sector} • Region: {selectedCompetitor.region}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function FilterGroup({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: string[];
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div>
      <label className="text-xs font-semibold text-gray-600 mb-2 block">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#58C5B0] focus:border-transparent"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt.charAt(0).toUpperCase() + opt.slice(1)}
          </option>
        ))}
      </select>
    </div>
  );
}

function MetricBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gradient-to-br from-gray-50 to-white rounded-xl p-4">
      <div className="text-xs text-gray-600 mb-1">{label}</div>
      <div className="text-lg font-bold text-[#2E2E2E]">{value}</div>
    </div>
  );
}
