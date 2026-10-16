/** Card actions are deterministic and may only be invoked by the active player. */
import type { GameState, Player, GameAction, ActionResult } from './types.js';
export declare function useCard(state: GameState, actor: Player, action: Extract<GameAction, {
    type: 'use_card';
}>): ActionResult;
