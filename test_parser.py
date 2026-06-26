"""Unit tests for monitor parsing and signal detection."""
from monitor import detect_rejection_loop, detect_review_status, detect_stagnation, update_flag

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
check("minor issues", "**STATUS:** MINOR_ISSUES", "changes_required")
check("pending", "**STATUS:** PENDING", "changes_required")
check("requires improvement", "**STATUS:** Requires Improvement", "changes_required")

# ── negative tests ─────────────────────────────────────────────────
check("no status", "The code looks good.", None)
check("partial match only", "APPROVED status", None)
check("empty content", "", None)
check("no reviewer msg", None, None)

review_a = """## Code Review

**Category:** Maintainability
**Severity:** Minor
**Description:** The cache uses OrderedDict. This is acceptable for LRU storage.
**Suggested Fix:** Keep the implementation simple unless profiling shows a need.

**STATUS:** MINOR
"""

review_b = """## Review Findings

**Category:** Error Handling
**Severity:** Minor
**Description:** Missing-key errors should include the requested key.
**Suggested Fix:** Return a clearer 404 detail for missing keys.

**STATUS:** MINOR
"""

review_c = """## Code Review

**Category:** Error Handling
**Severity:** Minor
**Description:** Missing-key errors should include the requested key.
**Suggested Fix:** Return a clearer 404 detail for missing keys.

**STATUS:** MINOR
"""

signal_messages = [
    {"sender": "reviewer", "content": review_a},
    {"sender": "reviewer", "content": review_b},
]

if detect_rejection_loop(signal_messages):
    failed += 1
    print("  [FAIL] suggested-fix boilerplate should not create rejection_loop")
else:
    passed += 1
    print("  [PASS] suggested-fix boilerplate should not create rejection_loop")

if detect_stagnation(signal_messages):
    failed += 1
    print("  [FAIL] different review content should not stagnate because of headings")
else:
    passed += 1
    print("  [PASS] different review content should not stagnate because of headings")

if not detect_stagnation([{"sender": "reviewer", "content": review_b}, {"sender": "reviewer", "content": review_c}]):
    failed += 1
    print("  [FAIL] same review issue with different heading should stagnate")
else:
    passed += 1
    print("  [PASS] same review issue with different heading should stagnate")

stale_flags = update_flag(["stagnation", "rejection_loop"], [{"sender": "reviewer", "content": review_a}])
if stale_flags:
    failed += 1
    print(f"  [FAIL] update_flag should drop stale flags, got={stale_flags!r}")
else:
    passed += 1
    print("  [PASS] update_flag drops stale flags")

print(f"\n{passed + failed} tests, {passed} passed, {failed} failed")
