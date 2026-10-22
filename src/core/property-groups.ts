import type { GameState, Tile } from './types.js';

export const LIME_PROPERTY_BLOCKS = [
  { id:'citrus', title:'柚香里', tileIds:[1,2,3] },
  { id:'peach', title:'蜜桃里', tileIds:[5,6,7] },
  { id:'herb', title:'香草里', tileIds:[9,10,11] },
  { id:'ginkgo', title:'银杏里', tileIds:[13,14,15] },
  { id:'lily', title:'铃兰里', tileIds:[17,18,19] },
  { id:'berry', title:'青梅里', tileIds:[21,22,23] },
  { id:'cloud', title:'流云里', tileIds:[25,26,27] },
  { id:'spring', title:'春日角', tileIds:[29] }
] as const;

export function propertyBlock(state: Pick<GameState,'map'>, tileId:number) {
  return state.map.id==='lime-garden-30'
    ? LIME_PROPERTY_BLOCKS.find(block=>(block.tileIds as readonly number[]).includes(tileId)) : undefined;
}

export function propertyRun(state:GameState,tileId:number):readonly Tile[] {
  const tile=state.tiles[tileId];
  if(!tile||tile.kind!=='property'||!tile.ownerId||tile.mortgaged)return [];
  const block=state.terraceRulesVersion===1?propertyBlock(state,tileId):undefined;
  if(!block)return [tile];
  const ids:readonly number[]=block.tileIds;
  const eligible=(id:number)=>state.tiles[id]?.kind==='property'&&state.tiles[id].ownerId===tile.ownerId&&!state.tiles[id].mortgaged;
  let first=ids.indexOf(tileId),last=first;
  while(first>0&&eligible(ids[first-1]))first--;
  while(last<ids.length-1&&eligible(ids[last+1]))last++;
  return ids.slice(first,last+1).map(id=>state.tiles[id]);
}

function tileRent(tile:Tile):number {
  return tile.mortgaged?0:(tile.level??0)===0?(tile.rent??0):(tile.levelRents?.[tile.level??0]??0);
}

export function propertyRent(state:GameState,tileId:number):number {
  return propertyRun(state,tileId).reduce((sum,tile)=>sum+tileRent(tile),0);
}

export function quotePropertyUpgrade(state:GameState,tileId:number) {
  const run=propertyRun(state,tileId);
  if(!run.length)return null;
  // 后买空地先补层，不能让先建的满级住宅阻断整排建设，也不能免费追平等级。
  const level=Math.min(...run.map(tile=>tile.level??0));
  if(level>=2)return null;
  const upgrades=run.filter(tile=>(tile.level??0)===level);
  if(upgrades.some(tile=>tile.upgradeCosts?.[level]===undefined))return null;
  const cost=upgrades.reduce((sum,tile)=>sum+tile.upgradeCosts![level],0);
  const rentBefore=run.reduce((sum,tile)=>sum+tileRent(tile),0);
  const rentAfter=rentBefore+upgrades.reduce((sum,tile)=>sum+(tile.levelRents?.[level+1]??0)-tileRent(tile),0);
  return {tileIds:run.map(tile=>tile.id),upgrades,cost,level:level+1,rentBefore,rentAfter};
}
