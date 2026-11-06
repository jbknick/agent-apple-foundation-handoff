import { z } from 'zod';

export const TaskSchema = z.enum(['diagnostics', 'diff_summary', 'issue_extract']);
export const ModeSchema = z.enum(['off', 'shadow', 'on']);
export const StatusSchema = z.enum(['ready', 'shadow', 'needs_agent', 'blocked']);
// Deprecated: the old name of `needs_agent` (renamed in #34), echoed as `legacyStatus` for one minor release.
export const LegacyStatusSchema = z.literal('needs_codex');
export const RouteSchema = z.enum(['deterministic', 'local']);
// Which Apple model route served a `local` run; null when no model route served it.
export const ModelRouteSchema = z.enum(['on_device', 'pcc']);
// User configuration only (APPLE_OFFLOAD_ROUTE); never a request field.
export const RoutePreferenceSchema = z.enum(['on_device', 'pcc_preferred']);
export const CoverageSchema = z.enum(['complete', 'partial']);

export const ProcessInputSchema = z.object({
  task: TaskSchema,
  path: z.string().min(1)
}).strict();

export const ReadInputSchema = z.object({
  artifactId: z.string().uuid(),
  startLine: z.number().int().min(1),
  endLine: z.number().int().min(1)
}).strict().refine(({ startLine, endLine }) => endLine >= startLine, {
  message: 'endLine must be greater than or equal to startLine'
}).refine(({ startLine, endLine }) => endLine - startLine < 200, {
  message: 'read range cannot exceed 200 lines'
});

export const FeedbackInputSchema = z.object({
  runId: z.string().uuid(),
  outcome: z.enum(['accepted', 'corrected', 'rejected'])
}).strict();

export const StatsInputSchema = z.object({
  since: z.iso.datetime({ offset: true }).optional()
}).strict();

export const EvidenceSchema = z.object({
  id: z.string().min(1),
  artifactId: z.string().uuid(),
  startLine: z.number().int().min(1),
  endLine: z.number().int().min(1),
  excerpt: z.string().max(2_048)
}).strict();

export const DiagnosticSchema = z.object({
  id: z.string().min(1),
  message: z.string().min(1),
  severity: z.enum(['error', 'warning', 'note', 'unknown']),
  path: z.string().nullable(),
  line: z.number().int().min(1).nullable(),
  column: z.number().int().min(1).nullable(),
  evidenceId: z.string().min(1)
}).strict();

export const DiagnosticsPayloadSchema = z.object({
  diagnostics: z.array(DiagnosticSchema).max(200)
}).strict();

export const DiffFileSchema = z.object({
  path: z.string().min(1),
  summary: z.string().min(1),
  additions: z.number().int().min(0),
  deletions: z.number().int().min(0),
  evidenceIds: z.array(z.string().min(1)).min(1)
}).strict();

export const DiffPayloadSchema = z.object({
  files: z.array(DiffFileSchema).max(200)
}).strict();

export const IssueFactSchema = z.object({
  text: z.string().min(1),
  evidenceId: z.string().min(1)
}).strict();

export const IssuePayloadSchema = z.object({
  requirements: z.array(IssueFactSchema).max(200),
  acceptanceCriteria: z.array(IssueFactSchema).max(200)
}).strict();

export const PayloadSchema = z.union([
  DiagnosticsPayloadSchema,
  DiffPayloadSchema,
  IssuePayloadSchema
]);

export const ProcessResultSchema = z.object({
  runId: z.string().uuid(),
  status: StatusSchema,
  routeUsed: RouteSchema.nullable(),
  modelRoute: ModelRouteSchema.nullable(),
  artifactId: z.string().uuid().nullable(),
  payload: PayloadSchema.nullable(),
  evidence: z.array(EvidenceSchema),
  coverage: CoverageSchema,
  reason: z.string().nullable(),
  legacyStatus: LegacyStatusSchema.optional().describe(
    'Deprecated: present only when status is needs_agent; removed after one minor release.'
  )
}).strict().refine(({ status, legacyStatus }) => (status === 'needs_agent') === (legacyStatus !== undefined), {
  message: 'legacyStatus is required for needs_agent and forbidden otherwise',
  path: ['legacyStatus']
});

export const ReadResultSchema = z.object({
  artifactId: z.string().uuid(),
  startLine: z.number().int().min(1),
  endLine: z.number().int().min(1),
  text: z.string().max(65_536)
}).strict();

export const FeedbackResultSchema = z.object({
  runId: z.string().uuid(),
  outcome: z.enum(['accepted', 'corrected', 'rejected']),
  recorded: z.literal(true)
}).strict();

export const StatsResultSchema = z.object({
  since: z.string().nullable(),
  runs: z.number().int().min(0),
  ready: z.number().int().min(0),
  shadow: z.number().int().min(0),
  needsAgent: z.number().int().min(0),
  needsCodex: z.number().int().min(0).describe('Deprecated alias of needsAgent; removed after one minor release.'),
  blocked: z.number().int().min(0),
  sourceBytes: z.number().int().min(0),
  outputBytes: z.number().int().min(0),
  averageLatencyMs: z.number().min(0).nullable(),
  modelRoutes: z.object({
    on_device: z.number().int().min(0),
    pcc: z.number().int().min(0)
  }).strict(),
  feedback: z.object({
    accepted: z.number().int().min(0),
    corrected: z.number().int().min(0),
    rejected: z.number().int().min(0)
  }).strict()
}).strict();

export type Task = z.infer<typeof TaskSchema>;
export type Mode = z.infer<typeof ModeSchema>;
export type ModelRoute = z.infer<typeof ModelRouteSchema>;
export type RoutePreference = z.infer<typeof RoutePreferenceSchema>;
export type Evidence = z.infer<typeof EvidenceSchema>;
export type Payload = z.infer<typeof PayloadSchema>;
export type ProcessResult = z.infer<typeof ProcessResultSchema>;
export type StatsResult = z.infer<typeof StatsResultSchema>;
