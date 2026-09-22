import type { Task } from './schemas.js';

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
