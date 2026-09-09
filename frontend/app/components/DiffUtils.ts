/**
 * Line-by-line diff computation utility using Longest Common Subsequence (LCS).
 */

export interface DiffLine {
  type: "added" | "deleted" | "unchanged";
  originalLineNumber?: number;
  refactoredLineNumber?: number;
  content: string;
}

export interface DiffStats {
  additions: number;
  deletions: number;
  unchanged: number;
  totalOriginalLines: number;
  totalRefactoredLines: number;
}

export interface DiffResult {
  lines: DiffLine[];
  stats: DiffStats;
}

/**
 * Computes line-by-line diff between original text and refactored text.
 */
export function computeLineDiff(original: string, refactored: string): DiffResult {
  const origLines = original ? original.split("\n") : [];
  const refLines = refactored ? refactored.split("\n") : [];

  const n = origLines.length;
  const m = refLines.length;

  // Compute Longest Common Subsequence matrix
  const dp: number[][] = Array.from({ length: n + 1 }, () => Array(m + 1).fill(0));

  for (let i = 1; i <= n; i++) {
    for (let j = 1; j <= m; j++) {
      if (origLines[i - 1] === refLines[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  // Backtrack to reconstruct line diff sequence
  let i = n;
  let j = m;
  const result: DiffLine[] = [];
  let additions = 0;
  let deletions = 0;
  let unchanged = 0;

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && origLines[i - 1] === refLines[j - 1]) {
      result.unshift({
        type: "unchanged",
        originalLineNumber: i,
        refactoredLineNumber: j,
        content: origLines[i - 1],
      });
      i--;
      j--;
      unchanged++;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      result.unshift({
        type: "added",
        refactoredLineNumber: j,
        content: refLines[j - 1],
      });
      j--;
      additions++;
    } else if (i > 0 && (j === 0 || dp[i][j - 1] < dp[i - 1][j])) {
      result.unshift({
        type: "deleted",
        originalLineNumber: i,
        content: origLines[i - 1],
      });
      i--;
      deletions++;
    }
  }

  return {
    lines: result,
    stats: {
      additions,
      deletions,
      unchanged,
      totalOriginalLines: n,
      totalRefactoredLines: m,
    },
  };
}
