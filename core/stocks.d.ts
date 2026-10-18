/** P3-10: deterministic trades with an optional bank settlement account on the five invented market quotations. */
import type { GameState, Player, GameAction, ActionResult, GameEvent, StockHoldings } from './types.js';
export declare const STOCK_FEE_BPS = 50;
export declare const MAX_SHARES = 1000000;
export declare function stockFee(gross: number): number;
export declare function tradeStock(state: GameState, actor: Player, action: Extract<GameAction, {
    type: 'buy_stock' | 'sell_stock';
}>): ActionResult;
/** Pay rent from quoted, fee-adjusted shares before selling land. Full lots only, in fixed symbol order. */
export declare function liquidateStocksForRent(state: GameState, actor: Player, due: number): {
    cash: number;
    holdings: StockHoldings | undefined;
    events: readonly GameEvent[];
};
