import { hasUnacceptedLicenseNotice, run, type CommandResult } from './apple-local.js';
import type { GenerateRequest, ProbeResult, Provider } from './provider.js';

// Apple Private Cloud Compute route (`pcc`), probe only.
//
// docs/pcc-research.md found that `/usr/bin/fm` exposes only the on-device
// `system` model, and that PCC is reachable only from Swift through
// PrivateCloudComputeLanguageModel behind a managed entitlement. This provider
// therefore never builds a PCC request. It probes the installed `fm` help text
// so the runtime reports PCC as unavailable from a real check rather than a
// hard-coded value, and the route chain falls back to on-device.
//
// Follow-up: if Apple confirms the entitlement covers this CLI, a signed Swift
// helper owns PCC calls and this provider invokes it. Until then `generate`
// always throws. This provider never runs `fm license` or `apple-offload setup`.

const FM_PATH = '/usr/bin/fm';
const PCC_IN_HELP = /private[\s-]*cloud|\bpcc\b/i;

export type FmHelpRunner = (args: string[]) => Promise<CommandResult>;

const runFmHelp: FmHelpRunner = args => run(FM_PATH, args, 3_000);

export function fmHelpAdvertisesPcc(helpText: string): boolean {
  return PCC_IN_HELP.test(helpText);
}

export class PccProvider implements Provider {
  private probePromise: Promise<ProbeResult> | undefined;

  constructor(
    private readonly runHelp: FmHelpRunner = runFmHelp,
    private readonly platform: NodeJS.Platform = process.platform
  ) {}

  probe(): Promise<ProbeResult> {
    this.probePromise ??= this.probeOnce();
    return this.probePromise;
  }

  async generate(_request: GenerateRequest): Promise<unknown> {
    const probe = await this.probe();
    // No PCC invocation exists until the Swift helper lands.
    throw new Error(probe.reason ?? 'pcc_unavailable');
  }

  private async probeOnce(): Promise<ProbeResult> {
    if (this.platform !== 'darwin') return this.blocked('macos_27_required');
    try {
      const [help, respondHelp] = await Promise.all([
        this.runHelp(['--help']),
        this.runHelp(['respond', '--help'])
      ]);
      const combined = [help.stdout, help.stderr, respondHelp.stdout, respondHelp.stderr].join('\n');
      if (hasUnacceptedLicenseNotice(combined)) return this.blocked('fm_license_not_accepted');
      if (help.code !== 0 || respondHelp.code !== 0) return this.blocked('fm_interface_unavailable');
      if (!fmHelpAdvertisesPcc(combined)) return this.blocked('fm_has_no_pcc_model');
      // fm now advertises a PCC model, but nothing here can call it yet.
      return this.blocked('pcc_invocation_not_implemented');
    } catch {
      return this.blocked('fm_probe_failed');
    }
  }

  private blocked(reason: string): ProbeResult {
    return {
      available: false,
      reason,
      osVersion: null,
      providerVersion: null,
      structuredOutput: false,
      localModelVerified: false,
      argvPromptExposure: false
    };
  }
}
