"""Unit tests for detect_review_status() markdown-tolerant parser."""
from monitor import detect_review_status

passed = 0
failed = 0


def make_msg(content):
    return [{"sender": "reviewer", "content": content}]


def check(label, content, expected):
    global passed, failed
    if content is None:
        result = detect_review_status([])
    else:
        result = detect_review_status(make_msg(content))
    ok = result == expected
    status = "PASS" if ok else "FAIL"
    if not ok:
        failed += 1
    else:
        passed += 1
    print(f"  [{status}] {label}: expected={expected!r} got={result!r}")


# ── APPROVED variants ──────────────────────────────────────────────
check("plain", "STATUS: APPROVED", "approved")
check("bold colons", "**STATUS:** APPROVED", "approved")
check("bold full", "**STATUS: APPROVED**", "approved")
check("bold colon prefix", "**STATUS**: APPROVED", "approved")
check("bold value", "STATUS: **APPROVED**", "approved")
check("underscore bold", "__STATUS__: APPROVED", "approved")
check("underscore italic", "_STATUS_: APPROVED", "approved")
check("backtick", "`STATUS`: APPROVED", "approved")
check("whitespace", "STATUS:   APPROVED", "approved")
check("newline before", "some text\nSTATUS: APPROVED", "approved")
check("multi line", "Review:\nCode looks good.\nSTATUS: APPROVED", "approved")

# ── CHANGES_REQUIRED variants ──────────────────────────────────────
check("plain changes", "STATUS: CHANGES_REQUIRED", "changes_required")
check("bold colons changes", "**STATUS:** CHANGES_REQUIRED", "changes_required")
check("bold full changes", "**STATUS: CHANGES_REQUIRED**", "changes_required")
check("bold colon prefix changes", "**STATUS**: CHANGES_REQUIRED", "changes_required")
check("bold value changes", "STATUS: **CHANGES_REQUIRED**", "changes_required")
check("underscore bold changes", "__STATUS__: CHANGES_REQUIRED", "changes_required")

# ── Previously-failing real-world patterns ─────────────────────────
check("both bolded", "**STATUS:** **CHANGES_REQUIRED**", "changes_required")
check("both bolded 2space", "**STATUS:**  **CHANGES_REQUIRED**", "changes_required")
check("colon newline bold", "**STATUS:**\n\n**CHANGES_REQUIRED**", "changes_required")
check("overall status", "**OVERALL STATUS:** **CHANGES_REQUIRED**", "changes_required")
check("overall status newline", "**OVERALL STATUS:**\n\n**CHANGES_REQUIRED**", "changes_required")
check("both bolded approved", "**STATUS:** **APPROVED**", "approved")
check("overall status approved", "**OVERALL STATUS:** **APPROVED**", "approved")

# ── negative tests ─────────────────────────────────────────────────
check("no status", "The code looks good.", None)
check("partial match only", "APPROVED status", None)
check("empty content", "", None)
check("no reviewer msg", None, None)

print(f"\n{passed + failed} tests, {passed} passed, {failed} failed")
