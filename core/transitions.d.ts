/** Shared immutable command transition primitives; not public game actions. */
import type { GameState, GameEvent, ActionResult, RejectReason } from './types.js';
export declare function reject(state: GameState, reason: RejectReason): ActionResult;
export declare function accept(state: GameState, events: readonly GameEvent[], changes: Partial<GameState>): ActionResult;
