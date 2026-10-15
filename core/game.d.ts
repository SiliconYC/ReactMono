/** 独立于页面的确定性回合与棋盘规则核心；第 #4 期加入地产买卖、收租、破产与胜负规则。 */
export declare const SCHEMA_VERSION: 1;
export type PlayerId = string;
export type TileKind = 'start' | 'property' | 'neutral';
export type Phase = 'setup' | 'await_roll' | 'await_decision' | 'await_end_turn' | 'finished';
export type PlayerKind = 'human' | 'computer';
export interface PlayerConfig {
    readonly id: PlayerId;
    readonly name: string;
}
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
export interface Tile extends TileConfig {
    readonly ownerId: PlayerId | null;
}
export interface GameEvent {
    readonly type: 'game_started' | 'die_rolled' | 'player_moved' | 'turn_ended' | 'tile_landed' | 'property_declined' | 'property_bought' | 'rent_paid' | 'player_bankrupt' | 'game_finished';
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
export type GameAction = {
    readonly type: 'start_game';
    readonly actorId: PlayerId;
} | {
    readonly type: 'roll';
    readonly actorId: PlayerId;
} | {
    readonly type: 'buy_property';
    readonly actorId: PlayerId;
} | {
    readonly type: 'decline_property';
    readonly actorId: PlayerId;
} | {
    readonly type: 'end_turn';
    readonly actorId: PlayerId;
};
export type RejectReason = 'INVALID_PHASE' | 'INVALID_ACTOR' | 'INSUFFICIENT_FUNDS';
export type ActionResult = {
    readonly ok: true;
    readonly state: GameState;
    readonly events: readonly GameEvent[];
} | {
    readonly ok: false;
    readonly state: GameState;
    readonly events: readonly [];
    readonly reason: RejectReason;
};
export declare const DEFAULT_CONFIG: GameConfig;
/** 固定 32 位种子，避免 Math.random 导致的回放不一致。 */
export declare function normalizeSeed(seed: number): number;
/** 返回新随机状态；绝不修改传入状态。 */
export declare function nextDie(randomState: number): {
    readonly value: number;
    readonly nextState: number;
};
/** 新建纯数据状态。每次调用都会创建隔离的玩家、棋盘数组。 */
export declare function createGame(seed: number, config?: GameConfig): GameState;
/** 按当前现金与未折旧购地价格计算净资产；仅用于回合上限时公平判定。 */
export declare function netWorth(state: GameState, playerId: PlayerId): number;
/** 单一命令入口：始终返回新状态或明确拒绝，不修改传入对象。 */
export declare function applyAction(state: GameState, action: GameAction): ActionResult;
