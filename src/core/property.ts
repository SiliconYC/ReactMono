/** P3-01: pure property creation and net worth valuation. */
import type { TileConfig, Tile, GameConfig, GameState, PlayerId } from './types.js';
import { DEFAULT_UPGRADES } from './config.js';
export function makePropertyTile(t: TileConfig, upgrades: GameConfig['upgrades']=DEFAULT_UPGRADES): Tile {
  if(t.kind!=='property')throw new Error('只能升级地产');
  const up=upgrades??DEFAULT_UPGRADES;
  return {...t, ownerId:null,level:0,
    upgradeCosts:up.costRates.map(r=>Math.round((t.price??0)*r)) as unknown as [number,number],
    levelRents:up.rentRates.map(r=>Math.round((t.rent??0)*r)) as unknown as [number,number,number]};
}

/** 净资产按购地原价与已付升级费用计价，不计未实现收益。 */
export function netWorth(state: GameState, playerId: PlayerId): number {
  const player = state.players.find(p => p.id === playerId);
  if (!player) throw new Error('玩家不存在');
  return player.cash + state.tiles.reduce((sum, tile) =>
    sum + (tile.ownerId === playerId && tile.kind === 'property'
      ? (tile.price??0)+(tile.upgradeCosts??[]).slice(0,tile.level??0).reduce((a,b)=>a+b,0) : 0), 0);
}

