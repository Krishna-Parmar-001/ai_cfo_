import { useState } from 'react';
import { Send, Mic, Upload } from 'lucide-react';
import { ChatMessage } from '../types';

interface RightPanelProps {
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
}

export default function RightPanel({ messages, onSendMessage }: RightPanelProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="w-96 bg-white/60 backdrop-blur-xl border-l border-gray-200/50 h-full flex flex-col">
      <div className="p-6 border-b border-gray-200/50 bg-white/40 backdrop-blur-md">
        <h2 className="text-lg font-semibold text-[#2E2E2E] font-['Space_Grotesk'] mb-2">Ask AI-CFO</h2>
        <p className="text-sm text-gray-600">Your financial intelligence partner</p>
      </div>

      <div className="flex-1 overflow-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="space-y-3">
            <ProactiveNudge text="⚠️ Marketing CAC rose 15%. Want to see what changed?" />
            <ProactiveNudge text="💡 Runway below 6 months — explore raise scenarios?" />
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id}>
            {message.role === 'user' ? (
              <div className="flex justify-end">
                <div className="bg-[#58C5B0] text-white px-4 py-3 rounded-2xl rounded-tr-sm max-w-[80%] shadow-md">
                  {message.content}
                </div>
              </div>
            ) : (
              <InsightCard message={message} />
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200/50 bg-white/40 backdrop-blur-md">
        <div className="flex items-center gap-2 bg-white rounded-xl shadow-md p-2 hover:shadow-lg transition-shadow duration-200">
          <button
            type="button"
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200"
          >
            <Upload className="w-5 h-5 text-gray-600" />
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything — 'Should we double R&D spend?'"
            className="flex-1 bg-transparent outline-none text-sm px-2"
          />
          <button
            type="button"
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200"
          >
            <Mic className="w-5 h-5 text-gray-600" />
          </button>
          <button
            type="submit"
            disabled={!input.trim()}
            className="p-2 bg-[#58C5B0] text-white rounded-lg hover:bg-[#4AB39F] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-110"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
}

function InsightCard({ message }: { message: ChatMessage }) {
  return (
    <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-lg p-5 space-y-4 hover:shadow-xl transition-shadow duration-300 border border-gray-100">
      <p className="text-sm text-gray-800 leading-relaxed">{message.content}</p>

      {message.reasoning && message.reasoning.length > 0 && (
        <div className="space-y-2 pt-3 border-t border-gray-200">
          <div className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Reasoning</div>
          {message.reasoning.map((reason, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-gray-600">
              <div className="w-1.5 h-1.5 bg-[#58C5B0] rounded-full mt-1.5 flex-shrink-0" />
              <span>{reason}</span>
            </div>
          ))}
        </div>
      )}

      {message.confidence && (
        <div className="flex items-center gap-2 pt-2 border-t border-gray-200">
          <div className="text-xs font-semibold text-gray-600">Confidence:</div>
          <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-[#58C5B0] to-[#4AB39F] transition-all duration-500 rounded-full"
              style={{ width: `${(message.confidence || 0) * 100}%` }}
            />
          </div>
          <div className="text-xs font-semibold text-[#58C5B0]">
            {Math.round((message.confidence || 0) * 100)}%
          </div>
        </div>
      )}

      {message.actions && message.actions.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-2">
          {message.actions.map((action, i) => (
            <button
              key={i}
              className="px-3 py-1.5 bg-[#58C5B0]/10 text-[#58C5B0] text-xs font-medium rounded-lg hover:bg-[#58C5B0]/20 transition-all duration-200 hover:scale-105"
            >
              {action}
            </button>
          ))}
        </div>
      )}

      {message.fileType && (
        <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
          <div
            className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              message.fileType === 'pdf' ? 'bg-red-100' : 'bg-green-100'
            }`}
          >
            {message.fileType === 'pdf' ? '📄' : '📊'}
          </div>
          <div className="flex-1">
            <div className="text-xs font-semibold text-gray-800">{message.fileName}</div>
            <div className="text-xs text-gray-600">Click to view in console</div>
          </div>
        </div>
      )}
    </div>
  );
}

function ProactiveNudge({ text }: { text: string }) {
  return (
    <button className="w-full bg-gradient-to-r from-orange-50 to-orange-100/50 border border-orange-200 rounded-xl p-4 text-left hover:shadow-md transition-all duration-200 hover:scale-[1.02] group">
      <p className="text-sm text-orange-800 font-medium group-hover:text-orange-900">{text}</p>
    </button>
  );
}
