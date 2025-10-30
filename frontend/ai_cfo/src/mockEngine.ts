import { MockFinancials, WhatIfParams, CreditScoreBreakdown, Agent, Competitor } from './types';

const BASE_FINANCIALS: MockFinancials = {
  mrr: 45000,
  burn: 85000,
  runway: 6.2,
  cash: 527000,
  expenses: {
    engineering: 45000,
    marketing: 18000,
    sales: 12000,
    operations: 7000,
    aws: 3000,
  },
  growth: 12.5,
  revenue: 45000,
};

export class MockDataEngine {
  private baseData: MockFinancials;
  private currentParams: WhatIfParams;

  constructor() {
    this.baseData = { ...BASE_FINANCIALS };
    this.currentParams = {
      spendChange: 0,
      hiringRate: 0,
      revenueGrowth: 0,
    };
  }

  applyWhatIf(params: WhatIfParams): MockFinancials {
    this.currentParams = params;

    const totalExpenses = Object.values(this.baseData.expenses).reduce((a, b) => a + b, 0);
    const spendMultiplier = 1 + params.spendChange / 100;
    const hiringImpact = params.hiringRate * 15000;
    const revenueMultiplier = 1 + params.revenueGrowth / 100;

    const newExpenses = {
      engineering: this.baseData.expenses.engineering * spendMultiplier + hiringImpact * 0.6,
      marketing: this.baseData.expenses.marketing * spendMultiplier,
      sales: this.baseData.expenses.sales * spendMultiplier + hiringImpact * 0.3,
      operations: this.baseData.expenses.operations * spendMultiplier + hiringImpact * 0.1,
      aws: this.baseData.expenses.aws * (1 + params.spendChange / 200),
    };

    const newTotalExpenses = Object.values(newExpenses).reduce((a, b) => a + b, 0);
    const newRevenue = this.baseData.revenue * revenueMultiplier;
    const newBurn = newTotalExpenses - newRevenue;
    const newRunway = newBurn > 0 ? this.baseData.cash / newBurn : 99;
    const newGrowth = this.baseData.growth + params.revenueGrowth * 0.4;

    return {
      mrr: newRevenue,
      burn: newBurn,
      runway: Math.max(0, newRunway),
      cash: this.baseData.cash,
      expenses: newExpenses,
      growth: newGrowth,
      revenue: newRevenue,
    };
  }

  getCurrentFinancials(): MockFinancials {
    if (
      this.currentParams.spendChange === 0 &&
      this.currentParams.hiringRate === 0 &&
      this.currentParams.revenueGrowth === 0
    ) {
      return { ...this.baseData };
    }
    return this.applyWhatIf(this.currentParams);
  }

  calculateCreditScore(financials: MockFinancials): { score: number; breakdown: CreditScoreBreakdown } {
    const revenueGrowth = Math.min(1, financials.growth / 30);
    const burnStability = Math.max(0, 1 - Math.abs(financials.burn - BASE_FINANCIALS.burn) / BASE_FINANCIALS.burn);
    const cashRunway = Math.min(1, financials.runway / 12);
    const debtRatio = 0.85;
    const paymentReliability = 0.92;
    const profitabilityIndex = Math.max(0, 1 - financials.burn / financials.revenue);
    const liquidityIndex = Math.min(1, financials.cash / (financials.burn * 3));

    const weights = {
      revenueGrowth: 0.25,
      burnStability: 0.15,
      cashRunway: 0.20,
      debtRatio: 0.10,
      paymentReliability: 0.10,
      profitabilityIndex: 0.10,
      liquidityIndex: 0.10,
    };

    const score = Math.round(
      1000 *
        (revenueGrowth * weights.revenueGrowth +
          burnStability * weights.burnStability +
          cashRunway * weights.cashRunway +
          debtRatio * weights.debtRatio +
          paymentReliability * weights.paymentReliability +
          profitabilityIndex * weights.profitabilityIndex +
          liquidityIndex * weights.liquidityIndex)
    );

    return {
      score,
      breakdown: {
        revenueGrowth: Math.round(revenueGrowth * 1000 * weights.revenueGrowth),
        burnStability: Math.round(burnStability * 1000 * weights.burnStability),
        cashRunway: Math.round(cashRunway * 1000 * weights.cashRunway),
        debtRatio: Math.round(debtRatio * 1000 * weights.debtRatio),
        paymentReliability: Math.round(paymentReliability * 1000 * weights.paymentReliability),
        profitabilityIndex: Math.round(profitabilityIndex * 1000 * weights.profitabilityIndex),
        liquidityIndex: Math.round(liquidityIndex * 1000 * weights.liquidityIndex),
      },
    };
  }

