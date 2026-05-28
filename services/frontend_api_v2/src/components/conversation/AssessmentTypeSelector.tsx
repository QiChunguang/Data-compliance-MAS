import type { AssessmentType, AssessmentTypeInfo } from "../../types/reguthink-interactive-api";

type Props = {
  value: AssessmentType;
  types: AssessmentTypeInfo[];
  onChange: (value: AssessmentType) => void;
};

export function AssessmentTypeSelector({ value, types, onChange }: Props) {
  return (
    <label className="assessment-select">
      <span>Assessment type</span>
      <select value={value} onChange={(event) => onChange(event.target.value as AssessmentType)}>
        {types.map((item) => (
          <option key={item.assessment_type} value={item.assessment_type}>
            {item.label || item.assessment_type}
          </option>
        ))}
      </select>
    </label>
  );
}
