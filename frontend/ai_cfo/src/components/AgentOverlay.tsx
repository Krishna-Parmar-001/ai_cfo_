import { useState, useEffect } from 'react';
import { X, Pause, Play } from 'lucide-react';
import { mockEngine } from '../mockEngine';
import { Agent } from '../types';

interface AgentOverlayProps {
  onClose: () => void;
}

export default function AgentOverlay({ onClose }: AgentOverlayProps) {
  const [agents, setAgents] = useState<Agent[]>(mockEngine.getAgents());
  const [paused, setPaused] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  useEffect(() => {
    if (paused) return;

    const interval = setInterval(() => {
      setAgents((prev) =>
        prev.map((agent) => ({
          ...agent,
          progress: agent.status === 'active' ? Math.min(100, agent.progress + Math.random() * 5) : agent.progress,
          status: agent.progress >= 100 ? 'idle' : agent.status,
        }))
      );
    }, 2000);

    return () => clearInterval(interval);
  }, [paused]);

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-md z-50 flex items-center justify-center p-6 animate-fadeIn">
      <div className="bg-gradient-to-br from-white/95 to-gray-50/95 backdrop-blur-xl rounded-3xl shadow-2xl w-full max-w-7xl h-[85vh] overflow-hidden animate-scaleIn">
        <div className="bg-white/95 backdrop-blur-xl border-b border-gray-200 p-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-[#2E2E2E] font-['Space_Grotesk']">Agent Pulse</h2>
            <p className="text-sm text-gray-600 mt-1">Live agent activity & explainable AI system</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setPaused(!paused)}
              className="px-4 py-2 bg-[#58C5B0] text-white rounded-xl hover:bg-[#4AB39F] transition-all duration-200 hover:shadow-lg flex items-center gap-2"
            >
              {paused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
              {paused ? 'Resume' : 'Pause'} Simulation
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-xl transition-all duration-200 hover:rotate-90"
            >
              <X className="w-6 h-6 text-gray-600" />
            </button>
          </div>
        </div>

        <div className="p-8 h-[calc(100%-88px)] overflow-auto">
          <div className="relative h-full">
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              {agents.map((agent) => {
                const fromPos = getAgentPosition(agent.id, agents.length);
                return agent.connections.map((toId) => {
                  const toAgent = agents.find((a) => a.id === toId);
                  if (!toAgent) return null;
                  const toPos = getAgentPosition(toId, agents.length);

                  return (
                    <g key={`${agent.id}-${toId}`}>
                      <line
                        x1={fromPos.x}
                        y1={fromPos.y}
                        x2={toPos.x}
                        y2={toPos.y}
                        stroke="#58C5B0"
                        strokeWidth="2"
                        opacity="0.3"
                        className="transition-all duration-500"
                      />
                      {agent.status === 'active' && (
                        <circle r="4" fill="#58C5B0" className="animate-flow">
                          <animateMotion dur="3s" repeatCount="indefinite">
                            <mpath xlinkHref={`#path-${agent.id}-${toId}`} />
                          </animateMotion>
                        </circle>
                      )}
                      <path
                        id={`path-${agent.id}-${toId}`}
                        d={`M ${fromPos.x} ${fromPos.y} L ${toPos.x} ${toPos.y}`}
                        fill="none"
                      />
                    </g>
                  );
                });
              })}
            </svg>

            <div className="relative grid grid-cols-3 gap-8 h-full">
              {agents.map((agent) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  onClick={() => setSelectedAgent(agent)}
                  paused={paused}
                />
              ))}
            </div>
          </div>
        </div>

        {selectedAgent && (
          <AgentDetailPanel agent={selectedAgent} onClose={() => setSelectedAgent(null)} />
        )}
      </div>
    </div>
  );
}

