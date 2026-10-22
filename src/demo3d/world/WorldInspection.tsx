import { useLayoutEffect,useRef,useState } from 'react';
import type {GameState} from '../../core/types.js';
import {propertyBlock,propertyRent,propertyRun} from '../../core/property-groups.js';
import type {InspectionRequest} from './map-picking.js';

export function WorldInspection({game,request}:{game:GameState;request:InspectionRequest}):React.JSX.Element {
  const ref=useRef<HTMLDivElement>(null),[point,setPoint]=useState({x:request.x+16,y:request.y+16});
  useLayoutEffect(()=>{const box=ref.current!.getBoundingClientRect();setPoint({x:Math.max(12,Math.min(request.x+16,innerWidth-box.width-12)),y:Math.max(12,request.y+box.height+28>innerHeight?request.y-box.height-16:request.y+16)});},[request]);
  const tile=request.kind==='tile'?game.tiles[request.tileId]:null;
  const player=request.kind==='player'?game.players.find(p=>p.id===request.playerId):null;
  return <div ref={ref} role="tooltip" className="world-inspection" style={{left:point.x,top:point.y}}>
    {tile?<><strong>{tile.id+1} · {tile.title}</strong>{tile.kind==='property'?<>
      <span>{tile.ownerId?`${game.players.find(p=>p.id===tile.ownerId)?.name}所有`:'待售土地'} · {['土地','住宅','高级住宅'][tile.level??0]}</span>
      <span>地价 {tile.price?.toLocaleString('zh-CN')} · {tile.mortgaged?'抵押中，暂停收租':`通行费 ${tile.ownerId?propertyRent(game,tile.id):tile.rent}`}</span>
      {propertyBlock(game,tile.id)&&<span>{propertyBlock(game,tile.id)!.title} · {game.terraceRulesVersion===1?(tile.ownerId?`${propertyRun(game,tile.id).length} 块连地`:'相邻同主土地可联排'):'旧版单地块规则'}</span>}
    </>:<span>公共地块 · {tile.facility==='hospital'?'医院':tile.facility==='prison'?'监狱':tile.facility==='shop'?'道具商店':tile.kind==='start'?'起点':'机会站点'}</span>}</>:player&&<>
      <strong>{player.name} · {player.kind==='computer'?'电脑':'真人'}</strong>
      <span>现金 {player.cash.toLocaleString('zh-CN')} · 存款 {(player.bankBalance??0).toLocaleString('zh-CN')}</span>
      <span>地产 {game.tiles.filter(t=>t.ownerId===player.id).length} 块 · 贷款 {(player.loanBalance??0).toLocaleString('zh-CN')}</span>
      <span>{player.bankrupt?'已破产':player.detention?`${player.detention.kind==='hospital'?'住院':'监禁'}，剩余 ${player.detention.remaining} 回合`:`位于 ${player.position+1} 号格 · ${game.tiles[player.position].title}`}</span>
    </>}
    <small>松开即收起</small>
  </div>;
}