  getAgents(): Agent[] {
    return [
      {
        id: 'accounting',
        name: 'Accounting Agent',
        description: 'Reconciling transactions from Stripe + bank feed.',
        status: 'active',
        progress: 72,
        lastActions: [
          'Reconciled 540 transactions',
          'Flagged 2 duplicate entries',
          'Updated balance: $527,000',
          'Synced with Stripe API',
          'Generated monthly reports',
        ],
        output: '540 transactions today',
        connections: ['fpna', 'treasury'],
      },
      {
        id: 'fpna',
        name: 'FP&A Agent',
        description: 'Analyzing last 30-day spend variance (R&D up 12%).',
        status: 'thinking',
        progress: 85,
        lastActions: [
          'Detected R&D spend increase: +12%',
          'Compared vs forecast: +4.2% variance',
          'Analyzed AWS cost spike: +30%',
          'User growth analysis: flat',
          'Updated forecast model',
        ],
        output: 'variance +4.2% vs forecast',
        connections: ['strategist', 'treasury'],
      },
      {
        id: 'treasury',
        name: 'Treasury Agent',
        description: 'Balancing cash flows, projecting runway 6.2 months.',
        status: 'active',
        progress: 94,
        lastActions: [
          'Updated cash position: $527k',
          'Projected runway: 6.2 months',
          'Modeled burn scenarios',
          'Flagged: runway below 6 months',
          'Recommended raise timeline',
        ],
        output: '6.2 months runway',
        connections: ['strategist'],
      },
      {
        id: 'audit',
        name: 'Audit & Compliance Agent',
        description: 'Cross-checking expenses with policy rules.',
        status: 'idle',
        progress: 100,
        lastActions: [
          'Scanned 328 expenses',
          'Found 3 policy exceptions',
          'Resolved compliance issues',
          'Updated expense categories',
          'Completed audit cycle',
        ],
        output: '3 exceptions resolved',
        connections: ['accounting'],
      },
      {
        id: 'strategist',
        name: 'CFO/Strategist Agent',
        description: 'Evaluating timing for Series A raise scenario.',
        status: 'thinking',
        progress: 67,
        lastActions: [
          'Analyzed funding readiness: 78%',
          'Modeled raise scenarios',
          'Evaluated market conditions',
          'Compared competitor raises',
          'Generated raise recommendation',
        ],
        output: 'Raise soon — 0.78 confidence',
        connections: [],
      },
    ];
  }

  getFundingReadiness(financials: MockFinancials): {
    score: number;
    factors: { name: string; score: number; status: 'good' | 'warning' | 'critical' }[];
    recommendation: string;
  } {
    const factors = [
      {
        name: 'Valuation Multiple',
        score: 72,
        status: 'good' as const,
      },
      {
        name: 'Growth Rate',
        score: Math.round(Math.min(100, (financials.growth / 20) * 100)),
        status: financials.growth > 15 ? ('good' as const) : ('warning' as const),
      },
      {
        name: 'Compliance & Audit',
        score: 95,
        status: 'good' as const,
      },
      {
        name: 'Team Scale',
        score: 68,
        status: 'warning' as const,
      },
      {
        name: 'Cash Runway',
        score: Math.round((financials.runway / 12) * 100),
        status: financials.runway > 9 ? ('good' as const) : financials.runway > 6 ? ('warning' as const) : ('critical' as const),
      },
    ];

    const avgScore = Math.round(factors.reduce((sum, f) => sum + f.score, 0) / factors.length);

    let recommendation = 'Ready to raise now.';
    if (avgScore < 70) {
      recommendation = 'Delay raise by 2 months for better multiple.';
    } else if (avgScore > 85) {
      recommendation = 'Strong position — raise at premium valuation.';
    }

    return {
      score: avgScore,
      factors,
      recommendation,
    };
  }

  getCompetitors(): Competitor[] {
    return [
      {
        id: 'c1',
        name: 'DataFlow AI',
        funding: 'Series B',
        valuation: 45000000,
        growth: 18.5,
        burn: 120000,
        sector: 'Analytics',
        region: 'US West',
        stage: 'Series B',
        x: 0.3,
        y: 0.6,
      },
      {
        id: 'c2',
        name: 'CloudSync',
        funding: 'Series A',
        valuation: 22000000,
        growth: 25.2,
        burn: 95000,
        sector: 'SaaS',
        region: 'US East',
        stage: 'Series A',
        x: 0.6,
        y: 0.4,
      },
      {
        id: 'c3',
        name: 'MetricsPro',
        funding: 'Seed',
        valuation: 8000000,
        growth: 32.1,
        burn: 45000,
        sector: 'Analytics',
        region: 'EU',
        stage: 'Seed',
        x: 0.75,
        y: 0.7,
      },
      {
        id: 'c4',
        name: 'FinanceOS',
        funding: 'Series A',
        valuation: 28000000,
        growth: 15.8,
        burn: 105000,
        sector: 'FinTech',
        region: 'US West',
        stage: 'Series A',
        x: 0.45,
        y: 0.3,
      },
      {
        id: 'c5',
        name: 'ZypherY',
        funding: 'Seed',
        valuation: 12000000,
        growth: 12.5,
        burn: 85000,
        sector: 'Analytics',
        region: 'US West',
        stage: 'Seed',
        x: 0.5,
        y: 0.5,
      },
    ];
  }

