/** Shared immutable command transition primitives; not public game actions. */
import type { GameState, GameEvent, ActionResult, RejectReason } from './types.js';
export function reject(state: GameState, reason: RejectReason): ActionResult {
  return { ok: false, reason, state, events: [] };
}
export function accept(state: GameState, events: readonly GameEvent[], changes: Partial<GameState>): ActionResult {
  return {
    ok: true,
    events,
    state: { ...state, ...changes, revision: state.revision + 1, events: [...state.events, ...events] }
  };
}
