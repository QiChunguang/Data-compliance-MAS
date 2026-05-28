import type { ReactNode } from "react";

export type JsonRecord = Record<string, unknown>;

export function asRecord(value: unknown): JsonRecord | null {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as JsonRecord) : null;
}

export function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

export function fieldText(record: JsonRecord | null | undefined, keys: string[], fallback = "missing / placeholder") {
  if (!record) {
    return fallback;
  }
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
    if (typeof value === "number" || typeof value === "boolean") {
      return String(value);
    }
  }
  return fallback;
}

export function JsonPreview({ value, maxHeight = 300 }: { value: unknown; maxHeight?: number }) {
  if (value === null || value === undefined) {
    return <div className="wb-placeholder">missing / placeholder</div>;
  }
  return (
    <pre className="wb-json" style={{ maxHeight }}>
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

export function PanelNote({ children }: { children: ReactNode }) {
  return <div className="wb-panel-note">{children}</div>;
}
