import type { AlertStatus, CameraStatus, IncidentStatus, Severity } from "./types";

// Colors come from the dataviz skill's fixed status palette (good/warning/serious/
// critical), mapped onto LOW/MEDIUM/HIGH/CRITICAL — see tailwind.config.ts "severity".
// Status color is always paired with the text label, never carries meaning alone.
export const severityStyles: Record<Severity, { text: string; bg: string; dot: string }> = {
  LOW: { text: "text-severity-low", bg: "bg-severity-low/10 border-severity-low/30", dot: "bg-severity-low" },
  MEDIUM: {
    text: "text-severity-medium",
    bg: "bg-severity-medium/10 border-severity-medium/30",
    dot: "bg-severity-medium",
  },
  HIGH: { text: "text-severity-high", bg: "bg-severity-high/10 border-severity-high/30", dot: "bg-severity-high" },
  CRITICAL: {
    text: "text-severity-critical",
    bg: "bg-severity-critical/10 border-severity-critical/30",
    dot: "bg-severity-critical",
  },
};

export const cameraStatusStyles: Record<CameraStatus, { text: string; dot: string; label: string }> = {
  ONLINE: { text: "text-severity-low", dot: "bg-severity-low", label: "LIVE" },
  OFFLINE: { text: "text-slate-500", dot: "bg-slate-500", label: "OFFLINE" },
  ERROR: { text: "text-severity-critical", dot: "bg-severity-critical", label: "ERROR" },
  PROCESSING: { text: "text-sky-400", dot: "bg-sky-400", label: "PROCESSING" },
};

export const alertStatusLabels: Record<AlertStatus, string> = {
  NEW: "New",
  REVIEWED: "Reviewed",
  DISMISSED: "Dismissed",
  ESCALATED: "Escalated",
};

export const incidentStatusLabels: Record<IncidentStatus, string> = {
  UNREVIEWED: "Unreviewed",
  UNDER_REVIEW: "Under Review",
  CONFIRMED: "Confirmed",
  DISMISSED: "Dismissed",
};

export function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}
