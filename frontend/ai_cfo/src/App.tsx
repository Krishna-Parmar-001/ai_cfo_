import { useState, useEffect } from 'react';
import { mockEngine } from './mockEngine';
import { Mode, MockFinancials, WhatIfParams, ChatMessage } from './types';
import LeftPanel from './components/LeftPanel';
import CenterPanel from './components/CenterPanel';
import RightPanel from './components/RightPanel';
import AgentOverlay from './components/AgentOverlay';
import WhatIfModal from './components/WhatIfModal';
import InvestorModal from './components/InvestorModal';
import FundingModal from './components/FundingModal';
import MarketModal from './components/MarketModal';

function App() {
  const [leftPanelOpen, setLeftPanelOpen] = useState(true);
  const [currentMode, setCurrentMode] = useState<Mode>('dashboard');
  const [financials, setFinancials] = useState<MockFinancials>(mockEngine.getCurrentFinancials());
  const [whatIfParams, setWhatIfParams] = useState<WhatIfParams>({ spendChange: 0, hiringRate: 0, revenueGrowth: 0 });
  const [showAgentOverlay, setShowAgentOverlay] = useState(false);
  const [showWhatIf, setShowWhatIf] = useState(false);
  const [showInvestor, setShowInvestor] = useState(false);
  const [showFunding, setShowFunding] = useState(false);
  const [showMarket, setShowMarket] = useState(false);
  const [chatMode, setChatMode] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentFile, setCurrentFile] = useState<{ type: string; name: string } | null>(null);

  useEffect(() => {
    const newFinancials = mockEngine.applyWhatIf(whatIfParams);
    setFinancials(newFinancials);
  }, [whatIfParams]);

  const handleModeSelect = (mode: Mode) => {
    setCurrentMode(mode);
    if (mode === 'whatif') {
      setShowWhatIf(true);
    } else if (mode === 'agents') {
      setShowAgentOverlay(true);
    } else if (mode === 'investor') {
      setShowInvestor(true);
    } else if (mode === 'funding') {
      setShowFunding(true);
    } else if (mode === 'market') {
      setShowMarket(true);
    }
  };

  const handleSendMessage = (content: string) => {
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setChatMode(true);

    setTimeout(() => {
      const response = mockEngine.generateMockResponse(content, financials);
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.content,
        timestamp: new Date(),
        confidence: response.confidence,
        reasoning: response.reasoning,
        actions: response.actions,
        fileType: response.fileType,
        fileName: response.fileName,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (response.fileType) {
        setCurrentFile({ type: response.fileType, name: response.fileName || 'file' });
      }
    }, 800);
  };

  const handleViewAnalytics = () => {
    setChatMode(false);
    setCurrentFile(null);
  };

  return (
    <div className="h-screen w-screen bg-[#FAFAFA] overflow-hidden flex font-['Inter']">
      <LeftPanel
        isOpen={leftPanelOpen}
        onToggle={() => setLeftPanelOpen(!leftPanelOpen)}
        onModeSelect={handleModeSelect}
        currentMode={currentMode}
      />

      <CenterPanel
        financials={financials}
        chatMode={chatMode}
        currentFile={currentFile}
        onViewAnalytics={handleViewAnalytics}
      />

      <RightPanel messages={messages} onSendMessage={handleSendMessage} />

      {showAgentOverlay && <AgentOverlay onClose={() => setShowAgentOverlay(false)} />}

      {showWhatIf && (
        <WhatIfModal
          params={whatIfParams}
          onParamsChange={setWhatIfParams}
          financials={financials}
          onClose={() => setShowWhatIf(false)}
        />
      )}

      {showInvestor && <InvestorModal financials={financials} onClose={() => setShowInvestor(false)} />}

      {showFunding && <FundingModal financials={financials} onClose={() => setShowFunding(false)} />}

      {showMarket && <MarketModal financials={financials} onClose={() => setShowMarket(false)} />}
    </div>
  );
}

export default App;
