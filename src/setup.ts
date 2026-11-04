import { spawn } from 'node:child_process';

export interface LicenseResult {
  status: 'accepted' | 'declined' | 'failed';
  exitCode: number | null;
}

type CommandRunner = (command: string, args: string[]) => Promise<number>;

function runPrivileged(command: string, args: string[]): Promise<number> {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      shell: false,
      stdio: ['inherit', process.stderr, process.stderr]
    });
    child.once('error', reject);
    child.once('close', code => resolve(code ?? -1));
  });
}

export async function acceptFmTerms(
  confirmation: string,
  run: CommandRunner = runPrivileged
): Promise<LicenseResult> {
  if (confirmation !== 'ACCEPT') return { status: 'declined', exitCode: null };
  const exitCode = await run('/usr/bin/sudo', ['/usr/bin/fm', 'license']);
  return { status: exitCode === 0 ? 'accepted' : 'failed', exitCode };
}
