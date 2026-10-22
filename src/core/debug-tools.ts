import { applyAction } from './game.js';
import { chooseComputerAction, choosePhaseAction } from './agent.js';
import { validateGameState } from './save.js';
import type { GameState } from './types.js';

export const MAX_DEBUG_CASH = 1_000_000_000_000;
export const MAX_DEBUG_ROUNDS = 100_000;

export function setDebugCash(state: GameState, playerId: string, cash: number): GameState {
  if (state.status !== 'playing') throw new Error('仅进行中的对局可以设置现金');
  if (!Number.isSafeInteger(cash) || cash < 0 || cash > MAX_DEBUG_CASH)
    throw new Error('现金必须是 0 至 1000000000000 的整数');
  if (!state.players.some(player => player.id === playerId)) throw new Error('找不到该玩家');
  // 调试赋值不伪造规则事件，也不占用规则动作的 revision；并发检查使用整个状态引用。
  const next = { ...state, players: state.players.map(player => player.id === playerId ? { ...player, cash } : player) };
  validateGameState(next);
  return next;
}

export interface DebugSimulationResult { readonly state: GameState; readonly actions: number; }
export function simulateDebugRounds(state: GameState, rounds: number, maxActions = 100_000): DebugSimulationResult {
  if (!Number.isSafeInteger(rounds) || rounds < 1 || rounds > MAX_DEBUG_ROUNDS)
    throw new Error('模拟轮数必须是 1 至 100000 的整数');
  if (!Number.isSafeInteger(maxActions) || maxActions < 1 || maxActions > 100_000)
    throw new Error('模拟动作上限无效');
  validateGameState(state);
  if (state.status === 'setup') throw new Error('请先开始对局');
  let current = state;
  let actions = 0;
  const targetRound = state.round + rounds;
  while (current.status === 'playing' && current.round < targetRound) {
    if (actions >= maxActions) throw new Error('模拟动作达到安全上限，原对局保持不变；请减少轮数');
    const player = current.players[current.currentPlayerIndex];
    const action = player.kind === 'computer'
      ? chooseComputerAction(current, { reserveCash: 200 })
      : choosePhaseAction(current, 200);
    if (!action) throw new Error('当前阶段没有可执行动作，原对局保持不变');
    const result = applyAction(current, action);
    if (!result.ok) throw new Error(`模拟操作被规则拒绝（${result.reason}），原对局保持不变`);
    current = result.state;
    actions++;
    // 沿用既有存档容量；不能截掉事件来绕过校验，否则 revision 与历史将失去一致性。
    if (current.events.length > 10_000) throw new Error('模拟超过现有存档事件上限，原对局保持不变；请减少轮数');
  }
  validateGameState(current);
  return { state: current, actions };
}
