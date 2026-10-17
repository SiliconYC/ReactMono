import type { GameEvent } from '../core/game.js';

export type RentCue = Readonly<{ fromId: string; toId: string; tileId: number; amount: number }>;

export function rentCueFor(events: readonly GameEvent[]): RentCue | null {
  const details = events.find(event => event.type === 'rent_paid')?.details;
  if (typeof details?.fromId !== 'string' || typeof details.toId !== 'string' ||
      typeof details.tileId !== 'number' || typeof details.amount !== 'number') return null;
  return { fromId: details.fromId, toId: details.toId, tileId: details.tileId, amount: details.amount };
}
