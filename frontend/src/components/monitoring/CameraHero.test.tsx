import { render, screen } from "@testing-library/react";
import { CameraHero } from "./CameraHero";
import type { Camera } from "@/lib/types";

const baseCamera: Camera = {
  id: "cam-1",
  name: "Camera 01",
  location: "Main Monitoring Camera",
  streamUrl: "webcam://0",
  status: "OFFLINE",
  isDemo: false,
  createdAt: "2026-01-01T00:00:00.000Z",
  updatedAt: "2026-01-01T00:00:00.000Z",
};

const defaultProps = {
  recentDetections: [],
  latestAction: null,
  latestAlert: null,
  aiServiceReachable: false,
  backendReachable: true,
  wsConnected: false,
};

describe("CameraHero", () => {
  it("renders the camera name and location", () => {
    render(<CameraHero camera={baseCamera} {...defaultProps} />);
    expect(screen.getByText(/Camera 01/)).toBeInTheDocument();
    expect(screen.getByText(/Main Monitoring Camera/)).toBeInTheDocument();
  });

  it("shows the honest CAMERA NOT CONNECTED empty state when offline — never a fake feed", () => {
    render(<CameraHero camera={baseCamera} {...defaultProps} />);
    expect(screen.getByText("CAMERA NOT CONNECTED")).toBeInTheDocument();
    expect(screen.getByText(/No live video stream/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Connect Camera/i })).toHaveAttribute("href", "/cameras");
  });

  it("shows the AI-active-no-preview state when the camera is ONLINE, not a fabricated video", () => {
    render(<CameraHero camera={{ ...baseCamera, status: "ONLINE" }} {...defaultProps} />);
    expect(screen.getByText(/AI analysis active — no video preview/)).toBeInTheDocument();
    expect(screen.queryByText("CAMERA NOT CONNECTED")).not.toBeInTheDocument();
  });

  it("shows a DEMO badge when the camera is flagged isDemo", () => {
    render(<CameraHero camera={{ ...baseCamera, isDemo: true }} {...defaultProps} />);
    expect(screen.getByText("DEMO")).toBeInTheDocument();
  });

  it("does not fabricate activity when nothing has been detected yet", () => {
    render(<CameraHero camera={baseCamera} {...defaultProps} />);
    expect(screen.getByText("No detections yet")).toBeInTheDocument();
    expect(screen.getByText("No active alert")).toBeInTheDocument();
  });

  it("renders real detection counts when provided", () => {
    render(
      <CameraHero
        camera={baseCamera}
        {...defaultProps}
        recentDetections={[
          { id: "d1", cameraId: "cam-1", objectLabel: "person", confidence: 0.9, boundingBox: "[]", mode: "REAL", frameTimestamp: "2026-01-01T00:00:00.000Z", createdAt: "2026-01-01T00:00:00.000Z" },
          { id: "d2", cameraId: "cam-1", objectLabel: "person", confidence: 0.9, boundingBox: "[]", mode: "REAL", frameTimestamp: "2026-01-01T00:00:00.000Z", createdAt: "2026-01-01T00:00:00.000Z" },
        ]}
      />
    );
    expect(screen.getByText("person × 2")).toBeInTheDocument();
  });

  it("badges the Threat Assessment section DEMO when the underlying alert is simulated — never lets a demo escalation look real", () => {
    render(
      <CameraHero
        camera={baseCamera}
        {...defaultProps}
        latestAlert={{
          id: "a1",
          cameraId: "cam-1",
          type: "fighting_candidate",
          severity: "CRITICAL",
          confidence: 0.6,
          description: "Sustained aggressive contact — potential fight detected.",
          status: "NEW",
          mode: "DEMO",
          threatScore: 0.9,
          createdAt: "2026-01-01T00:00:00.000Z",
          updatedAt: "2026-01-01T00:00:00.000Z",
        }}
      />
    );
    expect(screen.getByText("DEMO")).toBeInTheDocument();
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
  });

  it("reflects real system status connectivity, not assumed-good defaults", () => {
    render(<CameraHero camera={baseCamera} {...defaultProps} aiServiceReachable={false} wsConnected={false} />);
    const unavailable = screen.getAllByText("Unavailable");
    expect(unavailable.length).toBeGreaterThan(0);
  });
});
