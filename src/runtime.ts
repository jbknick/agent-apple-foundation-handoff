import {
  chmod,
  lstat,
  mkdir,
  open,
  readFile,
  readdir,
  realpath,
  stat,
  unlink,
  writeFile
} from 'node:fs/promises';
import { constants as fsConstants } from 'node:fs';
import { createHash, randomUUID } from 'node:crypto';
import os from 'node:os';
import path from 'node:path';
import { z } from 'zod';
import {
  CoverageSchema,
  DiagnosticsPayloadSchema,
  DiffPayloadSchema,
  FeedbackInputSchema,
  FeedbackResultSchema,
  IssuePayloadSchema,
  ModeSchema,
  ProcessInputSchema,
  ProcessResultSchema,
  ReadInputSchema,
  ReadResultSchema,
  StatsInputSchema,
  StatsResultSchema,
  type Evidence,
  type Mode,
  type Payload,
  type ProcessResult,
  type Task
} from './schemas.js';
import { AppleLocalProvider } from './apple-local.js';
import type { ProbeResult, Provider } from './provider.js';
import { Store } from './store.js';

const MAX_SOURCE_BYTES = 4 * 1024 * 1024;
const MAX_CHUNKS = 8;
const CHUNK_CHARACTERS = 32_000;
const DEADLINE_MS = 30_000;
const RESPONSE_TOKEN_BUDGET = 1_200;
const SNAPSHOT_TTL_MS = 24 * 60 * 60 * 1_000;

const ModelEvidenceSchema = z.object({
  id: z.string().min(1),
  startLine: z.number().int().min(1),
  endLine: z.number().int().min(1),
  excerpt: z.string().max(2_048)
}).strict();

const ModelDiagnosticsSchema = DiagnosticsPayloadSchema.extend({
  evidence: z.array(ModelEvidenceSchema)
}).strict();
const ModelDiffSchema = DiffPayloadSchema.extend({
  evidence: z.array(ModelEvidenceSchema)
}).strict();
const ModelIssueSchema = IssuePayloadSchema.extend({
  evidence: z.array(ModelEvidenceSchema)
}).strict();

interface Candidate {
  payload: Payload;
  evidence: Evidence[];
  coverage: z.infer<typeof CoverageSchema>;
}

export interface RuntimeOptions {
  mode?: Mode;
  roots?: string[];
  stateDir?: string;
  provider?: Provider;
  deadlineMs?: number;
}

export interface DoctorResult extends ProbeResult {
  stateDir: string;
  roots: string[];
  mode: Mode;
  setupRequired: boolean;
  setupCommand: string | null;
}

class PolicyError extends Error {}

function defaultStateDir(): string {
  const base = process.env.XDG_STATE_HOME || path.join(os.homedir(), '.local', 'state');
  return path.join(base, 'apple-offload');
}

function estimateTokens(value: string): number {
  return Math.ceil(value.length / 4);
}

async function beforeDeadline<T>(operation: Promise<T>, deadline: number): Promise<T> {
  const remaining = deadline - Date.now();
  if (remaining <= 0) throw new Error('deadline_exceeded');
  let timer: NodeJS.Timeout | undefined;
  try {
    return await Promise.race([
      operation,
      new Promise<never>((_resolve, reject) => {
        timer = setTimeout(() => reject(new Error('deadline_exceeded')), remaining);
      })
    ]);
  } finally {
    if (timer) clearTimeout(timer);
  }
}

export function redact(value: string): string {
  return value
    .replace(/-----BEGIN [^-]+ PRIVATE KEY-----[\s\S]*?-----END [^-]+ PRIVATE KEY-----/g, '[REDACTED_PRIVATE_KEY]')
    .replace(/\b(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16})\b/g, '[REDACTED_SECRET]')
    .replace(/\b(Authorization\s*:\s*Bearer\s+)[^\s]+/gi, '$1[REDACTED]')
    .replace(/\b([A-Z][A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY)\s*=\s*)[^\s]+/g, '$1[REDACTED]');
}

