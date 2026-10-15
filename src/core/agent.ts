/** 简单、确定性电脑玩家：从只读状态选择合法命令，不直接修改引擎数据。 */
import { type GameAction, type GameState } from './game.js';
export interface ComputerOptions { readonly reserveCash?: number }
export function choosePhaseAction(state: GameState, reserveCash: number): GameAction | null {
  if (!Number.isFinite(reserveCash) || reserveCash < 0) throw new Error('保留资金必须为非负有限数字');
  if (state.status !== 'playing') return null;
  const player = state.players[state.currentPlayerIndex];
  if (!player) return null;
  switch (state.phase) {
    case 'await_roll': return { type: 'roll', actorId: player.id };
    case 'await_decision': {
      const tile = state.tiles[player.position];
      if (!tile || tile.kind !== 'property' || tile.ownerId !== null) throw new Error('待购地状态与棋盘数据不一致');
      return { type: player.cash >= (tile.price ?? 0) + reserveCash ? 'buy_property' : 'decline_property', actorId: player.id };
    }
    case 'await_end_turn': return { type: 'end_turn', actorId: player.id };
    default: return null;
  }
}
export function chooseComputerAction(state: GameState, options: ComputerOptions = {}): GameAction | null {
  const reserveCash = options.reserveCash ?? 200;
  if (!Number.isFinite(reserveCash) || reserveCash < 0) throw new Error('保留资金必须为非负有限数字');
  const player = state.players[state.currentPlayerIndex];
  if (!player || player.kind !== 'computer') return null;
  return choosePhaseAction(state, reserveCash);
}
