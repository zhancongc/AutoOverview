/**
 * David 数据统计页面
 * 展示访问数、注册数、生成数、付费数等统计信息
 */
import React, { useState, useEffect } from 'react';

interface CurrencyStats {
  total_orders: number;
  total_revenue: number;
}

interface PlanCurrencyStats {
  count: number;
  revenue: number;
  name: string;
}

interface FunnelStats {
  search_uv: number;
  preview_to_matrix_rate: number;
  matrix_to_review_rate: number;
  total_credits_consumed: number;
  daily_credit_rate: number;
  preview_tasks: number;
  matrix_tasks: number;
  review_tasks: number;
}

interface OverviewStats {
  visits: {
    total: number;
    today: number;
  };
  registers: {
    total: number;
    today: number;
  };
  generations: {
    total: number;
    free: number;
    paid: number;
  };
  payments: {
    total_orders: number;
    by_currency: {
      [key: string]: CurrencyStats;
    };
    by_plan: {
      [key: string]: {
        [key: string]: PlanCurrencyStats;
      };
    };
  };
  today: {
    today_visits: number;
    today_registers: number;
    today_generations: number;
    today_payments: number;
    today_payments_by_currency: {
      [key: string]: {
        count: number;
        revenue: number;
      };
    };
  };
  funnel: FunnelStats;
}

interface DailyStats {
  date: string;
  visits: number;
  registers: number;
  generations: number;
  payments: number;
  payments_by_currency: {
    [key: string]: {
      count: number;
      revenue: number;
    };
  };
}