function isCredentialPath(filePath: string): boolean {
  const name = path.basename(filePath).toLowerCase();
  return name === '.env' || name.startsWith('.env.') ||
    /(?:credentials?|secrets?|id_rsa|id_ed25519)/.test(name) ||
    /\.(?:pem|p12|pfx|key)$/.test(name);
}

function within(root: string, target: string): boolean {
  return target === root || target.startsWith(`${root}${path.sep}`);
}

function diagnosticCandidate(lines: string[], artifactId: string): Candidate | null {
  const diagnostics: z.infer<typeof DiagnosticsPayloadSchema>['diagnostics'] = [];
  const evidence: Evidence[] = [];
  const location = /^(.*?):(\d+)(?::(\d+))?:\s*(error|warning|note)\s*(?:([A-Za-z]+\d+))?\s*:?\s*(.+)$/i;
  const codeOnly = /^\s*(error|warning|note)\s+([A-Za-z]+\d+)\s*:\s*(.+)$/i;
  for (const [index, raw] of lines.entries()) {
    const line = redact(raw);
    const match = location.exec(line);
    const fallback = codeOnly.exec(line);
    if (!match && !fallback) continue;
    const evidenceId = `E${evidence.length + 1}`;
    const severity = (match?.[4] ?? fallback?.[1] ?? 'unknown').toLowerCase() as 'error' | 'warning' | 'note';
    diagnostics.push({
      id: match?.[5] ?? fallback?.[2] ?? `D${diagnostics.length + 1}`,
      message: (match?.[6] ?? fallback?.[3] ?? line).trim(),
      severity,
      path: match?.[1] || null,
      line: match?.[2] ? Number(match[2]) : null,
      column: match?.[3] ? Number(match[3]) : null,
      evidenceId
    });
    evidence.push({ id: evidenceId, artifactId, startLine: index + 1, endLine: index + 1, excerpt: line });
  }
  return diagnostics.length ? { payload: { diagnostics }, evidence, coverage: 'complete' } : null;
}

function diffCandidate(lines: string[], artifactId: string): Candidate | null {
  const files: z.infer<typeof DiffPayloadSchema>['files'] = [];
  const evidence: Evidence[] = [];
  let current: { path: string; start: number; additions: number; deletions: number } | undefined;
  const finish = () => {
    if (!current) return;
    const id = `E${evidence.length + 1}`;
    const excerpt = redact(lines[current.start - 1] ?? '');
    evidence.push({ id, artifactId, startLine: current.start, endLine: current.start, excerpt });
    files.push({
      path: current.path,
      summary: `${current.additions} additions, ${current.deletions} deletions`,
      additions: current.additions,
      deletions: current.deletions,
      evidenceIds: [id]
    });
  };
  for (const [index, line] of lines.entries()) {
    const header = /^diff --git a\/(.+?) b\/(.+)$/.exec(line);
    if (header) {
      finish();
      current = { path: header[2] ?? header[1] ?? 'unknown', start: index + 1, additions: 0, deletions: 0 };
    } else if (current && line.startsWith('+') && !line.startsWith('+++')) current.additions += 1;
    else if (current && line.startsWith('-') && !line.startsWith('---')) current.deletions += 1;
  }
  finish();
  return files.length ? { payload: { files }, evidence, coverage: 'complete' } : null;
}

function issueCandidate(lines: string[], artifactId: string): Candidate | null {
  const requirements: z.infer<typeof IssuePayloadSchema>['requirements'] = [];
  const acceptanceCriteria: z.infer<typeof IssuePayloadSchema>['acceptanceCriteria'] = [];
  const evidence: Evidence[] = [];
  let section: 'requirements' | 'acceptance' | null = null;
  for (const [index, raw] of lines.entries()) {
    const line = redact(raw).trim();
    if (/^#{0,6}\s*(requirements?|scope)\s*:?​?$/i.test(line)) {
      section = 'requirements';
      continue;
    }
    if (/^#{0,6}\s*(acceptance criteria|done when)\s*:?​?$/i.test(line)) {
      section = 'acceptance';
      continue;
    }
    const bullet = /^[-*]\s+(.+)$/.exec(line);
    if (!section || !bullet?.[1]) continue;
    const id = `E${evidence.length + 1}`;
    const fact = { text: bullet[1], evidenceId: id };
    if (section === 'requirements') requirements.push(fact);
    else acceptanceCriteria.push(fact);
    evidence.push({ id, artifactId, startLine: index + 1, endLine: index + 1, excerpt: redact(raw) });
  }
  return requirements.length || acceptanceCriteria.length
    ? { payload: { requirements, acceptanceCriteria }, evidence, coverage: 'complete' }
    : null;
}

