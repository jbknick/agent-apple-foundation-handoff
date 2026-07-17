from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import unittest
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, build_opener


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "apple-foundation-models-handoff"
REFERENCE_ROOT = PLUGIN_ROOT / "references"
REFERENCE_NAMES = (
    "architecture-and-state.md",
    "orchestration-patterns.md",
    "apple-api-availability.md",
    "security-context-and-recovery.md",
    "evaluation-and-observability.md",
)
SWIFT_LABELS = {
    "compiled_sdk_26_5",
    "interface_verified_sdk_26_5",
    "official_beta_unverified",
    "pseudocode",
}
APPLE_OWNER = "apple-api-availability.md"
VOLATILE_OWNER_TOKENS = (
    "LanguageModelError",
    "LanguageModelSession.GenerationError",
    "PrivateCloudComputeLanguageModel.Error",
    "GenerationOptions.ToolCallingMode",
    "DynamicProfile",
    "DynamicInstructions",
    "SkillActivations",
)
EXPECTED_INTERFACE_SHA256 = (
    "ff2285670b0966addb9827dc895a3ee3c9db6e186baae62c034fed012632aacc"
)
UTILITIES_COMMIT = "376ca60e61985369d5067bd3c575bdb6a13f0e1b"
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
SWIFT_FENCE_PATTERN = re.compile(r"^```swift\s*$", re.MULTILINE)

REQUIRED_HEADINGS = {
    "architecture-and-state.md": (
        "## Scope and authority",
        "## Common result schema",
        "## Ownership and state fields",
        "## Lifecycle transition table",
        "## Termination and fallback boundary",
        "## Recovery and replay checklist",
        "## Related references",
        "## Source ledger",
        "## Limitations",
    ),
    "orchestration-patterns.md": (
        "## Scope and authority",
        "## Selection questions",
        "## Four-pattern comparison",
        "## Baton-pass",
        "## Isolated consultation",
        "## Deterministic routing",
        "## Transcript transfer",
        "## Anti-conflation boundaries",
        "## Context and cache implications",
        "## Failure ownership",
        "## Related references",
        "## Source ledger",
        "## Limitations",
    ),
    "apple-api-availability.md": (
        "## Scope and authority",
        "## Evidence labels",
        "## Normalized host and interface identity",
        "## Availability matrix",
        "## Stable SDK 26.5 surface",
        "## OS and Xcode 27 beta surface",
        "## Structured output and tools",
        "## Transcripts and history",
        "## Stable SDK 26.5 errors",
        "## OS and Xcode 27 beta errors",
        "## Provider and PCC boundary",
        "## Runtime Skills boundary",
        "## Cache and performance qualifications",
        "## Compile and blocker matrix",
        "## Related references",
        "## Source ledger",
        "## Limitations",
    ),
    "security-context-and-recovery.md": (
        "## Scope and authority",
        "## Untrusted inputs and trust boundaries",
        "## Context classes and provenance",
        "## Atomic boundary envelopes",
        "## Provider grants",
        "## Immediate effect confirmation",
        "## Reducer authority",
        "## Tool-result provenance",
        "## Command emission and effect reconciliation",
        "## Failure, cancellation, and transcript repair",
        "## Provider truth and safe fallback",
        "## Trace policy",
        "## Adversarial checklist",
        "## Residual risks",
        "## Related references",
        "## Source ledger",
        "## Limitations",
    ),
    "evaluation-and-observability.md": (
        "## Scope and authority",
        "## Evidence layers and states",
        "## Stable ID catalog",
        "## Corpus and oracle separation",
        "## Deterministic acceptance",
        "## Canonical rubric",
        "## Safe evidence",
        "## Reference-disclosure proof",
        "## Host matrix",
        "## Apple Evaluations",
        "## Instruments",
        "## Zero-denominator rules",
        "## Blockers",
        "## Related references",
        "## Source ledger",
        "## Limitations",
    ),
}

