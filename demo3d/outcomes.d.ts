import type { GameEvent, GameState } from '../core/game.js';
export type OutcomeCue = Readonly<{
    stage: 'bankrupt' | 'victory' | 'draw';
    actorId: string | null;
    winnerId: string | null;
    nonce: number;
}>;
/** Translates only this action's real events; never settles rules or replays old results. */
export declare function outcomeSequence(events: readonly GameEvent[], game: GameState): readonly OutcomeCue[];
