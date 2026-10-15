/** 独立于页面的确定性回合与棋盘规则核心；地产经济将在 #4 实现。 */
export const SCHEMA_VERSION = 1 as const;
export type PlayerId = string;
export type TileKind = 'start' | 'property' | 'neutral';
export type Phase = 'setup' | 'await_roll' | 'await_decision' | 'await_end_turn' | 'finished';
export type PlayerKind = 'human' | 'computer';

export interface PlayerConfig { readonly id: PlayerId; readonly name: string; }
export interface TileConfig {
  readonly id: number;
  readonly kind: TileKind;
  readonly title: string;
  readonly price?: number;
  readonly rent?: number;
}
export interface GameConfig {
  readonly players: readonly [PlayerConfig, PlayerConfig];
  readonly tiles: readonly TileConfig[];
  readonly initialCash: number;
  readonly maxRounds: number;
}
export interface Player {
  readonly id: PlayerId;
  readonly name: string;
  readonly kind: PlayerKind;
  readonly position: number;
  readonly cash: number;
  readonly bankrupt: boolean;
}
export interface Tile extends TileConfig { readonly ownerId: PlayerId | null; }
export interface GameEvent {
  readonly type: 'game_started' | 'die_rolled' | 'player_moved' | 'turn_ended' | 'tile_landed' | 'property_declined' | 'game_finished';
  readonly actorId?: PlayerId;
  readonly details?: Readonly<Record<string, string | number>>;
}
export interface GameState {
  readonly schemaVersion: typeof SCHEMA_VERSION;
  readonly status: 'setup' | 'playing' | 'finished';
  readonly phase: Phase;
  readonly revision: number;
  readonly round: number;
  readonly currentPlayerIndex: number;
  readonly randomState: number;
  readonly maxRounds: number;
  readonly players: readonly Player[];
  readonly tiles: readonly Tile[];
  readonly winnerId: PlayerId | null;
  readonly events: readonly GameEvent[];
}
export type GameAction =
  | { readonly type: 'start_game'; readonly actorId: PlayerId }
  | { readonly type: 'roll'; readonly actorId: PlayerId }
  | { readonly type: 'buy_property'; readonly actorId: PlayerId }
  | { readonly type: 'decline_property'; readonly actorId: PlayerId }
  | { readonly type: 'end_turn'; readonly actorId: PlayerId };
export type RejectReason = 'INVALID_PHASE' | 'INVALID_ACTOR' | 'NOT_IMPLEMENTED';
export type ActionResult =
  | { readonly ok: true; readonly state: GameState; readonly events: readonly GameEvent[] }
  | { readonly ok: false; readonly state: GameState; readonly events: readonly []; readonly reason: RejectReason };

const defaultTiles: readonly TileConfig[] = Array.from({ length: 24 }, (_, index): TileConfig => {
  if (index === 0) return { id: index, kind: 'start', title: '起点' };
  if (index % 3 === 0) return { id: index, kind: 'neutral', title: `休息站 ${index}` };
  return { id: index, kind: 'property', title: `地产 ${index}`, price: 100 + index * 10, rent: 20 + index * 2 };
});

export const DEFAULT_CONFIG: GameConfig = {
  players: [{ id: 'p1', name: '玩家' }, { id: 'p2', name: '电脑' }],
  tiles: defaultTiles,
  initialCash: 1500,
  maxRounds: 60
};

/** 固定 32 位种子，避免 Math.random 导致的回放不一致。 */
export function normalizeSeed(seed: number): number {
  if (!Number.isFinite(seed)) throw new Error('随机种子必须是有限数字');
  return (Math.trunc(seed) >>> 0) || 0x6d2b79f5;
}

/** 返回新随机状态；绝不修改传入状态。 */
export function nextDie(randomState: number): { readonly value: number; readonly nextState: number } {
  let x = normalizeSeed(randomState);
  x ^= x << 13;
  x ^= x >>> 17;
  x ^= x << 5;
  const nextState = x >>> 0;
  return { value: 1 + (nextState % 6), nextState };
}

function validateConfig(config: GameConfig): void {
  if (config.players.length !== 2 || new Set(config.players.map(p => p.id)).size !== 2 ||
      config.players.some(p => !p.id.trim() || !p.name.trim())) throw new Error('玩家配置必须包含两名不同玩家');
  if (config.tiles.length < 2 || config.tiles[0]?.kind !== 'start' ||
      config.tiles.filter(t => t.kind === 'start').length !== 1 ||
      config.tiles.some((t, i) => t.id !== i || !t.title.trim())) throw new Error('地图配置无效');
  if (!Number.isFinite(config.initialCash) || config.initialCash < 0 ||
      !Number.isInteger(config.maxRounds) || config.maxRounds < 1) throw new Error('游戏经济配置无效');
  if (config.tiles.some(t => t.kind === 'property' &&
      (!Number.isFinite(t.price) || (t.price ?? 0) < 0 || !Number.isFinite(t.rent) || (t.rent ?? 0) < 0))) {
    throw new Error('地产价格或租金无效');
  }
}