STABLE_GENERATION_ERROR_SIGNATURES = (
    "case exceededContextWindowSize(FoundationModels.LanguageModelSession.GenerationError.Context)",
    "case assetsUnavailable(FoundationModels.LanguageModelSession.GenerationError.Context)",
    "case guardrailViolation(FoundationModels.LanguageModelSession.GenerationError.Context)",
    "case unsupportedGuide(FoundationModels.LanguageModelSession.GenerationError.Context)",
    "case unsupportedLanguageOrLocale(FoundationModels.LanguageModelSession.GenerationError.Context)",
    "case decodingFailure(FoundationModels.LanguageModelSession.GenerationError.Context)",
    "case rateLimited(FoundationModels.LanguageModelSession.GenerationError.Context)",
    "case concurrentRequests(FoundationModels.LanguageModelSession.GenerationError.Context)",
    "case refusal(FoundationModels.LanguageModelSession.GenerationError.Refusal, FoundationModels.LanguageModelSession.GenerationError.Context)",
)
STABLE_SUPPORT_SIGNATURES = (
    "public let debugDescription: Swift.String",
    "public init(debugDescription: Swift.String)",
    "public init(transcriptEntries: [FoundationModels.Transcript.Entry])",
    "public var explanation: FoundationModels.LanguageModelSession.Response<Swift.String> { get async throws }",
    "public var explanationStream: FoundationModels.LanguageModelSession.ResponseStream<Swift.String> { get }",
    "public var errorDescription: Swift.String? { get }",
    "public var recoverySuggestion: Swift.String? { get }",
    "public var failureReason: Swift.String? { get }",
    "public var tool: any FoundationModels.Tool",
    "public var underlyingError: any Swift.Error",
    "public init(tool: any FoundationModels.Tool, underlyingError: any Swift.Error)",
)
BETA_CASE_SIGNATURES = (
    "case contextSizeExceeded(LanguageModelError.ContextSizeExceeded)",
    "case rateLimited(LanguageModelError.RateLimited)",
    "case refusal(LanguageModelError.Refusal)",
    "case timeout(LanguageModelError.Timeout)",
    "case guardrailViolation(LanguageModelError.GuardrailViolation)",
    "case unsupportedCapability(LanguageModelError.UnsupportedCapability)",
    "case unsupportedTranscriptContent(LanguageModelError.UnsupportedTranscriptContent)",
    "case unsupportedGenerationGuide(LanguageModelError.UnsupportedGenerationGuide)",
    "case unsupportedLanguageOrLocale(LanguageModelError.UnsupportedLanguageOrLocale)",
    "case concurrentRequests",
    "case transcriptMutationWhileResponding",
    "case assetsUnavailable(SystemLanguageModel.Error.AssetsUnavailable)",
    "case quotaLimitReached(PrivateCloudComputeLanguageModel.Error.QuotaLimitReached)",
    "case networkFailure(PrivateCloudComputeLanguageModel.Error.NetworkFailure)",
    "case serviceUnavailable(PrivateCloudComputeLanguageModel.Error.ServiceUnavailable)",
)
BETA_PAYLOAD_SIGNATURES = (
    "init(contextSize: Int, tokenCount: Int, debugDescription: String, metadata: [String : any Sendable] = [:])",
    "init(resetDate: Date?, debugDescription: String, metadata: [String : any Sendable] = [:])",
    "init(explanation: String, debugDescription: String, metadata: [String : any Sendable] = [:])",
    "init(debugDescription: String, metadata: [String : any Sendable] = [:])",
    "init(capability: LanguageModelCapabilities.Capability, debugDescription: String, metadata: [String : any Sendable] = [:])",
    "init(unsupportedContent: [Transcript.Entry], debugDescription: String, metadata: [String : any Sendable] = [:])",
    "init(schemaName: String?, debugDescription: String, metadata: [String : any Sendable] = [:])",
    "init(languageCode: Locale.LanguageCode, debugDescription: String, metadata: [String : any Sendable] = [:])",
    "init(limitIncreaseSuggestion: PrivateCloudComputeLanguageModel.QuotaUsage.LimitIncreaseSuggestion? = nil, resetDate: Date? = nil, debugDescription: String)",
    "init(tool: any Tool, underlyingError: any Error)",
    "var contextSize: Int",
    "var tokenCount: Int",
    "var resetDate: Date?",
    "nonisolated(nonsending) var explanation: LanguageModelSession.Response<String> { get async throws }",
    "var explanationStream: LanguageModelSession.ResponseStream<String> { get }",
    "var capability: LanguageModelCapabilities.Capability",
    "var unsupportedContent: [Transcript.Entry]",
    "var schemaName: String?",
    "var languageCode: Locale.LanguageCode",
    "var limitIncreaseSuggestion: PrivateCloudComputeLanguageModel.QuotaUsage.LimitIncreaseSuggestion?",
    "var tool: any Tool",
    "var underlyingError: any Error",
    "var errorDescription: String? { get }",
)

