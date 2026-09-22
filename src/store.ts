import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import type { Mode, ProcessResult, StatsResult, Task } from './schemas.js';

export interface RunRecord {
  runId: string;
  artifactId: string | null;
  task: Task;
  mode: Mode;
  result: ProcessResult;
  sourceBytes: number;
  outputBytes: number;
  estimatedInputTokens: number | null;
  estimatedOutputTokens: number | null;
  latencyMs: number;
  validation: 'passed' | 'failed' | 'not_run';
  providerVersion: string | null;
  osVersion: string | null;
}

export class Store {
  readonly database: DatabaseSync;

  constructor(stateDir: string) {
    mkdirSync(stateDir, { recursive: true, mode: 0o700 });
    this.database = new DatabaseSync(path.join(stateDir, 'state.sqlite'), {
      timeout: 5_000
    });
    this.database.exec(`
      PRAGMA journal_mode = WAL;
      PRAGMA foreign_keys = ON;
      CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY
      ) STRICT;
      INSERT OR IGNORE INTO schema_version(version) VALUES (1);
      CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        artifact_id TEXT,
        task TEXT NOT NULL,
        mode TEXT NOT NULL,
        route_used TEXT,
        status TEXT NOT NULL,
        coverage TEXT NOT NULL,
        reason TEXT,
        source_bytes INTEGER NOT NULL,
        output_bytes INTEGER NOT NULL,
        estimate_method TEXT NOT NULL,
        estimated_input_tokens INTEGER,
        estimated_output_tokens INTEGER,
        latency_ms INTEGER NOT NULL,
        validation TEXT NOT NULL,
        os_version TEXT,
        provider_version TEXT,
        prompt_version TEXT NOT NULL,
        created_at TEXT NOT NULL
      ) STRICT;
      CREATE TABLE IF NOT EXISTS feedback (
        run_id TEXT PRIMARY KEY REFERENCES runs(run_id) ON DELETE CASCADE,
        outcome TEXT NOT NULL,
        created_at TEXT NOT NULL
      ) STRICT;
    `);
  }

  recordRun(record: RunRecord): void {
    this.database.prepare(`
      INSERT INTO runs (
        run_id, artifact_id, task, mode, route_used, status, coverage, reason,
        source_bytes, output_bytes, estimate_method, estimated_input_tokens,
        estimated_output_tokens, latency_ms, validation, os_version,
        provider_version, prompt_version, created_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      record.runId,
      record.artifactId,
      record.task,
      record.mode,
      record.result.routeUsed,
      record.result.status,
      record.result.coverage,
      record.result.reason,
      record.sourceBytes,
      record.outputBytes,
      'chars_div_4_v1',
      record.estimatedInputTokens,
      record.estimatedOutputTokens,
      record.latencyMs,
      record.validation,
      record.osVersion,
      record.providerVersion,
      'apple-offload-v0',
      new Date().toISOString()
    );
  }

  recordFeedback(runId: string, outcome: string): void {
    const exists = this.database.prepare('SELECT 1 FROM runs WHERE run_id = ?').get(runId);
    if (!exists) throw new Error('unknown runId');
    this.database.prepare(`
      INSERT INTO feedback(run_id, outcome, created_at) VALUES (?, ?, ?)
      ON CONFLICT(run_id) DO UPDATE SET outcome = excluded.outcome, created_at = excluded.created_at
    `).run(runId, outcome, new Date().toISOString());
  }

  stats(since?: string): StatsResult {
    const filter = since ? 'WHERE created_at >= ?' : '';
    const args = since ? [since] : [];
    const aggregate = this.database.prepare(`
      SELECT
        COUNT(*) AS runs,
        SUM(CASE WHEN status = 'ready' THEN 1 ELSE 0 END) AS ready,
        SUM(CASE WHEN status = 'shadow' THEN 1 ELSE 0 END) AS shadow,
        SUM(CASE WHEN status = 'needs_codex' THEN 1 ELSE 0 END) AS needs_codex,
        SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) AS blocked,
        COALESCE(SUM(source_bytes), 0) AS source_bytes,
        COALESCE(SUM(output_bytes), 0) AS output_bytes,
        AVG(latency_ms) AS average_latency_ms
      FROM runs ${filter}
    `).get(...args) as Record<string, number | null>;
    const feedback = this.database.prepare(`
      SELECT
        SUM(CASE WHEN outcome = 'accepted' THEN 1 ELSE 0 END) AS accepted,
        SUM(CASE WHEN outcome = 'corrected' THEN 1 ELSE 0 END) AS corrected,
        SUM(CASE WHEN outcome = 'rejected' THEN 1 ELSE 0 END) AS rejected
      FROM feedback ${since ? 'WHERE created_at >= ?' : ''}
    `).get(...args) as Record<string, number | null>;
    return {
      since: since ?? null,
      runs: aggregate.runs ?? 0,
      ready: aggregate.ready ?? 0,
      shadow: aggregate.shadow ?? 0,
      needsCodex: aggregate.needs_codex ?? 0,
      blocked: aggregate.blocked ?? 0,
      sourceBytes: aggregate.source_bytes ?? 0,
      outputBytes: aggregate.output_bytes ?? 0,
      averageLatencyMs: aggregate.average_latency_ms ?? null,
      feedback: {
        accepted: feedback.accepted ?? 0,
        corrected: feedback.corrected ?? 0,
        rejected: feedback.rejected ?? 0
      }
    };
  }

  close(): void {
    this.database.close();
  }
}
