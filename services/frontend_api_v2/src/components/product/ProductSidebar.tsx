import React from 'react';
import type { HealthResponse } from '../../types/reguthink-api';

type ProductSidebarProps = {
  activeView: string;
  health: HealthResponse | null;
  onSelectView: (view: string) => void;
};

export const ProductSidebar: React.FC<ProductSidebarProps> = ({
  activeView,
  health,
  onSelectView,
}) => {
  const mainNavItems = [
    { key: 'chat', label: '智能对话', icon: '💬' },
    { key: 'agents', label: '智能体集群', icon: '🤖' },
    { key: 'knowledge', label: '知识图谱', icon: '🕸️' },
    { key: 'risk', label: '风险雷达', icon: '📡' },
    { key: 'import', label: '数据导入', icon: '📥' },
  ];

  const secondaryNavItems = [
    { key: 'jobs', label: '运行任务', icon: '⚡' },
    { key: 'report', label: '报告中心', icon: '📊' },
    { key: 'boundaries', label: '系统边界', icon: '⚙️' },
  ];

  const debugNavItems = [
    { key: 'matrix', label: '案例矩阵', icon: '🧪' },
  ];

  return (
    <aside className="product-sidebar">
      <div className="product-logo">
        <div className="product-logo-mark">RT</div>
        <span className="product-logo-text">ReguThink</span>
      </div>

      <nav className="product-nav">
        {mainNavItems.map((item) => (
          <button
            key={item.key}
            className={`product-nav-item ${activeView === item.key ? 'active' : ''}`}
            type="button"
            onClick={() => onSelectView(item.key)}
          >
            <span className="product-nav-icon">{item.icon}</span>
            <span className="product-nav-label">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="product-nav-divider"></div>

      <nav className="product-nav secondary">
        {secondaryNavItems.map((item) => (
          <button
            key={item.key}
            className={`product-nav-item ${activeView === item.key ? 'active' : ''}`}
            type="button"
            onClick={() => onSelectView(item.key)}
          >
            <span className="product-nav-icon">{item.icon}</span>
            <span className="product-nav-label">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="product-nav-divider"></div>

      <nav className="product-nav debug">
        {debugNavItems.map((item) => (
          <button
            key={item.key}
            className={`product-nav-item debug ${activeView === item.key ? 'active' : ''}`}
            type="button"
            onClick={() => onSelectView(item.key)}
          >
            <span className="product-nav-icon">{item.icon}</span>
            <span className="product-nav-label">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="product-status">
        <span className={`product-status-light ${health?.ok ? 'on' : ''}`}></span>
        <span className="product-status-text">
          {health?.ok ? '已连接' : '未连接'}
        </span>
      </div>
    </aside>
  );
};
