/** Turn movement, landing settlement and round-end decisions. */
import type { GameState, Player, ActionResult } from './types.js';
export declare function rollTurn(state: GameState, actor: Player): ActionResult;
/** The next live participant, wrapping past bankrupt seats. */
export declare function nextActiveIndex(players: readonly Player[], current: number): number;
export declare function endTurn(state: GameState, actor: Player): ActionResult;
