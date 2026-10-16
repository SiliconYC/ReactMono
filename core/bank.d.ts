/** Optional, deterministic local bank ledger. No network or real funds. */
import type { GameState, Player, GameAction, ActionResult, GameEvent, BankState } from './types.js';
export declare const DEFAULT_INTEREST_BPS = 100;
export declare const MAX_BANK_BALANCE = 1000000000000;
export declare function createBank(interestBps?: number): BankState;
export declare function transferBank(state: GameState, actor: Player, action: Extract<GameAction, {
    type: 'deposit_bank' | 'withdraw_bank';
}>): ActionResult;
/** Cash-first debt settlement, then automatic withdrawal, before #35 land liquidation. */
export declare function coverRentFromBank(state: GameState, actor: Player, due: number): {
    cash: number;
    bankBalance: number;
    amount: number;
};
export declare function settleBankRound(state: GameState, players: readonly Player[], round: number): {
    bank: BankState;
    players: readonly Player[];
    events: readonly GameEvent[];
};