function deterministic(task: Task, lines: string[], artifactId: string): Candidate | null {
  if (task === 'diagnostics') return diagnosticCandidate(lines, artifactId);
  if (task === 'diff_summary') return diffCandidate(lines, artifactId);
  return issueCandidate(lines, artifactId);
}

function referencedEvidence(payload: Payload): string[] {
  if ('diagnostics' in payload) return payload.diagnostics.map(item => item.evidenceId);
  if ('files' in payload) return payload.files.flatMap(item => item.evidenceIds);
  return [...payload.requirements, ...payload.acceptanceCriteria].map(item => item.evidenceId);
}

function prefixCandidate(candidate: Candidate, prefix: string): Candidate {
  const rename = (id: string) => `${prefix}${id}`;
  const payload = 'diagnostics' in candidate.payload
    ? { diagnostics: candidate.payload.diagnostics.map(item => ({ ...item, evidenceId: rename(item.evidenceId) })) }
    : 'files' in candidate.payload
      ? { files: candidate.payload.files.map(item => ({ ...item, evidenceIds: item.evidenceIds.map(rename) })) }
      : {
          requirements: candidate.payload.requirements.map(item => ({ ...item, evidenceId: rename(item.evidenceId) })),
          acceptanceCriteria: candidate.payload.acceptanceCriteria.map(item => ({ ...item, evidenceId: rename(item.evidenceId) }))
        };
  return {
    ...candidate,
    payload,
    evidence: candidate.evidence.map(item => ({ ...item, id: rename(item.id) }))
  };
}

function mergeCandidates(task: Task, candidates: Candidate[], partial: boolean): Candidate {
  const evidence = candidates.flatMap(candidate => candidate.evidence);
  const payload = task === 'diagnostics'
    ? { diagnostics: candidates.flatMap(candidate => 'diagnostics' in candidate.payload ? candidate.payload.diagnostics : []) }
    : task === 'diff_summary'
      ? { files: candidates.flatMap(candidate => 'files' in candidate.payload ? candidate.payload.files : []) }
      : {
          requirements: candidates.flatMap(candidate => 'requirements' in candidate.payload ? candidate.payload.requirements : []),
          acceptanceCriteria: candidates.flatMap(candidate => 'acceptanceCriteria' in candidate.payload ? candidate.payload.acceptanceCriteria : [])
        };
  return { payload, evidence, coverage: partial ? 'partial' : 'complete' };
}

export class AppleOffloadRuntime {
  readonly mode: Mode;
  readonly stateDir: string;
  readonly roots: string[];
  readonly provider: Provider;
  readonly store: Store;
  private readonly deadlineMs: number;
  // ponytail: process-local queue; add a filesystem lock only if concurrent CLI processes become a real workload.
  private queue: Promise<void> = Promise.resolve();

  constructor(options: RuntimeOptions = {}) {
    this.mode = options.mode ?? ModeSchema.parse(process.env.APPLE_OFFLOAD_MODE ?? 'shadow');
    this.stateDir = path.resolve(options.stateDir ?? process.env.APPLE_OFFLOAD_STATE_DIR ?? defaultStateDir());
    const configuredRoots = options.roots ?? process.env.APPLE_OFFLOAD_ROOTS?.split(path.delimiter).filter(Boolean) ?? [process.cwd()];
    this.roots = configuredRoots.map(root => path.resolve(root));
    this.provider = options.provider ?? new AppleLocalProvider();
    this.deadlineMs = options.deadlineMs ?? DEADLINE_MS;
    this.store = new Store(this.stateDir);
  }

