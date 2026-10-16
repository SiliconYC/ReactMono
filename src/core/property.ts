/** P3-01: pure property creation and net worth valuation. */
import type { TileConfig, Tile, GameConfig, GameState, PlayerId, Player, GameAction, ActionResult, GameEvent } from './types.js';
import { DEFAULT_UPGRADES } from './config.js';
import { accept, reject } from './transitions.js';
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



/** Transparent resale: 75% of land cost plus 50% of paid upgrade costs. */
export function resaleValue(tile:Tile):number {
  if(tile.kind!=='property')throw new Error('非地产不能出售');
  const paid=(tile.upgradeCosts??[]).slice(0,tile.level??0).reduce((sum,cost)=>sum+cost,0);
  return Math.floor((tile.price??0)*0.75)+Math.floor(paid*0.5);
}
/** Force sale only when rent cannot otherwise be paid, by ascending tile ID. */
export function liquidateForRent(state:GameState,actor:Player,due:number):{
  cash:number;tiles:readonly Tile[];events:readonly GameEvent[]
}{
  let cash=actor.cash;
  let tiles=state.tiles;
  const events:GameEvent[]=[];
  for(const t of state.tiles){
    if(cash>=due)break;
    if(t.kind!=='property'||t.ownerId!==actor.id)continue;
    const amount=resaleValue(t);
    cash+=amount;
    tiles=tiles.map(x=>x.id===t.id?{...x,ownerId:null,level:0}:x);
    events.push({type:'property_liquidated',actorId:actor.id,details:{
      tileId:t.id,amount,creditorId:'bank',reason:'rent'
    }});
  }
  return {cash,tiles,events};
}
export function sellProperty(state:GameState,actor:Player,action:Extract<GameAction,{type:'sell_property'}>):ActionResult{
  if(state.phase!=='await_end_turn'||!Number.isInteger(action.tileId))return reject(state,'INVALID_PHASE');
  const tile=state.tiles[action.tileId];
  if(!tile||tile.kind!=='property'||tile.ownerId!==actor.id)return reject(state,'INVALID_PHASE');
  const amount=resaleValue(tile);
  if(!Number.isSafeInteger(amount)||!Number.isSafeInteger(actor.cash+amount))return reject(state,'INVALID_PHASE');
  return accept(state,[{type:'property_sold',actorId:actor.id,details:{tileId:tile.id,amount}}],{
    tiles:state.tiles.map(t=>t.id===tile.id?{...t,ownerId:null,level:0}:t),
    players:state.players.map(p=>p.id===actor.id?{...p,cash:p.cash+amount}:p)
  });
}

/** Property decisions, purchases and upgrades remain pure commands. */
export function declineProperty(state: GameState, actor: Player): ActionResult {
      if (state.phase !== 'await_decision') return reject(state,'INVALID_PHASE');
      const tile = state.tiles[actor.position];
      if (tile.kind !== 'property' || tile.ownerId !== null) return reject(state,'INVALID_PHASE');
      return accept(state, [{ type: 'property_declined', actorId: actor.id, details: { tileId: tile.id } }], {
        phase: 'await_end_turn'
      });
}
export function upgradeProperty(state: GameState, actor: Player, action: Extract<GameAction,{type:'upgrade_property'}>): ActionResult {
      if (state.phase !== 'await_end_turn' || !Number.isInteger(action.tileId))return reject(state,'INVALID_PHASE');
      const tile=state.tiles[action.tileId];
      if (!tile || tile.kind!=='property' || tile.ownerId!==actor.id || (tile.level??0)>=2)return reject(state,'INVALID_PHASE');
      const level=tile.level??0;
      const cost=tile.upgradeCosts?.[level];
      if(cost===undefined)return reject(state,'INVALID_PHASE');
      if(actor.cash<cost)return reject(state,'INSUFFICIENT_FUNDS');
      return accept(state,[{type:'property_upgraded',actorId:actor.id,details:{tileId:tile.id,level:level+1,amount:cost}}],{
        tiles:state.tiles.map(t=>t.id===tile.id?{...t,level:level+1}:t),
        players:state.players.map(p=>p.id===actor.id?{...p,cash:p.cash-cost}:p)
      });
}
export function buyProperty(state: GameState, actor: Player): ActionResult {
      if (state.phase !== 'await_decision') return reject(state,'INVALID_PHASE');
      const tile = state.tiles[actor.position];
      if (tile.kind !== 'property' || tile.ownerId !== null) return reject(state,'INVALID_PHASE');
      const price = tile.price ?? 0;
      if (actor.cash < price) return reject(state,'INSUFFICIENT_FUNDS');
      return accept(state, [{ type: 'property_bought', actorId: actor.id, details: {
        tileId: tile.id, amount: price, ownerId: actor.id
      } }], {
        players: state.players.map(p => p.id === actor.id ? { ...p, cash: p.cash - price } : p),
        tiles: state.tiles.map(t => t.id === tile.id ? { ...t, ownerId: actor.id } : t),
        phase: 'await_end_turn'
      });
}