function AgentCard({
  agent,
  onClick,
  paused,
}: {
  agent: Agent;
  onClick: () => void;
  paused: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className="bg-white/80 backdrop-blur-md rounded-2xl shadow-lg p-6 hover:shadow-2xl transition-all duration-300 hover:scale-105 relative overflow-hidden group"
    >
      <div
        className={`absolute inset-0 ${
          agent.status === 'active'
            ? 'bg-gradient-to-br from-[#58C5B0]/10 to-[#58C5B0]/5 animate-pulse'
            : agent.status === 'thinking'
            ? 'bg-gradient-to-br from-blue-500/10 to-blue-500/5 animate-pulse'
            : 'bg-gradient-to-br from-gray-100/50 to-gray-50/50'
        }`}
      />

      <div className="relative z-10">
        <div className="flex items-center justify-between mb-3">
          <div
            className={`w-16 h-16 rounded-full flex items-center justify-center ${
              agent.status === 'active'
                ? 'bg-[#58C5B0]/20'
                : agent.status === 'thinking'
                ? 'bg-blue-500/20'
                : 'bg-gray-200'
            }`}
          >
            <div
              className={`w-12 h-12 rounded-full ${
                agent.status === 'active'
                  ? 'bg-[#58C5B0] animate-pulse'
                  : agent.status === 'thinking'
                  ? 'bg-blue-500 animate-pulse'
                  : 'bg-gray-400'
              }`}
            />
          </div>
          <StatusBadge status={agent.status} paused={paused} />
        </div>

        <h3 className="text-lg font-bold text-[#2E2E2E] mb-2 font-['Space_Grotesk']">
          {agent.name}
        </h3>
        <p className="text-sm text-gray-600 mb-4">{agent.description}</p>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600">Progress</span>
            <span className="font-semibold text-[#2E2E2E]">{agent.progress}%</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-[#58C5B0] to-[#4AB39F] transition-all duration-500 rounded-full"
              style={{ width: `${agent.progress}%` }}
            />
          </div>
        </div>

        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="text-xs text-gray-600 mb-1">Current Output</div>
          <div className="text-sm font-semibold text-[#2E2E2E]">{agent.output}</div>
        </div>
      </div>
    </button>
  );
}

function StatusBadge({ status, paused }: { status: string; paused: boolean }) {
  const colors = {
    active: 'bg-green-100 text-green-700',
    thinking: 'bg-blue-100 text-blue-700',
    idle: 'bg-gray-100 text-gray-600',
  };

  if (paused) {
    return (
      <span className="px-3 py-1 bg-orange-100 text-orange-700 text-xs font-semibold rounded-full">
        Paused
      </span>
    );
  }

  return (
    <span className={`px-3 py-1 ${colors[status as keyof typeof colors]} text-xs font-semibold rounded-full`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function AgentDetailPanel({ agent, onClose }: { agent: Agent; onClose: () => void }) {
  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white/95 backdrop-blur-xl shadow-2xl border-l border-gray-200 p-6 animate-slideInRight overflow-auto z-60">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-[#2E2E2E] font-['Space_Grotesk']">{agent.name}</h3>
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200"
        >
          <X className="w-5 h-5 text-gray-600" />
        </button>
      </div>

      <div className="space-y-6">
        <div>
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Description</h4>
          <p className="text-sm text-gray-700">{agent.description}</p>
        </div>

        <div>
          <h4 className="text-sm font-semibold text-gray-600 mb-3">Last 5 Actions</h4>
          <div className="space-y-2">
            {agent.lastActions.map((action, i) => (
              <div
                key={i}
                className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors duration-200"
              >
                <div className="w-6 h-6 bg-[#58C5B0]/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-bold text-[#58C5B0]">{i + 1}</span>
                </div>
                <p className="text-sm text-gray-700">{action}</p>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Current Output</h4>
          <div className="p-4 bg-gradient-to-br from-[#58C5B0]/10 to-[#58C5B0]/5 rounded-lg">
            <p className="text-sm font-semibold text-[#2E2E2E]">{agent.output}</p>
          </div>
        </div>

        {agent.connections.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-600 mb-2">Connected Agents</h4>
            <div className="space-y-2">
              {agent.connections.map((id) => (
                <div
                  key={id}
                  className="px-3 py-2 bg-gray-100 rounded-lg text-sm text-gray-700"
                >
                  {id.charAt(0).toUpperCase() + id.slice(1)} Agent
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function getAgentPosition(agentId: string, total: number) {
  const agents = ['accounting', 'fpna', 'treasury', 'audit', 'strategist'];
  const index = agents.indexOf(agentId);
  const angle = (index / total) * Math.PI * 2 - Math.PI / 2;
  const radius = 200;

  return {
    x: 400 + radius * Math.cos(angle),
    y: 300 + radius * Math.sin(angle),
  };
}
