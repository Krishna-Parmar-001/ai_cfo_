export interface MockFinancials {
  mrr: number;
  burn: number;
  runway: number;
  cash: number;
  expenses: {
    engineering: number;
    marketing: number;
    sales: number;
    operations: number;
    aws: number;
  };
  growth: number;
  revenue: number;
}

export interface WhatIfParams {
  spendChange: number;
  hiringRate: number;
  revenueGrowth: number;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'idle' | 'thinking';
  progress: number;
  lastActions: string[];
  output: string;
  connections: string[];
}

export interface CreditScoreBreakdown {
  revenueGrowth: number;
  burnStability: number;
  cashRunway: number;
  debtRatio: number;
  paymentReliability: number;
  profitabilityIndex: number;
  liquidityIndex: number;
}

export interface Competitor {
  id: string;
  name: string;
  funding: string;
  valuation: number;
  growth: number;
  burn: number;
  sector: string;
  region: string;
  stage: string;
  x: number;
  y: number;
}

export type Mode = 'dashboard' | 'whatif' | 'agents' | 'investor' | 'funding' | 'market';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  confidence?: number;
  reasoning?: string[];
  actions?: string[];
  fileType?: 'pdf' | 'csv' | 'folder';
  fileName?: string;
}
