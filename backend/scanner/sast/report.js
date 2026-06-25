/**
 * CodeGuard AI - Report Generator
 * Produces structured JSON output compatible with the CodeGuard scan pipeline.
 */

function generateReport(findings, filePath) {
  const bySeverity = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
  for (const f of findings) {
    const sev = (f.severity || "medium").toLowerCase();
    if (bySeverity[sev] !== undefined) bySeverity[sev]++;
    else bySeverity.medium++;
  }

  return {
    scanner: "codeguard-sast-js",
    version: "2.0",
    file_path: filePath,
    scan_timestamp: new Date().toISOString(),
    summary: {
      total_findings: findings.length,
      by_severity: bySeverity,
    },
    findings: findings.map(f => ({
      vulnerability_type: f.vulnerability_type,
      severity: f.severity,
      cwe_id: f.cwe_id,
      title: f.title || f.vulnerability_type,
      description: f.description || "",
      file_path: f.file_path || filePath,
      line_number: f.line_number || f.line_start || 0,
      line_start: f.line_start || f.line_number || 0,
      line_end: f.line_end || f.line_start || f.line_number || 0,
      code_snippet: f.code_snippet || "",
      confidence: typeof f.confidence === "number" ? Math.round(f.confidence * 100) / 100 : 0.7,
      analyzer_type: "sast-js",
      data_flow: f.data_flow || null,
      remediation: f.remediation || "",
      finding_metadata: f.finding_metadata || {},
    })),
  };
}

module.exports = { generateReport };