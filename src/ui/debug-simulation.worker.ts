import { simulateDebugRounds, type DebugSimulationResult } from '../core/debug-tools.js';
import type { GameState } from '../core/types.js';

export interface DebugSimulationRequest { readonly requestId: number; readonly game: GameState; readonly rounds: number; }
export type DebugSimulationReply =
  | { readonly requestId: number; readonly ok: true; readonly result: DebugSimulationResult }
  | { readonly requestId: number; readonly ok: false; readonly error: string };

const scope = self as unknown as {
  onmessage: ((event: MessageEvent<DebugSimulationRequest>) => void) | null;
  postMessage: (reply: DebugSimulationReply) => void;
};
scope.onmessage = ({ data }) => {
  try {
    scope.postMessage({ requestId: data.requestId, ok: true, result: simulateDebugRounds(data.game, data.rounds) });
  } catch (error) {
    scope.postMessage({ requestId: data.requestId, ok: false, error: error instanceof Error ? error.message : String(error) });
  }
};
