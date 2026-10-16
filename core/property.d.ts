/** P3-01: pure property creation and net worth valuation. */
import type { TileConfig, Tile, GameConfig, GameState, PlayerId, Player, GameAction, ActionResult, GameEvent, ResaleRules } from './types.js';
export declare function makePropertyTile(t: TileConfig, upgrades?: GameConfig['upgrades']): Tile;
/** 净资产按购地原价与已付升级费用计价，不计未实现收益。 */
export declare function netWorth(state: GameState, playerId: PlayerId): number;
/** Transparent resale: 75% of land cost plus 50% of paid upgrade costs. */
export declare function resaleValue(tile: Tile, rules?: ResaleRules): number;
/** Force sale only when rent cannot otherwise be paid, by ascending tile ID. */
export declare function liquidateForRent(state: GameState, actor: Player, due: number, creditorId: PlayerId): {
    cash: number;
    tiles: readonly Tile[];
    events: readonly GameEvent[];
};
export declare function sellProperty(state: GameState, actor: Player, action: Extract<GameAction, {
    type: 'sell_property';
}>): ActionResult;
/** Property decisions, purchases and upgrades remain pure commands. */
export declare function declineProperty(state: GameState, actor: Player): ActionResult;
export declare function upgradeProperty(state: GameState, actor: Player, action: Extract<GameAction, {
    type: 'upgrade_property';
}>): ActionResult;
export declare function buyProperty(state: GameState, actor: Player): ActionResult;
