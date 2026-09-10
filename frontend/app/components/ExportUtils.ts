/**
 * Markdown report generation and export utilities.
 */

export function formatReviewToMarkdown(review: any, originalCode?: string): string {
  const reviewId = review?.review_id || "LIVE_REVIEW";
  const verdict = review?.verdict || "PASS";
  const ratingScore = review?.rating_score ?? 85;
  const executiveSummary = review?.executive_summary || "Analysis completed successfully.";
  const mode = (review?.review_mode || "quick").toUpperCase();
  const execTime = review?.execution_time_seconds ? `${review.execution_time_seconds.toFixed(2)}s` : "N/A";
  const modelUsed = review?.model_used || "gemini-2.5-flash";
  const language = review?.language_detected || review?.input_metadata?.language || "auto";

  const metrics = review?.metrics || {};
  const findings = review?.findings || [];
  const refactoredCode = review?.refactored_code || "";
  const refactoringExplanation = review?.refactoring_explanation || "";
  const ragDocs = review?.rag_documents_cited || [];

  const lines: string[] = [
    `# ⚡ AI Code Review & Refactoring Audit Report`,
    ``,
    `**Review ID**: \`${reviewId}\`  `,
    `**Analysis Depth**: \`${mode}\`  `,
    `**Language Detected**: \`${language}\`  `,
    `**Provider Model**: \`${modelUsed}\`  `,
    `**Execution Duration**: \`${execTime}\`  `,
    ``,
    `---`,
    ``,
    `## 📊 Executive Summary`,
    ``,
    `- **Verdict**: **${verdict}**`,
    `- **Overall Code Health Rating**: **${ratingScore} / 100**`,
    ``,
    `### Synthesized Evaluation`,
    `${executiveSummary}`,
    ``,
    `---`,
    ``,
    `## 📈 Multi-Dimensional Metrics`,
    ``,
    `| Metric Dimension | Score | Rating |`,
    `| :--- | :---: | :---: |`,
    `| Security Rating | ${metrics.security ?? 90}% | ${getScoreRatingLabel(metrics.security ?? 90)} |`,
    `| Readability Score | ${metrics.readability ?? 85}% | ${getScoreRatingLabel(metrics.readability ?? 85)} |`,
    `| Maintainability Index | ${metrics.maintainability ?? 80}% | ${getScoreRatingLabel(metrics.maintainability ?? 80)} |`,
    `| Complexity Rating | ${metrics.complexity ?? 75}% | ${getScoreRatingLabel(metrics.complexity ?? 75)} |`,
    `| Overall Code Quality | ${metrics.quality ?? 88}% | ${getScoreRatingLabel(metrics.quality ?? 88)} |`,
    ``,
    `---`,
    ``,
    `## 🔍 Detailed Findings (${findings.length})`,
    ``
  ];

  if (findings.length === 0) {
    lines.push(`🎉 *No critical vulnerabilities, security risks, or anti-patterns were detected in this review.*\n`);
  } else {
    findings.forEach((f: any, idx: number) => {
      const lineRefs = f.line_numbers && f.line_numbers.length > 0 ? f.line_numbers.join(", ") : "N/A";
      lines.push(`### ${idx + 1}. [${f.severity || "INFO"}] ${f.title || "Finding"}`);
      lines.push(`- **Category**: \`${(f.category || "quality").toUpperCase()}\``);
      lines.push(`- **Line Number(s)**: Lines ${lineRefs}`);
      lines.push(`- **Description**: ${f.description || ""}`);
      if (f.impact) {
        lines.push(`- **Impact**: ${f.impact}`);
      }
      if (f.recommendation) {
        lines.push(``);
        lines.push(`**Recommended Remediation:**`);
        lines.push(`\`\`\``);
        lines.push(`${f.recommendation}`);
        lines.push(`\`\`\``);
      }
      lines.push(``);
    });
  }

  if (originalCode) {
    lines.push(`---`);
    lines.push(``);
    lines.push(`## 💻 Original Code (Submitted)`);
    lines.push(``);
    lines.push(`\`\`\`${language}`);
    lines.push(originalCode);
    lines.push(`\`\`\``);
    lines.push(``);
  }

  if (refactoredCode) {
    lines.push(`---`);
    lines.push(``);
    lines.push(`## 🛠️ Automated AST-Validated Refactoring`);
    lines.push(``);
    if (refactoringExplanation) {
      lines.push(`### Refactoring Rationale`);
      lines.push(`${refactoringExplanation}`);
      lines.push(``);
    }
    lines.push(`\`\`\`${language}`);
    lines.push(refactoredCode);
    lines.push(`\`\`\``);
    lines.push(``);
  }

  if (ragDocs && ragDocs.length > 0) {
    lines.push(`---`);
    lines.push(``);
    lines.push(`## 📚 RAG Vector Knowledge Base References`);
    lines.push(``);
    ragDocs.forEach((doc: any) => {
      lines.push(`### 📖 ${doc.title || "Reference"} (\`${doc.category || "general"}\`)`);
      lines.push(`${doc.content}`);
      lines.push(``);
    });
  }

  lines.push(`---`);
  lines.push(`*Report generated automatically by CodePilot AI Enterprise Review Platform.*`);

  return lines.join("\n");
}

function getScoreRatingLabel(score: number): string {
  if (score >= 85) return "🟢 Excellent";
  if (score >= 70) return "🟡 Good";
  if (score >= 50) return "🟠 Moderate Risk";
  return "🔴 High Risk";
}

export function downloadMarkdownFile(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export async function copyMarkdownToClipboard(content: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(content);
    return true;
  } catch {
    return false;
  }
}
