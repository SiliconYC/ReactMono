/** Pure finite-state rules for hospitals, prisons and inventory-limited shops. */
import type { GameState, Player, GameAction, ActionResult } from './types.js';
export declare function buyShopCard(state: GameState, actor: Player, action: Extract<GameAction, {
    type: 'buy_shop_card';
}>): ActionResult;
export declare function leaveShop(state: GameState, actor: Player): ActionResult;
/** Skips only the current detained player's turn; no dice draw or property event. */
export declare function skipDetentionTurn(state: GameState, actor: Player): ActionResult;
