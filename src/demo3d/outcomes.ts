import type { GameEvent, GameState } from '../core/game.js';

export type OutcomeCue = Readonly<{
  stage: 'bankrupt' | 'victory' | 'draw';
  actorId: string | null;
  winnerId: string | null;
  nonce: number;
}>;

/** Translates only this action's real events; never settles rules or replays old results. */
export function outcomeSequence(events: readonly GameEvent[], game: GameState): readonly OutcomeCue[] {
  const cues: OutcomeCue[] = [];
  for (const event of events) {
    if (event.type === 'player_bankrupt' && event.actorId) {
      cues.push({ stage: 'bankrupt', actorId: event.actorId, winnerId: null, nonce: game.revision + cues.length });
    }
  }
  if (events.some(event => event.type === 'game_finished')) {
    cues.push({
      stage: game.winnerId === null ? 'draw' : 'victory',
      actorId: game.winnerId,
      winnerId: game.winnerId,
      nonce: game.revision + cues.length
    });
  }
  return cues;
}