D_IDS = (
    "D-SCHEMA-001",
    "D-ROUTE-001",
    "D-OWNER-001",
    "D-TRANSITION-001",
    "D-TOOL-001",
    "D-CONTEXT-001",
    "D-CONTEXT-002",
    "D-GRANT-001",
    "D-PHASE-001",
    "D-EFFECT-001",
    "D-EFFECT-002",
    "D-FALLBACK-001",
    "D-EVIDENCE-001",
    "D-RUBRIC-001",
)
D_ID_MEANINGS = {
    "D-SCHEMA-001": "Versioned case/policy/result shape and oracle separation",
    "D-ROUTE-001": "Required and allowed destination",
    "D-OWNER-001": "Exactly one final response by the declared owner",
    "D-TRANSITION-001": "Valid, contiguous, acyclic, budgeted transitions",
    "D-TOOL-001": "Actor/tool allowlist and call budget",
    "D-CONTEXT-001": "Declared required-context inclusion",
    "D-CONTEXT-002": "Forbidden-context exclusion",
    "D-GRANT-001": (
        "Bound provider grant and independent state/policy revision match"
    ),
    "D-PHASE-001": "Canonical phase/event order and recovery position",
    "D-EFFECT-001": "Unique effect identities and one matching ledger entry",
    "D-EFFECT-002": (
        "One original command, no replay command, reconciliation before retry"
    ),
    "D-FALLBACK-001": "Only a declared safe fallback",
    "D-EVIDENCE-001": "Safe allowlisted evidence and exact hashes",
    "D-RUBRIC-001": (
        "Complete, anchored, hash-bound rubric integrity and verdict"
    ),
}
E_IDS = (
    "E-CLAUDE-LOAD-001",
    "E-CODEX-LOAD-001",
    "E-CLAUDE-ACTIVATE-001",
    "E-CODEX-ACTIVATE-001",
    "E-CROSSHOST-STRUCT-001",
    "E-CROSSHOST-CAP-001",
    "E-APPLE-HOST-001",
    "E-APPLE-EVAL-001",
    "E-APPLE-INSTR-001",
)
RUBRIC_DIMENSIONS = (
    "Pattern selection",
    "Apple API grounding and version labeling",
    "Security-policy completeness",
    "Context minimization",
    "Failure and recovery behavior",
    "Testability and observability",
    "Limitation honesty",
)


