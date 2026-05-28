import type { CaseGrade, CaseSummary } from "../../types/reguthink-api";

export type CaseFilter = "all" | "ge70" | "lt70" | "weak" | CaseGrade;

type CaseRailProps = {
  cases: CaseSummary[];
  selectedCaseId: string;
  query: string;
  filter: CaseFilter;
  onQueryChange: (query: string) => void;
  onFilterChange: (filter: CaseFilter) => void;
  onSelectCase: (caseId: string) => void;
};

const FILTERS: Array<[CaseFilter, string]> = [
  ["all", "all"],
  ["ge70", ">=70"],
  ["lt70", "<70"],
  ["weak", "weak"],
  ["B", "B"],
  ["C", "C"],
  ["D", "D"],
  ["F", "F"],
];

export function filterCases(cases: CaseSummary[], query: string, filter: CaseFilter) {
  const normalizedQuery = query.trim().toLowerCase();
  return cases.filter((item) => {
    const matchesQuery =
      !normalizedQuery ||
      item.case_id.toLowerCase().includes(normalizedQuery) ||
      item.main_issue.toLowerCase().includes(normalizedQuery);
    const matchesFilter =
      filter === "all" ||
      (filter === "ge70" && item.ge_70) ||
      (filter === "lt70" && !item.ge_70) ||
      (filter === "weak" && (item.final_score < 70 || item.main_issue.includes("不足") || item.main_issue.includes("缺"))) ||
      item.grade === filter;
    return matchesQuery && matchesFilter;
  });
}

export function CaseRail({
  cases,
  selectedCaseId,
  query,
  filter,
  onQueryChange,
  onFilterChange,
  onSelectCase,
}: CaseRailProps) {
  const visibleCases = filterCases(cases, query, filter);
  const lowScoreCount = cases.filter((item) => !item.ge_70).length;

  return (
    <aside className="wb-case-rail" aria-label="case rail">
      <button className="wb-new-diagnostic" type="button">新建诊断</button>
      <div className="wb-rail-search">
        <input
          aria-label="search cases"
          placeholder="搜索 case / weakness"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
        />
      </div>
      <div className="wb-filter-row" aria-label="case filters">
        {FILTERS.map(([key, label]) => (
          <button
            className={filter === key ? "active" : ""}
            key={key}
            type="button"
            onClick={() => onFilterChange(key)}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="wb-rail-meta">
        <span>{visibleCases.length} / {cases.length} cases</span>
        <span className="warn">{lowScoreCount} low-score visible</span>
      </div>
      <div className="wb-case-list">
        {visibleCases.map((item) => (
          <button
            className={item.case_id === selectedCaseId ? "wb-case-card active" : "wb-case-card"}
            key={item.case_id}
            type="button"
            onClick={() => onSelectCase(item.case_id)}
          >
            <span className="wb-case-id">{item.case_id}</span>
            <span className="wb-case-row">
              <strong>{item.final_score}</strong>
              <span>{item.grade}</span>
              <span>{item.ge_70 ? ">=70" : "<70 warning"}</span>
            </span>
            <span className="wb-case-weakness">{item.main_issue}</span>
          </button>
        ))}
      </div>
    </aside>
  );
}
