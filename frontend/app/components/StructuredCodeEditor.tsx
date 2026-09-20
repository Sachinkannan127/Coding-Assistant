"use client";

import React, { useState, useRef, useMemo, useEffect, useCallback } from "react";
import { Sparkles, Copy, Check, Trash2, Code2 } from "lucide-react";

export interface StructuredCodeEditorProps {
  code: string;
  setCode: (val: string) => void;
  language?: string;
  setLanguage?: (val: string) => void;
  height?: string;
  minHeight?: string;
  placeholder?: string;
  readOnly?: boolean;
  showToolbar?: boolean;
  extraHeaderControls?: React.ReactNode;
  extraFooterControls?: React.ReactNode;
}

export default function StructuredCodeEditor({
  code,
  setCode,
  language = "python",
  setLanguage,
  height,
  minHeight = "380px",
  placeholder = "// Write or paste code snippet here...",
  readOnly = false,
  showToolbar = true,
  extraHeaderControls,
  extraFooterControls,
}: StructuredCodeEditorProps) {
  const [tabSize, setTabSize] = useState<number>(language === "python" || language === "c" || language === "cpp" ? 4 : 2);
  const [fontSize, setFontSize] = useState<"sm" | "md" | "lg">("md");
  const [copied, setCopied] = useState<boolean>(false);
  const [cursorPos, setCursorPos] = useState<{ line: number; col: number }>({ line: 1, col: 1 });
  const [activeLine, setActiveLine] = useState<number>(1);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);

  // Sync tab size when language changes
  useEffect(() => {
    if (language === "python" || language === "c" || language === "cpp" || language === "java") {
      setTabSize(4);
    } else {
      setTabSize(2);
    }
  }, [language]);

  const lineCount = useMemo(() => {
    if (!code) return 1;
    return code.split("\n").length;
  }, [code]);

  const lineNumbers = useMemo(() => {
    return Array.from({ length: Math.max(lineCount, 14) }, (_, i) => i + 1);
  }, [lineCount]);

  // Synchronize scrolling between textarea and line numbers gutter
  const handleScroll = () => {
    if (textareaRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  };

  // Track cursor position (Line & Column) & Active Line
  const updateCursorPosition = useCallback(() => {
    if (!textareaRef.current) return;
    const { selectionStart } = textareaRef.current;
    const textBeforeCursor = code.substring(0, selectionStart);
    const lines = textBeforeCursor.split("\n");
    const currentLine = lines.length;
    const currentCol = lines[lines.length - 1].length + 1;

    setCursorPos({ line: currentLine, col: currentCol });
    setActiveLine(currentLine);
  }, [code]);

  useEffect(() => {
    updateCursorPosition();
  }, [code, updateCursorPosition]);

  // Advanced Keybindings: Tab, Shift+Tab, Enter auto-indent, Auto-closing brackets
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (readOnly) return;
    const textarea = textareaRef.current;
    if (!textarea) return;

    const { selectionStart, selectionEnd } = textarea;
    const indentSpaces = " ".repeat(tabSize);

    // 1. Tab & Shift+Tab handling
    if (e.key === "Tab") {
      e.preventDefault();

      if (selectionStart !== selectionEnd) {
        // Multi-line selection indent / outdent
        const startLineIdx = code.substring(0, selectionStart).lastIndexOf("\n") + 1;
        const endLineIdx = selectionEnd;
        const selectedText = code.substring(startLineIdx, endLineIdx);
        const lines = selectedText.split("\n");

        let modifiedLines: string[];
        if (e.shiftKey) {
          // Outdent
          modifiedLines = lines.map((line) => {
            if (line.startsWith(indentSpaces)) return line.substring(tabSize);
            if (line.startsWith("\t")) return line.substring(1);
            return line.replace(/^ +/, (m) => (m.length > tabSize ? m.substring(tabSize) : ""));
          });
        } else {
          // Indent
          modifiedLines = lines.map((line) => indentSpaces + line);
        }

        const newText =
          code.substring(0, startLineIdx) + modifiedLines.join("\n") + code.substring(endLineIdx);
        setCode(newText);

        setTimeout(() => {
          if (textarea) {
            textarea.selectionStart = startLineIdx;
            textarea.selectionEnd = startLineIdx + modifiedLines.join("\n").length;
          }
        }, 0);
      } else {
        // Single cursor indent / outdent
        if (e.shiftKey) {
          // Outdent line
          const lineStart = code.substring(0, selectionStart).lastIndexOf("\n") + 1;
          const currentLine = code.substring(lineStart, selectionStart);
          if (currentLine.endsWith(indentSpaces)) {
            const newText =
              code.substring(0, selectionStart - tabSize) + code.substring(selectionStart);
            setCode(newText);
            setTimeout(() => {
              if (textarea) {
                textarea.selectionStart = textarea.selectionEnd = selectionStart - tabSize;
              }
            }, 0);
          }
        } else {
          // Insert indent spaces
          const newText =
            code.substring(0, selectionStart) + indentSpaces + code.substring(selectionEnd);
          setCode(newText);
          setTimeout(() => {
            if (textarea) {
              textarea.selectionStart = textarea.selectionEnd = selectionStart + tabSize;
            }
          }, 0);
        }
      }
      return;
    }

    // 2. Enter key auto-indentation
    if (e.key === "Enter") {
      e.preventDefault();
      const lineStart = code.substring(0, selectionStart).lastIndexOf("\n") + 1;
      const currentLine = code.substring(lineStart, selectionStart);
      
      // Calculate leading spaces/tabs
      const match = currentLine.match(/^[\t ]*/);
      let indent = match ? match[0] : "";

      const trimmedLine = currentLine.trim();
      const lastChar = trimmedLine.slice(-1);
      
      // Auto-indent further if line ends with block openers: :, {, (, [
      if (lastChar === ":" || lastChar === "{" || lastChar === "(" || lastChar === "[") {
        indent += indentSpaces;
      }

      const charAfterCursor = code.charAt(selectionStart);
      const isBetweenBrackets =
        (lastChar === "{" && charAfterCursor === "}") ||
        (lastChar === "(" && charAfterCursor === ")") ||
        (lastChar === "[" && charAfterCursor === "]");

      let insertContent = "\n" + indent;
      let newCursorPos = selectionStart + insertContent.length;

      if (isBetweenBrackets) {
        const outerIndent = match ? match[0] : "";
        insertContent += "\n" + outerIndent;
      }

      const newText =
        code.substring(0, selectionStart) + insertContent + code.substring(selectionEnd);
      setCode(newText);

      setTimeout(() => {
        if (textarea) {
          textarea.selectionStart = textarea.selectionEnd = newCursorPos;
        }
      }, 0);
      return;
    }

    // 3. Auto-closing pairs: (), {}, [], "", '', ``
    const pairs: Record<string, string> = {
      "(": ")",
      "{": "}",
      "[": "]",
      '"': '"',
      "'": "'",
      "`": "`",
    };

    if (pairs[e.key]) {
      const openChar = e.key;
      const closeChar = pairs[e.key];

      if (selectionStart !== selectionEnd) {
        // Wrap selection
        e.preventDefault();
        const selectedText = code.substring(selectionStart, selectionEnd);
        const newText =
          code.substring(0, selectionStart) +
          openChar +
          selectedText +
          closeChar +
          code.substring(selectionEnd);
        setCode(newText);

        setTimeout(() => {
          if (textarea) {
            textarea.selectionStart = selectionStart + 1;
            textarea.selectionEnd = selectionEnd + 1;
          }
        }, 0);
        return;
      } else if (openChar === closeChar && code.charAt(selectionStart) === closeChar) {
        // Skip over closing quote if already typed
        e.preventDefault();
        setTimeout(() => {
          if (textarea) {
            textarea.selectionStart = textarea.selectionEnd = selectionStart + 1;
          }
        }, 0);
        return;
      } else if (openChar !== closeChar) {
        e.preventDefault();
        const newText =
          code.substring(0, selectionStart) +
          openChar +
          closeChar +
          code.substring(selectionEnd);
        setCode(newText);

        setTimeout(() => {
          if (textarea) {
            textarea.selectionStart = textarea.selectionEnd = selectionStart + 1;
          }
        }, 0);
        return;
      }
    }
  };

  // Structured Code Formatter
  const handleFormatCode = () => {
    if (!code || !code.trim()) return;

    const indentStr = " ".repeat(tabSize);
    const lines = code.split("\n");
    let currentIndentLevel = 0;
    const formattedLines: string[] = [];

    const isPython = language.toLowerCase() === "python";

    lines.forEach((line) => {
      let trimmed = line.trim();
      if (!trimmed) {
        formattedLines.push("");
        return;
      }

      if (!isPython) {
        // Handle closing braces for C-like languages
        if (trimmed.startsWith("}") || trimmed.startsWith(")") || trimmed.startsWith("]")) {
          currentIndentLevel = Math.max(0, currentIndentLevel - 1);
        }

        formattedLines.push(indentStr.repeat(currentIndentLevel) + trimmed);

        // Increase indent after opening braces
        const openBraces = (trimmed.match(/[\{\(\[]/g) || []).length;
        const closeBraces = (trimmed.match(/[\}\)\]]/g) || []).length;
        currentIndentLevel = Math.max(0, currentIndentLevel + (openBraces - closeBraces));
      } else {
        // Python Indentation Normalization
        const leadingSpaceMatch = line.match(/^[\t ]*/);
        const origSpaces = leadingSpaceMatch ? leadingSpaceMatch[0] : "";
        const rawIndentCount = origSpaces.replace(/\t/g, "    ").length;
        const normalizedLevel = Math.round(rawIndentCount / 4);

        formattedLines.push(indentStr.repeat(normalizedLevel) + trimmed);
      }
    });

    // Clean multiple consecutive blank lines down to max 1
    const cleaned = formattedLines
      .join("\n")
      .replace(/\n{3,}/g, "\n\n")
      .trim() + "\n";

    setCode(cleaned);
  };

  const handleCopyCode = () => {
    if (!code) return;
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const fontSizeClass =
    fontSize === "sm" ? "editor-text-sm" : fontSize === "lg" ? "editor-text-lg" : "editor-text-md";

  return (
    <div className="structured-editor-container" style={{ height: height || "auto" }}>
      {/* Editor Header Toolbar */}
      {showToolbar && (
        <div className="structured-editor-toolbar">
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
            <span className="badge badge-purple" style={{ fontSize: "0.72rem", padding: "0.2rem 0.5rem", fontWeight: 700 }}>
              <Code2 className="w-3.5 h-3.5 mr-1 inline text-purple-300" />
              {language.toUpperCase()} ENGINE
            </span>

            {setLanguage && (
              <select
                className="select-input"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                style={{ fontSize: "0.76rem", padding: "0.25rem 0.6rem", height: "28px" }}
              >
                <option value="python">Python 3</option>
                <option value="javascript">JavaScript</option>
                <option value="typescript">TypeScript</option>
                <option value="c">C</option>
                <option value="cpp">C++</option>
                <option value="java">Java</option>
                <option value="go">Go</option>
                <option value="rust">Rust</option>
              </select>
            )}

            {extraHeaderControls}
          </div>

          <div style={{ display: "flex", gap: "0.4rem", alignItems: "center", flexWrap: "wrap" }}>
            {/* Format Code Button */}
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={handleFormatCode}
              disabled={readOnly || !code.trim()}
              title="Auto-Format & Structure Code"
              style={{ fontSize: "0.74rem", padding: "0.25rem 0.6rem", height: "28px", borderColor: "rgba(168, 85, 247, 0.4)", color: "#c084fc" }}
            >
              <Sparkles className="w-3.5 h-3.5 mr-1 text-purple-400 inline" /> Format Code
            </button>

            {/* Tab Size Selector */}
            <div style={{ display: "flex", alignItems: "center", background: "var(--bg-input)", borderRadius: "6px", border: "1px solid var(--border-subtle)", padding: "2px" }}>
              <button
                type="button"
                className={`btn btn-xs ${tabSize === 2 ? "btn-primary" : "btn-secondary"}`}
                onClick={() => setTabSize(2)}
                style={{ fontSize: "0.68rem", padding: "0.15rem 0.4rem", height: "22px", borderRadius: "4px" }}
                title="Indent size: 2 spaces"
              >
                2s
              </button>
              <button
                type="button"
                className={`btn btn-xs ${tabSize === 4 ? "btn-primary" : "btn-secondary"}`}
                onClick={() => setTabSize(4)}
                style={{ fontSize: "0.68rem", padding: "0.15rem 0.4rem", height: "22px", borderRadius: "4px" }}
                title="Indent size: 4 spaces"
              >
                4s
              </button>
            </div>

            {/* Font Size Selector */}
            <div style={{ display: "flex", alignItems: "center", background: "var(--bg-input)", borderRadius: "6px", border: "1px solid var(--border-subtle)", padding: "2px" }}>
              <button
                type="button"
                className={`btn btn-xs ${fontSize === "sm" ? "btn-primary" : "btn-secondary"}`}
                onClick={() => setFontSize("sm")}
                style={{ fontSize: "0.68rem", padding: "0.15rem 0.4rem", height: "22px", borderRadius: "4px" }}
                title="Font size: Small (13px)"
              >
                A-
              </button>
              <button
                type="button"
                className={`btn btn-xs ${fontSize === "md" ? "btn-primary" : "btn-secondary"}`}
                onClick={() => setFontSize("md")}
                style={{ fontSize: "0.68rem", padding: "0.15rem 0.4rem", height: "22px", borderRadius: "4px" }}
                title="Font size: Medium (15px)"
              >
                A
              </button>
              <button
                type="button"
                className={`btn btn-xs ${fontSize === "lg" ? "btn-primary" : "btn-secondary"}`}
                onClick={() => setFontSize("lg")}
                style={{ fontSize: "0.68rem", padding: "0.15rem 0.4rem", height: "22px", borderRadius: "4px" }}
                title="Font size: Large (17px)"
              >
                A+
              </button>
            </div>

            {/* Copy Button */}
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={handleCopyCode}
              disabled={!code}
              title="Copy Code"
              style={{ fontSize: "0.74rem", padding: "0.25rem 0.5rem", height: "28px" }}
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            </button>

            {/* Clear Button */}
            {!readOnly && (
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setCode("")}
                disabled={!code}
                title="Clear Editor"
                style={{ fontSize: "0.74rem", padding: "0.25rem 0.5rem", height: "28px" }}
              >
                <Trash2 className="w-3.5 h-3.5 text-rose-400" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Editor Code Body with Line Numbers & Synced Scroll */}
      <div className="structured-editor-body" style={{ minHeight }}>
        {/* Line Numbers Gutter */}
        <div className={`structured-line-numbers ${fontSizeClass}`} ref={lineNumbersRef}>
          {lineNumbers.map((num) => (
            <div
              key={num}
              className={`line-num-item ${num === activeLine ? "active-line-num" : ""}`}
            >
              {num}
            </div>
          ))}
        </div>

        {/* Textarea Code Canvas */}
        <textarea
          ref={textareaRef}
          className={`structured-code-textarea ${fontSizeClass}`}
          placeholder={placeholder}
          value={code}
          onChange={(e) => setCode(e.target.value)}
          onKeyDown={handleKeyDown}
          onScroll={handleScroll}
          onClick={updateCursorPosition}
          onKeyUp={updateCursorPosition}
          readOnly={readOnly}
          spellCheck={false}
          tabIndex={0}
        />
      </div>

      {/* Editor Status Footer Bar */}
      <div className="structured-editor-footer">
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <span>
            Line <strong style={{ color: "var(--accent-cyan)" }}>{cursorPos.line}</strong>, Column <strong style={{ color: "var(--accent-cyan)" }}>{cursorPos.col}</strong>
          </span>
          <span>•</span>
          <span>{lineCount} lines</span>
          <span>•</span>
          <span>{code.length.toLocaleString()} chars</span>
        </div>

        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          {extraFooterControls}
          <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontStyle: "italic" }}>
            Tab = Indent ({tabSize}s) • Auto-closing Brackets Active
          </span>
        </div>
      </div>
    </div>
  );
}