/** 新建纯数据状态。每次调用都会创建隔离的玩家、棋盘数组。 */
export function createGame(seed: number, config: GameConfig = DEFAULT_CONFIG): GameState {
  validateConfig(config);
  return {
    schemaVersion: SCHEMA_VERSION,
    status: 'setup',
    phase: 'setup',
    revision: 0,
    round: 1,
    currentPlayerIndex: 0,
    randomState: normalizeSeed(seed),
    maxRounds: config.maxRounds,
    players: config.players.map((p, index): Player => ({
      id: p.id, name: p.name, kind: index === 0 ? 'human' : 'computer',
      position: 0, cash: config.initialCash, bankrupt: false
    })),
    tiles: config.tiles.map(t => ({ ...t, ownerId: null })),
    winnerId: null,
    events: []
  };
}

/** 单一命令入口：始终返回新状态或明确拒绝，不修改传入对象。 */
export function applyAction(state: GameState, action: GameAction): ActionResult {
  const actor = state.players[state.currentPlayerIndex];
  const reject = (reason: RejectReason): ActionResult => ({ ok: false, reason, state, events: [] });
  if (!actor || actor.id !== action.actorId) return reject('INVALID_ACTOR');
  if (action.type === 'start_game') {
    if (state.phase !== 'setup') return reject('INVALID_PHASE');
    return accept(state, [{ type: 'game_started', actorId: action.actorId }], {
      status: 'playing', phase: 'await_roll'
    });
  }
  if (state.phase === 'setup' || state.phase === 'finished') return reject('INVALID_PHASE');

  switch (action.type) {
    case 'roll': {
      if (state.phase !== 'await_roll') return reject('INVALID_PHASE');
      const { value, nextState } = nextDie(state.randomState);
      const position = (actor.position + value) % state.tiles.length;
      const landed = state.tiles[position];
      const events: GameEvent[] = [
        { type: 'die_rolled', actorId: actor.id, details: { value } },
        { type: 'player_moved', actorId: actor.id, details: { from: actor.position, to: position } },
        { type: 'tile_landed', actorId: actor.id, details: { tileId: landed.id, title: landed.title } }
      ];
      const phase: Phase = landed.kind === 'property' && landed.ownerId === null
        ? 'await_decision' : 'await_end_turn';
      return accept(state, events, {
        randomState: nextState,
        players: state.players.map(p => p.id === actor.id ? { ...p, position } : p),
        phase
      });
    }
    case 'decline_property': {
      if (state.phase !== 'await_decision') return reject('INVALID_PHASE');
      const tile = state.tiles[actor.position];
      if (tile.kind !== 'property' || tile.ownerId !== null) return reject('INVALID_PHASE');
      return accept(state, [{ type: 'property_declined', actorId: actor.id, details: { tileId: tile.id } }], {
        phase: 'await_end_turn'
      });
    }
    case 'end_turn': {
      if (state.phase !== 'await_end_turn') return reject('INVALID_PHASE');
      const lastPlayer = state.currentPlayerIndex === state.players.length - 1;
      const finished = lastPlayer && state.round >= state.maxRounds;
      const events: GameEvent[] = [{ type: 'turn_ended', actorId: actor.id }];
      if (finished) events.push({ type: 'game_finished', details: { reason: 'round_limit' } });
      return accept(state, events, {
        status: finished ? 'finished' : 'playing',
        phase: finished ? 'finished' : 'await_roll',
        currentPlayerIndex: (state.currentPlayerIndex + 1) % state.players.length,
        round: !finished && lastPlayer ? state.round + 1 : state.round,
        // #4 将在该边界计算净资产胜负；当前没有经济规则，只以平局终止测试局。
        winnerId: null
      });
    }
    case 'buy_property':
      return state.phase !== 'await_decision' ? reject('INVALID_PHASE') : reject('NOT_IMPLEMENTED');
  }
}

function accept(state: GameState, events: readonly GameEvent[], changes: Partial<GameState>): ActionResult {
  return {
    ok: true,
    events,
    state: { ...state, ...changes, revision: state.revision + 1, events: [...state.events, ...events] }
  };
}
