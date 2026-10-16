/** Stable public API; the implementation remains deterministic and React-independent. */
export { SCHEMA_VERSION, UPGRADE_RULES_VERSION } from './types.js';
export type { CardKind, PlayerId, TileKind, Phase, PlayerKind, PlayerConfig, TileConfig, GameMap, MapCell, GameConfig, Player, Tile, GameEvent, GameState, GameAction, RejectReason, ActionResult } from './types.js';
export { DEFAULT_CARD_RULES, DEFAULT_EVENT_RULES, DEFAULT_UPGRADES, DEFAULT_CONFIG, HARBOR_CONFIG } from './config.js';
export { normalizeSeed, nextDie } from './random.js';
export { DEFAULT_MAP, INTERNAL_TEST_MAP, HARBOR_MAP, inferMap, advancePosition, validateMap } from './maps.js';
export { makePropertyTile, netWorth } from './property.js';
import type { GameConfig, GameState, GameAction, ActionResult } from './types.js';
/** 新建纯数据状态。每次调用都会创建隔离的玩家、棋盘数组。 */
export declare function createGame(seed: number, config?: GameConfig): GameState;
/** 单一命令入口：始终返回新状态或明确拒绝，不修改传入对象。 */
export declare function applyAction(state: GameState, action: GameAction): ActionResult;