def is_approved_apple_source(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    if parsed.netloc in {"developer.apple.com", "security.apple.com"}:
        return True
    return (
        parsed.netloc == "github.com"
        and parsed.path.startswith("/apple/foundation-models-utilities/")
        and UTILITIES_COMMIT in parsed.path
    )


class ReferenceLibraryTests(unittest.TestCase):
    maxDiff = None

    def texts(self) -> dict[str, str]:
        texts: dict[str, str] = {}
        for name in REFERENCE_NAMES:
            path = REFERENCE_ROOT / name
            self.assertTrue(path.is_file(), f"missing reference: {name}")
            texts[name] = path.read_text(encoding="utf-8")
        return texts

    def test_exact_reference_topology_is_regular_and_non_symlinked(self):
        self.assertTrue(REFERENCE_ROOT.exists(), "reference tree is absent")
        root_mode = REFERENCE_ROOT.lstat().st_mode
        self.assertTrue(stat.S_ISDIR(root_mode))
        self.assertFalse(stat.S_ISLNK(root_mode))
        self.assertEqual(
            sorted(REFERENCE_NAMES),
            sorted(path.name for path in REFERENCE_ROOT.iterdir()),
        )
        for name in REFERENCE_NAMES:
            mode = (REFERENCE_ROOT / name).lstat().st_mode
            self.assertTrue(stat.S_ISREG(mode), name)
            self.assertFalse(stat.S_ISLNK(mode), name)

    def test_required_sections_are_complete_and_titles_do_not_activate(self):
        for name, text in self.texts().items():
            first_line = text.splitlines()[0]
            self.assertRegex(first_line, r"^# \S")
            self.assertNotRegex(
                first_line.lower(), r"activate|activation|trigger|when to use"
            )
            for heading in REQUIRED_HEADINGS[name]:
                with self.subTest(file=name, heading=heading):
                    self.assertIn(heading, text)

    def test_relative_links_are_contained_and_every_reference_has_an_incoming_edge(self):
        incoming = {name: 0 for name in REFERENCE_NAMES}
        for name, text in self.texts().items():
            for raw_target in LINK_PATTERN.findall(text):
                target = unquote(raw_target.split("#", 1)[0]).strip()
                if not target or urlparse(target).scheme in {"http", "https"}:
                    continue
                relative = Path(target)
                self.assertFalse(relative.is_absolute(), (name, target))
                self.assertNotIn("..", relative.parts, (name, target))
                resolved = (REFERENCE_ROOT / relative).resolve()
                self.assertTrue(
                    resolved.is_relative_to(REFERENCE_ROOT.resolve()),
                    (name, target),
                )
                self.assertTrue(resolved.is_file(), (name, target))
                self.assertFalse(resolved.is_symlink(), (name, target))
                if resolved.name in incoming and resolved.name != name:
                    incoming[resolved.name] += 1
        self.assertFalse(
            [name for name, count in incoming.items() if count == 0],
            incoming,
        )

    def test_volatile_apple_declarations_have_one_owner(self):
        texts = self.texts()
        for token in VOLATILE_OWNER_TOKENS:
            owners = [name for name, text in texts.items() if token in text]
            self.assertEqual([APPLE_OWNER], owners, token)

    def test_architecture_contract_is_complete(self):
        text = self.texts()["architecture-and-state.md"]
        required = (
            "activationStatus = activated",
            "selectedSkill",
            "routerInput = { domain, requestedOperation, artifactState, evidenceState }",
            'architectureSchemaVersion: "1.0"',
            "architectureResult",
            "workflow-specific sections are additive inside",
            "stateVersion",
            "policyVersion",
            "stable",
            "transitioning",
            "recoveryRequired",
            "terminated",
            "stable-only ordinary termination",
            "explicit successful reconciliation",
            "late/replayed event or unavailable repair",
            "Preserve authority, phase, pending/checkpoint state, counts, ledger, and repair facts; emit no command.",
            "at most one command",
        )
        for token in required:
            self.assertIn(token, text)
        self.assertRegex(text, r"stateVersion.*policyVersion|policyVersion.*stateVersion")
        self.assertIn("independently", text)
        self.assertNotIn("exactly-once", text)
        for invented_domain in (
            "implementationResult",
            "reviewResult",
            "debugResult",
            "validationResult",
        ):
            self.assertNotIn(invented_domain, text)

    def test_pattern_contract_is_complete(self):
        text = self.texts()["orchestration-patterns.md"]
        required = (
            "Baton-pass",
            "Isolated consultation",
            "Deterministic routing",
            "Transcript transfer",
            "Destination becomes active and owns the final response",
            "Parent receives a typed result and retains final ownership",
            "routing is not inherently a handoff",
            "Only explicitly copied entries",
            "destination finishes the user-facing task + selected shared history -> baton-pass",
            "parent needs bounded expertise + isolated child transcript -> consultation",
            "application chooses one route before work -> deterministic routing",
            "new session is initialized from selected entries -> transcript transfer",
        )
        for token in required:
            self.assertIn(token, text)
        self.assertNotIn("BatonPass(", text)
        self.assertNotRegex(text, r"(?:struct|class|enum|protocol)\s+BatonPass\b")
        self.assertNotRegex(text, r"drop-in\s+`?PhoneFriendTool`?", re.IGNORECASE)

    def test_apple_api_contract_has_exact_host_errors_and_boundaries(self):
        text = self.texts()[APPLE_OWNER]
        required = (
            "SDK: macOS 26.5",
            "Swift: Apple Swift 6.3.2",
            EXPECTED_INTERFACE_SHA256,
            "arm64e-apple-macos.swiftinterface",
            "GenerationOptions.ToolCallingMode",
            "static values",
            ".allowed",
            ".required",
            ".disallowed",
            "SDK 26.5 `LanguageModelSession.GenerationError`",
            "OS and Xcode 27 beta",
            "Provider behavior varies",
            "not a runtime dependency",
            UTILITIES_COMMIT,
        )
        for token in required:
            self.assertIn(token, text)
        for signature in (
            *STABLE_GENERATION_ERROR_SIGNATURES,
            *STABLE_SUPPORT_SIGNATURES,
            *BETA_CASE_SIGNATURES,
            *BETA_PAYLOAD_SIGNATURES,
        ):
            with self.subTest(signature=signature):
                self.assertIn(signature, text)
        self.assertEqual(
            9,
            text.count("metadata: [String : any Sendable] = [:]"),
            "every LanguageModelError payload initializer preserves its DocC default",
        )
        self.assertEqual(
            2,
            text.count(
                "init(debugDescription: String, metadata: "
                "[String : any Sendable] = [:])"
            ),
            "Timeout and GuardrailViolation have the same exact initializer",
        )
        self.assertNotRegex(text, r"ToolCallingMode\s+(?:enum|cases)")

    def test_swift_fences_have_one_allowed_label_and_compiled_blocks_typecheck(self):
        compiled: list[tuple[str, str]] = []
        for name, text in self.texts().items():
            lines = text.splitlines()
            for index, line in enumerate(lines):
                if line != "```swift":
                    continue
                previous = index - 1
                while previous >= 0 and not lines[previous].strip():
                    previous -= 1
                self.assertGreaterEqual(previous, 0, name)
                match = re.fullmatch(
                    r"Code status: `([a-z0-9_]+)`", lines[previous].strip()
                )
                self.assertIsNotNone(match, (name, index + 1))
                label = match.group(1)
                self.assertIn(label, SWIFT_LABELS, (name, index + 1))
                end = index + 1
                while end < len(lines) and lines[end] != "```":
                    end += 1
                self.assertLess(end, len(lines), (name, index + 1))
                if label == "compiled_sdk_26_5":
                    compiled.append((name, "\n".join(lines[index + 1 : end]) + "\n"))
        self.assertTrue(compiled, "at least one compiled_sdk_26_5 block is required")

        sdk_version = subprocess.run(
            ["xcrun", "--sdk", "macosx", "--show-sdk-version"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(0, sdk_version.returncode, sdk_version.stderr)
        self.assertEqual(
            "26.5",
            sdk_version.stdout.strip(),
            f"blocked/sdk_version_mismatch:{sdk_version.stdout.strip()}",
        )
        sdk = subprocess.run(
            ["xcrun", "--sdk", "macosx", "--show-sdk-path"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(0, sdk.returncode, sdk.stderr)
        with tempfile.TemporaryDirectory() as directory:
            for index, (name, source) in enumerate(compiled):
                snippet = Path(directory) / f"snippet-{index}.swift"
                snippet.write_text(source, encoding="utf-8", newline="\n")
                result = subprocess.run(
                    [
                        "swiftc",
                        "-typecheck",
                        "-target",
                        "arm64-apple-macos26.0",
                        "-sdk",
                        sdk.stdout.strip(),
                        str(snippet),
                    ],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                self.assertEqual(0, result.returncode, f"{name}: {result.stderr}")

    def test_external_source_authorities_are_approved_and_versioned(self):
        urls: set[str] = set()
        for name, text in self.texts().items():
            file_urls = {
                target
                for target in LINK_PATTERN.findall(text)
                if urlparse(target).scheme in {"http", "https"}
            }
            self.assertTrue(file_urls, f"source ledger has no URL: {name}")
            urls.update(file_urls)
        for url in urls:
            with self.subTest(url=url):
                self.assertTrue(is_approved_apple_source(url), url)

    def test_security_contract_is_complete(self):
        text = self.texts()["security-context-and-recovery.md"]
        required = (
            "Official Apple fact",
            "Mandatory application policy",
            "Recommended control",
            "C0",
            "C1",
            "C2",
            "C3",
            "never transferable",
            "provenance",
            "destination",
            "purpose",
            "fields",
            "tools",
            "retention",
            "expiry",
            "person",
            "stateVersion",
            "policyVersion",
            "immediate effect confirmation",
            "typed tool-result provenance",
            "one effect identity",
            "replay/late event -> unchanged state and no executor command",
            "retry -> only after explicit reconciliation establishes external truth",
            "safe fallback",
            ".onToolCall",
            ".historyTransform",
            "official_beta_unverified",
        )
        for token in required:
            self.assertIn(token, text)
        for line in text.splitlines():
            if "exactly-once" in line:
                self.assertIn("never promise exactly-once", line)
        self.assertNotIn("traces are unencrypted", text.lower())
        self.assertNotRegex(text, r"\[[^\]]+\]\([^)]*\.(?:trace|xcresult)[^)]*\)")
        self.assertNotRegex(text, r"\braw(?:Prompt|Response)\b")

    def test_evaluation_contract_is_complete(self):
        text = self.texts()["evaluation-and-observability.md"]
        for evidence_id in (*D_IDS, *E_IDS):
            self.assertIn(evidence_id, text)
        for evidence_id, meaning in D_ID_MEANINGS.items():
            with self.subTest(evidence_id=evidence_id):
                self.assertIn(f"| `{evidence_id}` | {meaning} |", text)
        self.assertIn(
            "D-GRANT-001 binds person/session, source profile/provider, "
            "destination profile/provider, purpose, exact classes, exact fields, "
            "tools, retention, expiry, applicable provider disclosure, exceptional "
            "C2 permission, stateVersion, and policyVersion; any bound-field change "
            "invalidates the grant.",
            text.replace("\n", " "),
        )
        for state in ("pass", "fail", "blocked", "not_applicable"):
            self.assertRegex(text, rf"`{state}`")
        self.assertIn("value: null", text)
        self.assertIn("status: not_applicable", text)
        self.assertIn("mean is at least 3.0", text)
        self.assertIn("Scores are integers from 1 through 4", text)
        for dimension in RUBRIC_DIMENSIONS:
            self.assertIn(dimension, text)
        self.assertIn("synthetic/redacted", text)
        self.assertIn("normalized metadata", text)
        self.assertIn("Xcode 27", text)
        self.assertIn("optional evidence", text)
        self.assertIn("not authorization", text)
        self.assertIn("not default CI", text)
        self.assertNotRegex(text, r"\[[^\]]+\]\([^)]*\.(?:trace|xcresult)[^)]*\)")
        self.assertNotRegex(text, r"\braw(?:Prompt|Response)\b")

    def test_no_placeholders_private_paths_or_unsafe_evidence_markers(self):
        combined = "\n".join(self.texts().values())
        self.assertNotRegex(combined, r"(?i)\bTODO\b|\bTBD\b|coming soon|placeholder")
        self.assertNotRegex(combined, r"/Users/|/home/")
        self.assertNotRegex(
            combined,
            r"BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY|(?i:api[_-]?key|access[_-]?token)",
        )


@unittest.skipUnless(
    os.environ.get("DEV137_CHECK_EXTERNAL_LINKS") == "1",
    "set DEV137_CHECK_EXTERNAL_LINKS=1 to resolve official sources",
)
class ReferenceExternalSourceTests(unittest.TestCase):
    def test_every_unique_official_source_resolves(self):
        urls: set[str] = set()
        for name in REFERENCE_NAMES:
            text = (REFERENCE_ROOT / name).read_text(encoding="utf-8")
            urls.update(
                target
                for target in LINK_PATTERN.findall(text)
                if urlparse(target).scheme in {"http", "https"}
            )
        self.assertTrue(urls)
        opener = build_opener()
        for url in sorted(urls):
            with self.subTest(url=url):
                request = Request(
                    url,
                    method="HEAD",
                    headers={"User-Agent": "DEV-137-source-audit/1.0"},
                )
                try:
                    response = opener.open(request, timeout=10)
                except HTTPError as error:
                    error.close()
                    if error.code not in {400, 403, 405, 406, 429}:
                        self.fail(f"source_http_failure:{error.code}:{url}")
                    request = Request(
                        url,
                        method="GET",
                        headers={
                            "User-Agent": "DEV-137-source-audit/1.0",
                            "Range": "bytes=0-0",
                        },
                    )
                    try:
                        response = opener.open(request, timeout=10)
                    except HTTPError as get_error:
                        get_error.close()
                        self.fail(f"source_http_failure:{get_error.code}:{url}")
                    except (URLError, TimeoutError, OSError) as get_error:
                        self.skipTest(
                            f"blocked/source_network_unavailable:{type(get_error).__name__}"
                        )
                except (URLError, TimeoutError, OSError) as error:
                    self.skipTest(
                        f"blocked/source_network_unavailable:{type(error).__name__}"
                    )
                with response:
                    self.assertLess(response.status, 400, url)
                    self.assertTrue(is_approved_apple_source(response.geturl()))


if __name__ == "__main__":
    unittest.main()