  async initialize(): Promise<void> {
    await mkdir(path.join(this.stateDir, 'snapshots'), { recursive: true, mode: 0o700 });
    await mkdir(path.join(this.stateDir, 'candidates'), { recursive: true, mode: 0o700 });
    await chmod(this.stateDir, 0o700);
    await this.purge();
  }

  async doctor(): Promise<DoctorResult> {
    const probe = await this.provider.probe();
    const setupRequired = probe.reason === 'fm_license_not_accepted';
    return {
      ...probe,
      stateDir: this.stateDir,
      roots: this.roots,
      mode: this.mode,
      setupRequired,
      setupCommand: setupRequired ? 'node dist/cli.js setup' : null
    };
  }

  process(input: unknown): Promise<ProcessResult> {
    const parsed = ProcessInputSchema.parse(input);
    return this.exclusive(() => this.processOnce(parsed.task, parsed.path));
  }

  private async processOnce(task: Task, requestedPath: string): Promise<ProcessResult> {
    const started = Date.now();
    const runId = randomUUID();
    if (this.mode === 'off') {
      const result = this.result(runId, 'needs_codex', null, null, null, [], 'complete', 'mode_off');
      this.record(task, runId, null, result, 0, started, null);
      return result;
    }

    let snapshot: { artifactId: string; content: string; bytes: number };
    try {
      snapshot = await this.snapshot(requestedPath);
    } catch (error) {
      const reason = error instanceof PolicyError ? error.message : 'snapshot_failed';
      const status = reason === 'source_too_large' ? 'needs_codex' : 'blocked';
      const result = this.result(runId, status, null, null, null, [], 'complete', reason);
      this.record(task, runId, null, result, 0, started, null);
      return result;
    }

    const lines = snapshot.content.split(/\r?\n/);
    let route: 'deterministic' | 'local' = 'deterministic';
    let candidate = deterministic(task, lines, snapshot.artifactId);
    let probe: ProbeResult | null = null;
    let reason: string | null = null;

    if (!candidate) {
      route = 'local';
      probe = await this.provider.probe();
      if (!probe.available) reason = probe.reason ?? 'local_model_unavailable';
      else {
        try {
          candidate = await this.generate(task, lines, snapshot.artifactId, started + this.deadlineMs);
        } catch (error) {
          reason = error instanceof Error ? error.message : 'generation_failed';
        }
      }
    }

    if (!candidate) {
      const result = this.result(runId, 'needs_codex', route, snapshot.artifactId, null, [], 'complete', reason ?? 'no_supported_facts');
      this.record(task, runId, snapshot.artifactId, result, snapshot.bytes, started, probe);
      return result;
    }

    try {
      this.validateCandidate(candidate, lines);
    } catch {
      const result = this.result(runId, 'needs_codex', route, snapshot.artifactId, null, [], candidate.coverage, 'invalid_evidence');
      this.record(task, runId, snapshot.artifactId, result, snapshot.bytes, started, probe);
      return result;
    }

    if (this.mode === 'shadow') {
      await writeFile(
        path.join(this.stateDir, 'candidates', `${runId}.json`),
        JSON.stringify(candidate),
        { mode: 0o600 }
      );
      const result = this.result(runId, 'shadow', route, snapshot.artifactId, null, [], candidate.coverage, null);
      this.record(task, runId, snapshot.artifactId, result, snapshot.bytes, started, probe, candidate);
      return result;
    }

    const result = this.result(runId, 'ready', route, snapshot.artifactId, candidate.payload, candidate.evidence, candidate.coverage, null);
    this.record(task, runId, snapshot.artifactId, result, snapshot.bytes, started, probe);
    return result;
  }

