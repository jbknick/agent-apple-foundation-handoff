import type { ModelRoute, Task } from './schemas.js';

export interface ProbeResult {
  available: boolean;
  reason: string | null;
  osVersion: string | null;
  providerVersion: string | null;
  structuredOutput: boolean;
  localModelVerified: boolean;
  argvPromptExposure: boolean;
}

export interface GenerateRequest {
  task: Task;
  content: string;
  deadline: number;
}

export interface Provider {
  probe(): Promise<ProbeResult>;
  generate(request: GenerateRequest): Promise<unknown>;
}

export class MockProvider implements Provider {
  constructor(
    private readonly response: unknown,
    private readonly available = true
  ) {}

  async probe(): Promise<ProbeResult> {
    return {
      available: this.available,
      reason: this.available ? null : 'mock_unavailable',
      osVersion: 'mock-os',
      providerVersion: 'mock-v1',
      structuredOutput: this.available,
      localModelVerified: this.available,
      argvPromptExposure: false
    };
  }

  async generate(_request: GenerateRequest): Promise<unknown> {
    if (!this.available) throw new Error('mock_unavailable');
    return structuredClone(this.response);
  }
}

export interface RouteProvider {
  route: ModelRoute;
  provider: Provider;
}

export interface RouteFailure {
  route: ModelRoute;
  reason: string;
}

export type RouteOutcome<T> =
  | { route: ModelRoute; value: T; probe: ProbeResult; failures: RouteFailure[] }
  | { route: null; probe: ProbeResult | null; failures: RouteFailure[] };

// Tries each allowed Apple model route in order for a whole run, so one route
// serves every chunk. A probe that reports unavailable or an attempt that throws
// (including a deadline) records the reason and falls back to the next route.
export class RouteChain {
  constructor(readonly routes: readonly RouteProvider[]) {
    if (!routes.length) throw new Error('at least one model route is required');
  }

  async serve<T>(attempt: (provider: Provider, isLastRoute: boolean) => Promise<T>): Promise<RouteOutcome<T>> {
    const failures: RouteFailure[] = [];
    let probe: ProbeResult | null = null;
    for (const [index, { route, provider }] of this.routes.entries()) {
      probe = await provider.probe();
      if (!probe.available) {
        failures.push({ route, reason: probe.reason ?? `${route}_unavailable` });
        continue;
      }
      try {
        const value = await attempt(provider, index === this.routes.length - 1);
        return { route, value, probe, failures };
      } catch (error) {
        failures.push({ route, reason: error instanceof Error ? error.message : 'generation_failed' });
      }
    }
    return { route: null, probe, failures };
  }

  // A single-route chain keeps the bare reason; otherwise every route is named.
  describeFailures(failures: readonly RouteFailure[]): string | null {
    if (!failures.length) return null;
    if (this.routes.length === 1) return failures[0]!.reason;
    return failures.map(failure => `${failure.route}:${failure.reason}`).join(';');
  }
}
