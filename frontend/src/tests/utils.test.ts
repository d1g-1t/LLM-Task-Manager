import { describe, expect, it } from 'vitest';
import { cn, formatDate, isOverdue } from '@/lib/utils';

describe('utils', () => {
  it('cn merges tailwind classes', () => {
    expect(cn('p-2', false && 'hidden', 'p-4')).toBe('p-4');
  });

  it('formatDate handles null', () => {
    expect(formatDate(null)).toBe('—');
  });

  it('isOverdue returns true for past dates not done', () => {
    const past = new Date(Date.now() - 86400000).toISOString();
    expect(isOverdue(past, 'pending')).toBe(true);
    expect(isOverdue(past, 'done')).toBe(false);
    expect(isOverdue(null, 'pending')).toBe(false);
  });
});