  async read(input: unknown): Promise<z.infer<typeof ReadResultSchema>> {
    const parsed = ReadInputSchema.parse(input);
    const snapshotPath = path.join(this.stateDir, 'snapshots', `${parsed.artifactId}.txt`);
    const metadata = await stat(snapshotPath);
    if (Date.now() - metadata.mtimeMs > SNAPSHOT_TTL_MS) throw new Error('artifact_expired');
    const lines = (await readFile(snapshotPath, 'utf8')).split(/\r?\n/);
    const selected = lines.slice(parsed.startLine - 1, parsed.endLine).map(redact).join('\n');
    if (Buffer.byteLength(selected) > 65_536) throw new Error('read_result_too_large');
    return ReadResultSchema.parse({
      artifactId: parsed.artifactId,
      startLine: parsed.startLine,
      endLine: Math.min(parsed.endLine, lines.length),
      text: selected
    });
  }

  feedback(input: unknown): z.infer<typeof FeedbackResultSchema> {
    const parsed = FeedbackInputSchema.parse(input);
    this.store.recordFeedback(parsed.runId, parsed.outcome);
    return FeedbackResultSchema.parse({ ...parsed, recorded: true });
  }

  stats(input: unknown = {}): z.infer<typeof StatsResultSchema> {
    const parsed = StatsInputSchema.parse(input);
    return StatsResultSchema.parse(this.store.stats(parsed.since));
  }

  async purge(all = false): Promise<{ removed: number }> {
    let removed = 0;
    for (const directory of ['snapshots', 'candidates']) {
      const root = path.join(this.stateDir, directory);
      await mkdir(root, { recursive: true, mode: 0o700 });
      for (const entry of await readdir(root, { withFileTypes: true })) {
        if (!entry.isFile()) continue;
        const target = path.join(root, entry.name);
        const metadata = await stat(target);
        if (all || Date.now() - metadata.mtimeMs > SNAPSHOT_TTL_MS) {
          await unlink(target);
          removed += 1;
        }
      }
    }
    return { removed };
  }

  close(): void {
    this.store.close();
  }

  private async snapshot(requestedPath: string): Promise<{ artifactId: string; content: string; bytes: number }> {
    const absolute = path.resolve(requestedPath);
    if (isCredentialPath(absolute)) throw new PolicyError('credential_file_rejected');
    const sourceLstat = await lstat(absolute);
    if (sourceLstat.isSymbolicLink()) throw new PolicyError('symlink_rejected');
    if (!sourceLstat.isFile()) throw new PolicyError('regular_file_required');
    const canonical = await realpath(absolute);
    const canonicalRoots = await Promise.all(this.roots.map(root => realpath(root)));
    if (!canonicalRoots.some(root => within(root, canonical))) throw new PolicyError('path_outside_approved_roots');
    const handle = await open(canonical, fsConstants.O_RDONLY | fsConstants.O_NOFOLLOW);
    try {
      const metadata = await handle.stat();
      if (!metadata.isFile()) throw new PolicyError('regular_file_required');
      if (metadata.size > MAX_SOURCE_BYTES) throw new PolicyError('source_too_large');
      const content = await handle.readFile('utf8');
      const artifactId = randomUUID();
      const digest = createHash('sha256').update(content).digest('hex');
      await writeFile(path.join(this.stateDir, 'snapshots', `${artifactId}.txt`), content, { mode: 0o600, flag: 'wx' });
      await writeFile(path.join(this.stateDir, 'snapshots', `${artifactId}.sha256`), `${digest}\n`, { mode: 0o600, flag: 'wx' });
      return { artifactId, content, bytes: Buffer.byteLength(content) };
    } finally {
      await handle.close();
    }
  }

