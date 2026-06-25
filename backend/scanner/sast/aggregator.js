/**
 * CodeGuard AI - Vulnerability Aggregator
 * Deduplicates findings and produces final report.
 */

class VulnerabilityAggregator {
  /** Deduplicate findings by CWE + file + line */
  aggregate(findings) {
    const deduped = new Map();

    for (const finding of findings) {
      const key = this._dedupKey(finding);
      const existing = deduped.get(key);

      if (!existing) {
        deduped.set(key, finding);
      } else {
        // Keep the finding with higher confidence or richer data
        if ((finding.confidence || 0) > (existing.confidence || 0)) {
          deduped.set(key, finding);
        }
        // Merge data flow if existing has none but new one does
        if (finding.data_flow && !existing.data_flow) {
          existing.data_flow = finding.data_flow;
        }
      }
    }

    return Array.from(deduped.values());
  }

  _dedupKey(finding) {
    const cwe = finding.cwe_id || "unknown";
    const file = finding.file_path || "unknown";
    const line = finding.line_start || finding.line_number || 0;
    return `${cwe}:${file}:${line}`;
  }

  /** Group findings by severity */
  groupBySeverity(findings) {
    const groups = { critical: [], high: [], medium: [], low: [], info: [] };
    for (const f of findings) {
      const sev = (f.severity || "medium").toLowerCase();
      if (groups[sev]) groups[sev].push(f);
      else groups.medium.push(f);
    }
    return groups;
  }
}

module.exports = { VulnerabilityAggregator };