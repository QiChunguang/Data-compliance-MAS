import React from 'react';

type ProductWelcomePanelProps = {
  onSelectAssessment: (type: string) => void;
};

const QUICK_TASKS = [
  {
    id: 'data_transaction_compliance',
    title: '数据交易合规评估',
    description: '评估数据交易场景的合规性风险',
  },
  {
    id: 'data_flow_security_review',
    title: '数据流通安全审查',
    description: '审查数据流通的安全风险',
  },
  {
    id: 'cross_border_data_transfer',
    title: '跨境数据传输评估',
    description: '评估跨境数据传输的合规性',
  },
  {
    id: 'pipl_personal_information_protection',
    title: 'PIPL 个人信息保护',
    description: '评估个人信息保护合规性',
  },
];

export const ProductWelcomePanel: React.FC<ProductWelcomePanelProps> = ({
  onSelectAssessment,
}) => {
  return (
    <div className="product-welcome-panel">
      <div className="product-welcome-icon">
        <div className="product-welcome-icon-inner">
          <span className="product-welcome-icon-symbol">🧩</span>
        </div>
      </div>

      <h1 className="product-welcome-title">您好，有什么可以帮您？</h1>
      <p className="product-welcome-subtitle">选择评估类型开始进行合规评估</p>

      <div className="product-quick-tasks-grid">
        {QUICK_TASKS.map((task) => (
          <button
            key={task.id}
            className="product-quick-task-card"
            type="button"
            onClick={() => onSelectAssessment(task.id)}
          >
            <span className="product-quick-task-title">{task.title}</span>
            <span className="product-quick-task-desc">{task.description}</span>
          </button>
        ))}
      </div>

      <div className="product-welcome-footer">
        <div className="product-welcome-hint">
          <span className="product-welcome-hint-badge">提示</span>
          <span className="product-welcome-hint-text">
            当前输出为非正式合规辅助分析。上传材料仅作为业务事实，不写入法规知识库。
          </span>
        </div>
      </div>
    </div>
  );
};
