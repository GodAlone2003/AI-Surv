import { severityStyles, cameraStatusStyles, formatTime } from "./style";

describe("severityStyles", () => {
  it("has an entry for every severity level", () => {
    expect(Object.keys(severityStyles).sort()).toEqual(["CRITICAL", "HIGH", "LOW", "MEDIUM"]);
  });
});

describe("cameraStatusStyles", () => {
  it("labels ONLINE as LIVE", () => {
    expect(cameraStatusStyles.ONLINE.label).toBe("LIVE");
  });
  it("labels OFFLINE distinctly from ONLINE", () => {
    expect(cameraStatusStyles.OFFLINE.label).not.toBe(cameraStatusStyles.ONLINE.label);
  });
});

describe("formatTime", () => {
  it("formats an ISO timestamp as a time string", () => {
    const result = formatTime("2026-01-01T14:32:18.000Z");
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });
});