export const DavidPage: React.FC = () => {
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);
  const [site, setSite] = useState<string>('');

  useEffect(() => {
    fetchStats();
  }, [days, site]);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);

      const siteParam = site ? `&site=${site}` : '';

      // 获取概览数据
      const overviewRes = await fetch(`/api/admin/stats/overview${site ? `?site=${site}` : ''}`);
      if (!overviewRes.ok) throw new Error('获取概览数据失败');
      const overviewData = await overviewRes.json();
      setOverview(overviewData.data);

      // 获取每日数据
      const dailyRes = await fetch(`/api/admin/stats/daily?days=${days}${siteParam}`);
      if (!dailyRes.ok) throw new Error('获取每日数据失败');
      const dailyData = await dailyRes.json();
      setDailyStats(dailyData.data.stats);

    } catch (err) {
      setError(err instanceof Error ? err.message : '加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('zh-CN').format(num);
  };

  const formatCurrency = (num: number, currency: string = 'CNY') => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: currency
    }).format(num);
  };

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    subtitle?: string;
    color?: string;
  }> = ({ title, value, subtitle, color = 'blue' }) => (
    <div className="stat-card">
      <div className="stat-title">{title}</div>
      <div className={`stat-value stat-${color}`}>{value}</div>
      {subtitle && <div className="stat-subtitle">{subtitle}</div>}
    </div>
  );

  if (loading) {
    return (
      <div className="david-page">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>加载数据中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="david-page">
        <div className="error-container">
          <p>{error}</p>
          <button onClick={fetchStats} className="retry-btn">重试</button>
        </div>
      </div>
    );
  }

  if (!overview) {
    return null;
  }

  const cnyStats = overview.payments.by_currency?.CNY || { total_orders: 0, total_revenue: 0 };
  const usdStats = overview.payments.by_currency?.USD || { total_orders: 0, total_revenue: 0 };

  const todayCny = overview.today.today_payments_by_currency?.CNY || { count: 0, revenue: 0 };
  const todayUsd = overview.today.today_payments_by_currency?.USD || { count: 0, revenue: 0 };
  const funnel = overview.funnel || {
    search_uv: 0,
    preview_to_matrix_rate: 0,
    matrix_to_review_rate: 0,
    total_credits_consumed: 0,
    daily_credit_rate: 0,
    preview_tasks: 0,
    matrix_tasks: 0,
    review_tasks: 0
  };

  return (
    <div className="david-page">
      <div className="david-container">
        <header className="david-header">
          <div className="david-header-row">
            <div>
              <h1>数据统计中心</h1>
              <p className="david-subtitle">实时监控系统运营数据</p>
            </div>
            <div className="site-tabs">
              {[
                { key: '', label: '全部' },
                { key: 'zh', label: '国内' },
                { key: 'en', label: '海外' },
              ].map(tab => (
                <button
                  key={tab.key}
                  className={`site-tab ${site === tab.key ? 'active' : ''}`}
                  onClick={() => setSite(tab.key)}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </header>

        {/* 北极星指标 */}
        <section className="david-section">
          <h2 className="section-title">北极星指标 (近30天)</h2>
          <div className="stats-grid">
            <StatCard
              title="搜索 UV"
              value={formatNumber(funnel.search_uv)}
              subtitle="获客能力与引流渠道质量"
              color="blue"
            />
            <StatCard
              title="预览 → 矩阵转化率"
              value={`${funnel.preview_to_matrix_rate}%`}
              subtitle={`目标 >15% | 预览 ${formatNumber(funnel.preview_tasks)} → 矩阵 ${formatNumber(funnel.matrix_tasks)}`}
              color={funnel.preview_to_matrix_rate >= 15 ? 'green' : 'orange'}
            />
            <StatCard
              title="矩阵 → 综述转化率"
              value={`${funnel.matrix_to_review_rate}%`}
              subtitle={`目标 >30% | 矩阵 ${formatNumber(funnel.matrix_tasks)} → 综述 ${formatNumber(funnel.review_tasks)}`}
              color={funnel.matrix_to_review_rate >= 30 ? 'green' : 'orange'}
            />
            <StatCard
              title="Credits 消耗速率"
              value={`${formatNumber(funnel.daily_credit_rate)}/天`}
              subtitle={`近30天总消耗 ${formatNumber(funnel.total_credits_consumed)} credits`}
              color="purple"
            />
          </div>
        </section>

        {/* 概览卡片 */}
        <section className="david-section">
          <h2 className="section-title">数据概览</h2>
          <div className="stats-grid">
            <StatCard
              title="总访问量"
              value={formatNumber(overview.visits.total)}
              subtitle={`今日 +${formatNumber(overview.visits.today)}`}
              color="blue"
            />
            <StatCard
              title="总注册量"
              value={formatNumber(overview.registers.total)}
              subtitle={`今日 +${formatNumber(overview.registers.today)}`}
              color="green"
            />
            <StatCard
              title="总生成数"
              value={formatNumber(overview.generations.total)}
              subtitle={`免费 ${formatNumber(overview.generations.free)} | 付费 ${formatNumber(overview.generations.paid)}`}
              color="purple"
            />
            <StatCard
              title="总收入 (CNY)"
              value={formatCurrency(cnyStats.total_revenue, 'CNY')}
              subtitle={`共 ${cnyStats.total_orders} 笔订单`}
              color="orange"
            />
            <StatCard
              title="总收入 (USD)"
              value={formatCurrency(usdStats.total_revenue, 'USD')}
              subtitle={`共 ${usdStats.total_orders} 笔订单`}
              color="teal"
            />
          </div>
        </section>

        {/* 今日数据 */}
        <section className="david-section">
          <h2 className="section-title">今日数据</h2>
          <div className="today-grid">
            <div className="today-item">
              <span className="today-label">访问量</span>
              <span className="today-value">{formatNumber(overview.today.today_visits)}</span>
            </div>
            <div className="today-item">
              <span className="today-label">注册量</span>
              <span className="today-value">{formatNumber(overview.today.today_registers)}</span>
            </div>
            <div className="today-item">
              <span className="today-label">生成数</span>
              <span className="today-value">{formatNumber(overview.today.today_generations)}</span>
            </div>
            <div className="today-item">
              <span className="today-label">付费数 (CNY)</span>
              <span className="today-value">{formatNumber(todayCny.count)}</span>
            </div>
            <div className="today-item">
              <span className="today-label">收入 (CNY)</span>
              <span className="today-value today-revenue">{formatCurrency(todayCny.revenue, 'CNY')}</span>
            </div>
            <div className="today-item">
              <span className="today-label">付费数 (USD)</span>
              <span className="today-value">{formatNumber(todayUsd.count)}</span>
            </div>
            <div className="today-item">
              <span className="today-label">收入 (USD)</span>
              <span className="today-value today-revenue">{formatCurrency(todayUsd.revenue, 'USD')}</span>
            </div>
          </div>
        </section>

        {/* 套餐统计 */}
        <section className="david-section">
          <h2 className="section-title">套餐统计 (CNY)</h2>
          <div className="plans-grid">
            {Object.entries(overview.payments.by_plan).map(([type, currencyData]: [string, any]) => (
              <div key={type} className="plan-card">
                <div className="plan-name">{currencyData.CNY?.name || type}</div>
                <div className="plan-stats">
                  <div className="plan-stat">
                    <span className="plan-label">订单数</span>
                    <span className="plan-number">{formatNumber(currencyData.CNY?.count || 0)}</span>
                  </div>
                  <div className="plan-stat">
                    <span className="plan-label">收入</span>
                    <span className="plan-number plan-revenue">{formatCurrency(currencyData.CNY?.revenue || 0, 'CNY')}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 套餐统计 USD */}
        <section className="david-section">
          <h2 className="section-title">套餐统计 (USD)</h2>
          <div className="plans-grid">
            {Object.entries(overview.payments.by_plan).map(([type, currencyData]: [string, any]) => (
              <div key={`${type}-usd`} className="plan-card">
                <div className="plan-name">{currencyData.USD?.name || type}</div>
                <div className="plan-stats">
                  <div className="plan-stat">
                    <span className="plan-label">订单数</span>
                    <span className="plan-number">{formatNumber(currencyData.USD?.count || 0)}</span>
                  </div>
                  <div className="plan-stat">
                    <span className="plan-label">收入</span>
                    <span className="plan-number plan-revenue">{formatCurrency(currencyData.USD?.revenue || 0, 'USD')}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 每日趋势 */}
        <section className="david-section">
          <div className="trend-header">
            <h2 className="section-title">每日趋势</h2>
            <div className="days-selector">
              <button
                className={`days-btn ${days === 7 ? 'active' : ''}`}
                onClick={() => setDays(7)}
              >7天</button>
              <button
                className={`days-btn ${days === 30 ? 'active' : ''}`}
                onClick={() => setDays(30)}
              >30天</button>
              <button
                className={`days-btn ${days === 90 ? 'active' : ''}`}
                onClick={() => setDays(90)}
              >90天</button>
            </div>
          </div>

          <div className="trend-table-container">
            <table className="trend-table">
              <thead>
                <tr>
                  <th>日期</th>
                  <th>访问量</th>
                  <th>注册量</th>
                  <th>生成数</th>
                  <th>付费数</th>
                  <th>收入 (CNY)</th>
                  <th>收入 (USD)</th>
                </tr>
              </thead>
              <tbody>
                {dailyStats.map((day) => {
                  const dayCny = day.payments_by_currency?.CNY || { count: 0, revenue: 0 };
                  const dayUsd = day.payments_by_currency?.USD || { count: 0, revenue: 0 };
                  return (
                    <tr key={day.date}>
                      <td>{day.date}</td>
                      <td>{formatNumber(day.visits)}</td>
                      <td>{formatNumber(day.registers)}</td>
                      <td>{formatNumber(day.generations)}</td>
                      <td>{formatNumber(day.payments)}</td>
                      <td className="trend-revenue">{formatCurrency(dayCny.revenue, 'CNY')}</td>
                      <td className="trend-revenue">{formatCurrency(dayUsd.revenue, 'USD')}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <style>{`
        .david-page {
          min-height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 40px 20px;
        }

        .david-container {
          max-width: 1400px;
          margin: 0 auto;
        }

        .david-header {
          color: white;
          margin-bottom: 40px;
        }

        .david-header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .david-header h1 {
          font-size: 2.5rem;
          font-weight: 700;
          margin-bottom: 10px;
        }

        .david-subtitle {
          font-size: 1.1rem;
          opacity: 0.9;
        }

        .site-tabs {
          display: flex;
          gap: 8px;
          background: rgba(255,255,255,0.15);
          border-radius: 10px;
          padding: 4px;
        }

        .site-tab {
          padding: 8px 20px;
          border: none;
          border-radius: 8px;
          font-size: 0.9rem;
          font-weight: 500;
          cursor: pointer;
          background: transparent;
          color: rgba(255,255,255,0.7);
          transition: all 0.2s;
        }

        .site-tab:hover {
          color: white;
          background: rgba(255,255,255,0.1);
        }

        .site-tab.active {
          background: white;
          color: #1a1a2e;
          font-weight: 600;
        }

        .david-section {
          background: white;
          border-radius: 16px;
          padding: 30px;
          margin-bottom: 30px;
          box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }

        .section-title {
          font-size: 1.5rem;
          font-weight: 600;
          margin-bottom: 25px;
          color: #333;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
        }

        .stat-card {
          padding: 25px;
          border-radius: 12px;
          background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }

        .stat-title {
          font-size: 0.9rem;
          color: #666;
          margin-bottom: 10px;
        }

        .stat-value {
          font-size: 2rem;
          font-weight: 700;
          margin-bottom: 8px;
        }

        .stat-blue { color: #2196F3; }
        .stat-green { color: #4CAF50; }
        .stat-purple { color: #9C27B0; }
        .stat-orange { color: #FF9800; }
        .stat-teal { color: #009688; }

        .stat-subtitle {
          font-size: 0.85rem;
          color: #888;
        }

        .today-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 15px;
        }

        .today-item {
          text-align: center;
          padding: 20px;
          background: #f8f9fa;
          border-radius: 10px;
        }

        .today-label {
          display: block;
          font-size: 0.9rem;
          color: #666;
          margin-bottom: 8px;
        }

        .today-value {
          display: block;
          font-size: 1.5rem;
          font-weight: 600;
          color: #333;
        }

        .today-revenue {
          color: #4CAF50;
        }

        .plans-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
        }

        .plan-card {
          padding: 20px;
          background: linear-gradient(135deg, #e0eafe 0%, #f0f4ff 100%);
          border-radius: 10px;
        }

        .plan-name {
          font-size: 1.1rem;
          font-weight: 600;
          color: #333;
          margin-bottom: 15px;
        }

        .plan-stats {
          display: flex;
          justify-content: space-between;
        }

        .plan-stat {
          text-align: center;
        }

        .plan-label {
          display: block;
          font-size: 0.8rem;
          color: #666;
          margin-bottom: 5px;
        }

        .plan-number {
          display: block;
          font-size: 1.1rem;
          font-weight: 600;
          color: #333;
        }

        .plan-revenue {
          color: #4CAF50;
        }

        .trend-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .days-selector {
          display: flex;
          gap: 10px;
        }

        .days-btn {
          padding: 8px 20px;
          border: 1px solid #ddd;
          background: white;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .days-btn:hover {
          background: #f5f5f5;
        }

        .days-btn.active {
          background: #2196F3;
          color: white;
          border-color: #2196F3;
        }

        .trend-table-container {
          overflow-x: auto;
        }

        .trend-table {
          width: 100%;
          border-collapse: collapse;
        }

        .trend-table th,
        .trend-table td {
          padding: 12px 15px;
          text-align: left;
          border-bottom: 1px solid #eee;
        }

        .trend-table th {
          background: #f8f9fa;
          font-weight: 600;
          color: #666;
        }

        .trend-table tbody tr:hover {
          background: #f8f9fa;
        }

        .trend-revenue {
          color: #4CAF50;
          font-weight: 600;
        }

        .loading-container,
        .error-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 400px;
          color: white;
        }

        .spinner {
          width: 50px;
          height: 50px;
          border: 4px solid rgba(255,255,255,0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .retry-btn {
          margin-top: 20px;
          padding: 12px 30px;
          background: white;
          color: #667eea;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 600;
        }

        @media (max-width: 768px) {
          .david-header h1 {
            font-size: 1.8rem;
          }

          .stats-grid {
            grid-template-columns: 1fr;
          }

          .today-grid {
            grid-template-columns: repeat(2, 1fr);
          }

          .trend-header {
            flex-direction: column;
            gap: 15px;
            align-items: flex-start;
          }
        }
      `}</style>
    </div>
  );
};
