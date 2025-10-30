import { X, Sliders, Activity, FileText, TrendingUp, Radar } from 'lucide-react';
import { Mode } from '../types';

interface LeftPanelProps {
  isOpen: boolean;
  onToggle: () => void;
  onModeSelect: (mode: Mode) => void;
  currentMode: Mode;
}

const modes = [
  { id: 'whatif' as Mode, icon: Sliders, label: 'What-if Sandbox', color: '#58C5B0' },
  { id: 'agents' as Mode, icon: Activity, label: 'Agent Pulse', color: '#58C5B0' },
  { id: 'investor' as Mode, icon: FileText, label: 'Investor Sync', color: '#58C5B0' },
  { id: 'funding' as Mode, icon: TrendingUp, label: 'Funding Readiness', color: '#58C5B0' },
  { id: 'market' as Mode, icon: Radar, label: 'Market Radar', color: '#58C5B0' },
];

export default function LeftPanel({ isOpen, onToggle, onModeSelect, currentMode }: LeftPanelProps) {
  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed left-0 top-1/2 -translate-y-1/2 bg-white/80 backdrop-blur-md shadow-lg rounded-r-2xl p-3 hover:bg-white transition-all duration-300 z-50"
      >
        <Activity className="w-5 h-5 text-[#2E2E2E]" />
      </button>
    );
  }

  return (
    <div className="w-64 bg-white/60 backdrop-blur-xl border-r border-gray-200/50 h-full flex flex-col p-4 animate-slideIn">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-sm font-semibold text-[#2E2E2E] font-['Space_Grotesk']">Modes</h2>
        <button
          onClick={onToggle}
          className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors duration-200"
        >
          <X className="w-4 h-4 text-gray-600" />
        </button>
      </div>

      <div className="space-y-2">
        {modes.map((mode) => (
          <button
            key={mode.id}
            onClick={() => onModeSelect(mode.id)}
            className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all duration-200 group hover:scale-[1.02] hover:shadow-md ${
              currentMode === mode.id
                ? 'bg-gradient-to-r from-[#58C5B0]/10 to-[#58C5B0]/5 shadow-sm'
                : 'hover:bg-gray-50'
            }`}
          >
            <div
              className={`p-2 rounded-lg transition-all duration-200 ${
                currentMode === mode.id ? 'bg-[#58C5B0]/20' : 'bg-gray-100 group-hover:bg-[#58C5B0]/10'
              }`}
            >
              <mode.icon
                className={`w-4 h-4 transition-colors duration-200 ${
                  currentMode === mode.id ? 'text-[#58C5B0]' : 'text-[#2E2E2E] group-hover:text-[#58C5B0]'
                }`}
              />
            </div>
            <div className="flex-1 text-left">
              <div className="text-sm font-medium text-[#2E2E2E]">{mode.label}</div>
            </div>
            <div
              className={`w-2 h-2 rounded-full transition-all duration-200 ${
                currentMode === mode.id ? 'bg-[#58C5B0] animate-pulse' : 'bg-gray-300'
              }`}
            />
          </button>
        ))}
      </div>
    </div>
  );
}
