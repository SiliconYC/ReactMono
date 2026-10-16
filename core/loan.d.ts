/** P3-08: deterministic secured loans. The bank is a virtual lender, never another player. */
import type { GameState, Player, Tile, GameAction, ActionResult, GameEvent, LoanState } from './types.js';
export declare const DEFAULT_LOAN_INTEREST_BPS = 200;
export declare function createLoan(interestBps?: number): LoanState;
export declare function loanLimit(state: GameState, playerId: string, excludeId?: number): number;
export declare function transferLoan(state: GameState, actor: Player, action: Extract<GameAction, {
    type: 'mortgage_property' | 'release_mortgage' | 'borrow_loan' | 'repay_loan';
}>): ActionResult;
/** Compounding is only allowed while collateral covers it. Otherwise the lender seizes pledged land.
 * Pledged collateral's resale value repays principal and excess proceeds return to the borrower.
 * Deficiency is recorded as a bank loss (not shifted to another player).
 */
export declare function foreclose(state: GameState, player: Player, tiles: readonly Tile[]): {
    player: Player;
    tiles: readonly Tile[];
    events: readonly GameEvent[];
};
export declare function settleLoanRound(state: GameState, players: readonly Player[], tiles: readonly Tile[], round: number): {
    loan: LoanState;
    players: readonly Player[];
    tiles: readonly Tile[];
    events: readonly GameEvent[];
};
