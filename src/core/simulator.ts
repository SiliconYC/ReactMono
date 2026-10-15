/** 真实引擎无界面完整对局；记录种子与每一步，拒绝循环或伪造终局。 */
import { applyAction, createGame, type GameAction, type GameConfig, type GameState, DEFAULT_CONFIG } from './game.js';
import { chooseComputerAction, choosePhaseAction } from './agent.js';
export interface SimulationOptions { readonly config?: GameConfig; readonly reserveCash?: number; readonly humanReserveCash?: number; readonly maxActions?: number }
export interface SimulationReport {
  readonly seed: number; readonly finalState: GameState; readonly playerTurns: number;
  readonly actions: number; readonly rejections: number; readonly finishReason: string; readonly trace: readonly string[];
}
export function runSimulation(seed: number, options: SimulationOptions = {}): SimulationReport {
  const config = options.config ?? DEFAULT_CONFIG;
  const reserveCash = options.reserveCash ?? 200;
  const humanReserveCash = options.humanReserveCash ?? 100;
  if (![reserveCash, humanReserveCash].every(x => Number.isFinite(x) && x >= 0)) throw new Error('保留资金必须为非负有限数字');
  const maxActions = options.maxActions ?? config.maxRounds * 6;
  if (!Number.isInteger(maxActions) || maxActions < 1) throw new Error('动作上限必须为正整数');
  const start = createGame(seed, config);
  const ready = applyAction(start, { type: 'start_game', actorId: start.players[0].id });
  if (!ready.ok) throw new Error('seed=' + seed + ' 无法开始模拟：' + ready.reason);
  let state = ready.state, actions = 0, playerTurns = 0;
  const trace: string[] = [];
  while (state.status !== 'finished') {
    if (actions >= maxActions) throw new Error('seed=' + seed + ' 执行超过动作上限 ' + maxActions + '；最近轨迹：' + trace.slice(-12).join(' | '));
    const actor = state.players[state.currentPlayerIndex];
    const action: GameAction | null = actor.kind === 'computer'
      ? chooseComputerAction(state, {reserveCash}) : choosePhaseAction(state, humanReserveCash);
    if (!action) throw new Error('seed=' + seed + ' 无法处理阶段 ' + state.phase);
    const beforeRevision = state.revision;
    const result = applyAction(state, action);
    if (!result.ok) throw new Error('seed=' + seed + ' 第' + (actions+1) + '步 ' + action.type + ' 被拒绝：' + result.reason);
    state = result.state;
    if (state.revision !== beforeRevision + 1) throw new Error('seed=' + seed + ' 状态版本异常');
    if (!state.players.every(p => Number.isFinite(p.cash) && p.cash >= 0 && p.position >= 0 && p.position < state.tiles.length) ||
        !state.tiles.every(t => t.ownerId === null || state.players.some(p => p.id === t.ownerId))) throw new Error('seed=' + seed + ' 现金、位置或产权非法');
    actions++;
    trace.push(actions + ':' + actor.id + ':' + action.type + ':' + state.phase);
    if (action.type === 'roll') playerTurns++;
  }
  if (playerTurns > config.maxRounds * state.players.length) throw new Error('seed=' + seed + ' 回合上限被突破');
  const finished = [...state.events].reverse().find(e => e.type === 'game_finished');
  if (!finished) throw new Error('seed=' + seed + ' 没有终局事件');
  return { seed, finalState: state, playerTurns, actions, rejections: 0,
    finishReason: String(finished.details?.reason ?? 'unknown'), trace };
}
