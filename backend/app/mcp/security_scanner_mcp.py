"""
🥇 Security Scanner MCP Connector Server.
Audits OWASP Top 10 security vulnerabilities, secrets leaks, and unsafe patterns.
"""

import re
from typing import Dict, Any, List


class SecurityScannerMcpServer:
    SERVER_ID = "security_scanner"
    NAME = "Security Scanner MCP"
    DESCRIPTION = "OWASP Top 10 security audit, SQL injection detection, XSS, and hardcoded secrets scanner"
    CATEGORY = "Security"

    SECRET_PATTERNS = [
        (re.compile(r"(?i)(api_key|apikey|secret_key|secret|password|passwd|pwd)\s*=\s*['\"][A-Za-z0-9_\-]{8,}['\"]"), "Hardcoded Credential/Secret"),
        (re.compile(r"AIzaSy[A-Za-z0-9_\-]{33}"), "Google Gemini/Firebase API Key"),
        (re.compile(r"sk-[A-Za-z0-9]{32,}"), "OpenAI API Key"),
        (re.compile(r"-----BEGIN (RSA|EC|PRIVATE) KEY-----"), "Private Key PEM Signature")
    ]

    VULNERABILITY_PATTERNS = [
        (re.compile(r"(?i)SELECT\s+.*\s+FROM\s+.*\s*\+"), "SQL Injection via string concatenation", "CRITICAL", 3),
        (re.compile(r"(?i)eval\s*\("), "Arbitrary Code Execution via eval()", "CRITICAL", 95),
        (re.compile(r"(?i)exec\s*\("), "Dynamic Command Execution via exec()", "CRITICAL", 95),
        (re.compile(r"(?i)pickle\.loads\s*\("), "Unsafe Object Deserialization via pickle", "HIGH", 501),
        (re.compile(r"(?i)subprocess\.(Popen|call|run)\s*\(.*shell\s*=\s*True"), "Shell Injection Risk (shell=True)", "HIGH", 78)
    ]

    @classmethod
    def get_tools(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "scan_vulnerabilities",
                "description": "Audits source code for OWASP Top 10 vulnerabilities including SQL injection, RCE, unsafe eval, and command injection.",
                "server_id": cls.SERVER_ID,
                "parameters": [
                    {"name": "code", "type": "string", "description": "Source code text to scan", "required": True}
                ]
            },
            {
                "name": "detect_hardcoded_secrets",
                "description": "Scans code payload for exposed API keys, credentials, secret tokens, and private SSH/RSA keys.",
                "server_id": cls.SERVER_ID,
                "parameters": [
                    {"name": "code", "type": "string", "description": "Source code text to scan for secrets", "required": True}
                ]
            }
        ]

    @classmethod
    async def execute_tool(cls, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        code = args.get("code", "")
        if not code or not code.strip():
            raise ValueError("Parameter 'code' cannot be empty.")

        if tool_name == "scan_vulnerabilities":
            return cls._scan_vulnerabilities(code)
        elif tool_name == "detect_hardcoded_secrets":
            return cls._detect_hardcoded_secrets(code)
        else:
            raise ValueError(f"Unknown tool '{tool_name}' for server '{cls.SERVER_ID}'")

    @classmethod
    def _scan_vulnerabilities(cls, code: str) -> Dict[str, Any]:
        findings = []
        lines = code.splitlines()

        for idx, line in enumerate(lines, start=1):
            for pattern, title, severity, cwe in cls.VULNERABILITY_PATTERNS:
                if pattern.search(line):
                    findings.append({
                        "line": idx,
                        "title": title,
                        "severity": severity,
                        "cwe": f"CWE-{cwe}",
                        "snippet": line.strip()
                    })

        critical_count = sum(1 for f in findings if f["severity"] == "CRITICAL")
        high_count = sum(1 for f in findings if f["severity"] == "HIGH")

        security_score = max(0, 100 - (critical_count * 30 + high_count * 15))

        return {
            "vulnerabilities_detected": len(findings),
            "security_score": security_score,
            "verdict": "FAILED_SECURITY_AUDIT" if critical_count > 0 else "PASSED_WITH_WARNINGS" if high_count > 0 else "PASSED_SECURITY_AUDIT",
            "findings": findings
        }

    @classmethod
    def _detect_hardcoded_secrets(cls, code: str) -> Dict[str, Any]:
        secrets = []
        lines = code.splitlines()

        for idx, line in enumerate(lines, start=1):
            for pattern, secret_type in cls.SECRET_PATTERNS:
                if pattern.search(line):
                    secrets.append({
                        "line": idx,
                        "type": secret_type,
                        "masked_snippet": line.strip()[:15] + "..." + line.strip()[-5:]
                    })

        return {
            "secrets_found_count": len(secrets),
            "secrets": secrets,
            "has_leaks": len(secrets) > 0,
            "recommendation": "Never commit plaintext credentials into source code. Use environment variables (.env) or Secret Managers."
        }
