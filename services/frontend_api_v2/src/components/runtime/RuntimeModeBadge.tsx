import type { RuntimeMode } from "../../types/reguthink-interactive-api";

export function RuntimeModeBadge({ mode }: { mode: RuntimeMode }) {
  return <span className={mode === "dry_run" ? "wb-chip warning" : "wb-chip danger"}>{mode}</span>;
}
