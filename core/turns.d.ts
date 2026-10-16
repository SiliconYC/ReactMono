/** Turn movement, landing settlement and round-end decisions. */
import type { GameState, Player, ActionResult } from './types.js';
export declare function rollTurn(state: GameState, actor: Player): ActionResult;
export declare function endTurn(state: GameState, actor: Player): ActionResult;
