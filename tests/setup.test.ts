import { expect, it, vi } from 'vitest';
import { acceptFmTerms } from '../src/setup.js';

it('requires exact confirmation before launching the fixed Apple license command', async () => {
  const run = vi.fn(async () => 0);
  expect(await acceptFmTerms('yes', run)).toEqual({ status: 'declined', exitCode: null });
  expect(run).not.toHaveBeenCalled();

  expect(await acceptFmTerms('ACCEPT', run)).toEqual({ status: 'accepted', exitCode: 0 });
  expect(run).toHaveBeenCalledWith('/usr/bin/sudo', ['/usr/bin/fm', 'license']);
});