  generateMockResponse(query: string, financials: MockFinancials): {
    content: string;
    confidence: number;
    reasoning: string[];
    actions: string[];
    fileType?: 'pdf' | 'csv' | 'folder';
    fileName?: string;
  } {
    const lowerQuery = query.toLowerCase();

    if (lowerQuery.includes('investor') || lowerQuery.includes('one-pager')) {
      return {
        content: 'Generated investor one-pager with current financials, growth metrics, and funding position.',
        confidence: 0.94,
        reasoning: [
          'Pulled MRR, burn, and runway from Treasury Agent',
          'Compiled growth metrics from FP&A analysis',
          'Added competitive positioning from Market Radar',
          'Formatted using standard investor deck template',
        ],
        actions: ['View PDF', 'Download ZIP', 'Schedule Updates'],
        fileType: 'pdf',
        fileName: 'ZypherY_Investor_Summary_Oct2025.pdf',
      };
    }

    if (lowerQuery.includes('double') && lowerQuery.includes('r&d')) {
      const impact = this.applyWhatIf({ ...this.currentParams, spendChange: 100 });
      return {
        content: `Doubling R&D spend would increase burn by ${Math.round(((impact.burn - financials.burn) / financials.burn) * 100)}%, reducing runway to ${impact.runway.toFixed(1)} months. Growth could increase by ~5-8% if hiring accelerates product velocity.`,
        confidence: 0.82,
        reasoning: [
          `Current R&D: $${Math.round(financials.expenses.engineering).toLocaleString()}/mo`,
          `New R&D: $${Math.round(impact.expenses.engineering).toLocaleString()}/mo`,
          `Burn increase: $${Math.round(impact.burn - financials.burn).toLocaleString()}/mo`,
          'Historical correlation: +10% R&D → +4-6% growth',
        ],
        actions: ['Run What-if Simulation', 'View Funding Impact'],
      };
    }

    if (lowerQuery.includes('runway') || lowerQuery.includes('cash')) {
      return {
        content: `Current runway is ${financials.runway.toFixed(1)} months at $${Math.round(financials.burn).toLocaleString()}/mo burn. Treasury Agent recommends raising within 3-4 months to maintain 12+ month buffer post-raise.`,
        confidence: 0.91,
        reasoning: [
          `Cash balance: $${Math.round(financials.cash).toLocaleString()}`,
          `Monthly burn: $${Math.round(financials.burn).toLocaleString()}`,
          'Industry standard: 12-18 months post-raise',
          'Raise cycle typically takes 3-6 months',
        ],
        actions: ['View Funding Readiness', 'Model Raise Scenarios'],
      };
    }

    if (lowerQuery.includes('aws') || lowerQuery.includes('cost')) {
      return {
        content: `AWS spend increased 30% ($${Math.round(BASE_FINANCIALS.expenses.aws).toLocaleString()} → $${Math.round(financials.expenses.aws).toLocaleString()}) while user growth remained flat. FP&A Agent flagged this as inefficiency — likely compute over-provisioning or data transfer spikes.`,
        confidence: 0.88,
        reasoning: [
          'AWS cost spike detected: +30% MoM',
          'User growth: flat (0-2% range)',
          'Cost per user increased significantly',
          'Audit Agent found no policy violations',
        ],
        actions: ['Investigate AWS Usage', 'Optimize Infrastructure'],
      };
    }

    if (lowerQuery.includes('transaction') || lowerQuery.includes('csv')) {
      return {
        content: 'Retrieved last 7 days of transactions (124 entries) from Accounting Agent. Data includes vendor, amount, category, and reconciliation status.',
        confidence: 0.96,
        reasoning: [
          'Pulled from accounting ledger',
          'Cross-checked with bank feed',
          'Filtered by date range: Oct 9-16, 2025',
          'Validated all entries',
        ],
        actions: ['Download CSV', 'View in Console'],
        fileType: 'csv',
        fileName: 'Transactions_Last7Days.csv',
      };
    }

    return {
      content: `Based on current financials: MRR is $${Math.round(financials.mrr).toLocaleString()} (+${financials.growth.toFixed(1)}% growth), burn is $${Math.round(financials.burn).toLocaleString()}/mo, and runway is ${financials.runway.toFixed(1)} months. All agents are monitoring key metrics and will alert on anomalies.`,
      confidence: 0.89,
      reasoning: [
        'Data sourced from live agent network',
        'All metrics cross-validated',
        'Confidence based on data freshness',
        'Updated 2 minutes ago',
      ],
      actions: ['View Full Dashboard', 'Run What-if Analysis'],
    };
  }
}

export const mockEngine = new MockDataEngine();
