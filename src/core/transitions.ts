/** Shared immutable command transition primitives; not public game actions. */
import type { GameState, GameEvent, ActionResult, RejectReason } from './types.js';
import { assertMoneyState } from './money.js';
export function reject(state: GameState, reason: RejectReason): ActionResult {
  return { ok: false, reason, state, events: [] };
}
export function accept(state: GameState, events: readonly GameEvent[], changes: Partial<GameState>): ActionResult {
  assertMoneyState(state);
  const next = { ...state, ...changes, revision: state.revision + 1, events: [...state.events, ...events] };
  assertMoneyState(next);
  return {
    ok: true,
    events,
    state: next
  };
}