  private async generate(task: Task, lines: string[], artifactId: string, deadline: number): Promise<Candidate> {
    const chunks: Array<{ start: number; lines: string[] }> = [];
    let current: string[] = [];
    let start = 1;
    let size = 0;
    for (const [index, raw] of lines.entries()) {
      const line = redact(raw);
      if (current.length && size + line.length > CHUNK_CHARACTERS) {
        chunks.push({ start, lines: current });
        if (chunks.length === MAX_CHUNKS) break;
        current = [];
        start = index + 1;
        size = 0;
      }
      current.push(line);
      size += line.length + 1;
    }
    if (current.length && chunks.length < MAX_CHUNKS) chunks.push({ start, lines: current });
    const partial = chunks.reduce((count, chunk) => count + chunk.lines.length, 0) < lines.length;
    const candidates: Candidate[] = [];
    for (const [index, chunk] of chunks.entries()) {
      const numbered = chunk.lines.map((line, offset) => `${chunk.start + offset}: ${line}`).join('\n');
      let lastError: unknown;
      for (let attempt = 0; attempt < 2; attempt += 1) {
        if (deadline - Date.now() < 1_000) throw new Error('deadline_exceeded');
        try {
          const generated = await beforeDeadline(
            this.provider.generate({ task, content: numbered, deadline }),
            deadline
          );
          const candidate = this.parseGenerated(task, generated, artifactId);
          this.validateCandidate(candidate, lines);
          candidates.push(prefixCandidate(candidate, `C${index + 1}_`));
          lastError = undefined;
          break;
        } catch (error) {
          lastError = error;
        }
      }
      if (lastError) throw lastError;
    }
    if (!candidates.length) throw new Error('generation_empty');
    return mergeCandidates(task, candidates, partial);
  }

  private parseGenerated(task: Task, generated: unknown, artifactId: string): Candidate {
    const parsed = task === 'diagnostics'
      ? ModelDiagnosticsSchema.parse(generated)
      : task === 'diff_summary'
        ? ModelDiffSchema.parse(generated)
        : ModelIssueSchema.parse(generated);
    const { evidence: rawEvidence, ...payload } = parsed;
    return {
      payload: payload as Payload,
      evidence: rawEvidence.map(item => ({ ...item, artifactId })),
      coverage: 'complete'
    };
  }

  private validateCandidate(candidate: Candidate, sourceLines: string[]): void {
    const evidenceById = new Map(candidate.evidence.map(item => [item.id, item]));
    if (evidenceById.size !== candidate.evidence.length) throw new Error('duplicate evidence id');
    for (const id of referencedEvidence(candidate.payload)) {
      if (!evidenceById.has(id)) throw new Error('missing evidence');
    }
    for (const item of candidate.evidence) {
      if (item.endLine < item.startLine || item.endLine > sourceLines.length) throw new Error('invalid evidence range');
      const actual = sourceLines.slice(item.startLine - 1, item.endLine).map(redact).join('\n').trim();
      if (actual !== item.excerpt.trim()) throw new Error('evidence mismatch');
    }
    const serialized = JSON.stringify(candidate);
    if (estimateTokens(serialized) > RESPONSE_TOKEN_BUDGET) throw new Error('response_budget_exceeded');
  }

  private result(
    runId: string,
    status: ProcessResult['status'],
    routeUsed: ProcessResult['routeUsed'],
    artifactId: string | null,
    payload: Payload | null,
    evidence: Evidence[],
    coverage: ProcessResult['coverage'],
    reason: string | null
  ): ProcessResult {
    return ProcessResultSchema.parse({ runId, status, routeUsed, artifactId, payload, evidence, coverage, reason });
  }

  private record(
    task: Task,
    runId: string,
    artifactId: string | null,
    result: ProcessResult,
    sourceBytes: number,
    started: number,
    probe: ProbeResult | null,
    candidate?: Candidate
  ): void {
    const output = candidate ? JSON.stringify(candidate) : JSON.stringify(result);
    this.store.recordRun({
      runId,
      artifactId,
      task,
      mode: this.mode,
      result,
      sourceBytes,
      outputBytes: Buffer.byteLength(output),
      estimatedInputTokens: sourceBytes ? Math.ceil(sourceBytes / 4) : null,
      estimatedOutputTokens: estimateTokens(output),
      latencyMs: Date.now() - started,
      validation: result.status === 'ready' || result.status === 'shadow' ? 'passed' : 'not_run',
      providerVersion: probe?.providerVersion ?? (result.routeUsed === 'deterministic' ? 'deterministic-v1' : null),
      osVersion: probe?.osVersion ?? null
    });
  }

  private async exclusive<T>(operation: () => Promise<T>): Promise<T> {
    const previous = this.queue;
    let release!: () => void;
    this.queue = new Promise<void>(resolve => { release = resolve; });
    await previous;
    try {
      return await operation();
    } finally {
      release();
    }
  }
}
