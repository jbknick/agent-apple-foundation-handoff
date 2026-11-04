import { expect, it } from 'vitest';
import { hasUnacceptedLicenseNotice } from '../src/apple-local.js';

it('distinguishes the unaccepted notice from normal help mentioning license', () => {
  expect(hasUnacceptedLicenseNotice('license  Show and agree to the Legal Notice & Terms')).toBe(false);
  expect(hasUnacceptedLicenseNotice(
    'YOU HAVE NOT AGREED TO THE APPLE FOUNDATION MODELS CLI LEGAL NOTICE & TERMS.'
  )).toBe(true);
});
