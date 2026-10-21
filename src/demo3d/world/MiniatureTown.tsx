import { worldForMap } from '../../core/level-data.js';
import { useMemo, type MutableRefObject } from 'react';
import type { Navigation } from './world-navigation.js';
import type { GameState } from '../../core/game.js';
import { ResidentialBuildings } from './ResidentialBuildings.js';
import { StreetProperties } from './StreetProperties.js';
import { anchorsForMap, GROUND_TOP, inwardAngleForTile, ROAD_CONNECTOR_CENTER_Y, ROAD_CONNECTOR_THICKNESS, ROAD_TILE_CENTER_Y, ROAD_TILE_THICKNESS } from './layout.js';
import { RoadLabels } from './RoadLabels.js';
import { Instances, type Instance } from './Instances.js';
import type { WorldView } from './world-view.js';
import { MASCOT_SEAT_COLORS as PLAYER_COLORS } from './seats.js';
type TownProps = Readonly<{game:GameState;view:WorldView;nav:MutableRefObject<Navigation>;selectedTileId?:number|null;onSelectTile?:(tileId:number)=>void}>;

export function MiniatureTown({game,view,nav,selectedTileId,onSelectTile}:TownProps):React.JSX.Element {
  const anchors=anchorsForMap(game.map);
  const detail=view.zoom>=17||game.map.id==='classic-24';
  const ownerColor=(id:string)=>PLAYER_COLORS[game.players.findIndex(p=>p.id===id)]??'#f8c95d';
  const roads=useMemo(()=>anchors.tiles.map((p,id)=>({...p,y:ROAD_TILE_CENTER_Y,rotation:worldForMap(game.map)?.tiles[id].rotation??0,color:id===0?'#e7bd64':game.tiles[id].kind==='property'?'#e6dfc9':game.map.id==='classic-24'?'#b6cfe0':'#b6cfc3'})),[anchors,game.map]);
  const edges=useMemo(()=>game.map.route.map((id,i)=>{
    const a=anchors.tiles[id],b=anchors.tiles[game.map.route[(i+1)%game.map.route.length]];
    return {x:(a.x+b.x)/2,y:ROAD_CONNECTOR_CENTER_Y,z:(a.z+b.z)/2,sx:game.map.id==='classic-24'?1.82:1.2,sz:Math.hypot(a.x-b.x,a.z-b.z),rotation:Math.atan2(b.x-a.x,b.z-a.z)};
  }),[anchors,game.map]);
  const lots=game.tiles.map(tile=>({...anchors.lots[tile.id],tileId:tile.id,y:GROUND_TOP+.035,rotation:inwardAngleForTile(tile.id,game.map),color:tile.ownerId?ownerColor(tile.ownerId):tile.kind==='property'?'#c2ce9f':'#b8c59f'}));
  const simpleHouses=game.tiles.filter(t=>t.ownerId&&(t.level??0)>0&&!detail).map(t=>({...anchors.lots[t.id],tileId:t.id,y:GROUND_TOP+.5,sy:1+(t.level??1)*.3,color:ownerColor(t.ownerId!)}));
  const paving:Instance[]=detail?game.tiles.flatMap(t=>{
    const p=anchors.tiles[t.id],q=anchors.lots[t.id],angle=Math.atan2(q.x-p.x,q.z-p.z),d=Math.hypot(q.x-p.x,q.z-p.z);
    return [.35,.5,.65].map(k=>({x:p.x+(q.x-p.x)*k,y:GROUND_TOP+.018,z:p.z+(q.z-p.z)*k,sx:.36,sz:Math.min(.28,d*.1),rotation:angle,color:'#d4ccb3',tileId:t.id}));
  }):[];
  const selected=selectedTileId==null?[]:[lots[selectedTileId]].filter(Boolean);
  const borders=detail?roads.flatMap(p=>[-1,1].flatMap(side=>[-1,1].map(end=>({x:p.x+Math.cos(p.rotation)*side*.72+Math.sin(p.rotation)*end*.67,z:p.z-Math.sin(p.rotation)*side*.72+Math.cos(p.rotation)*end*.67,y:GROUND_TOP+.068,rotation:p.rotation,color:'#f6efda'})))):[];
  return <group name="路线与街区">
    <RoadLabels map={game.map} view={view} nav={nav}/>
    <Instances items={edges.map(e=>({...e,sx:e.sx+.18,y:GROUND_TOP+.012}))}><boxGeometry args={[1,.024,1]}/><meshStandardMaterial color="#b8b49c" roughness={1}/></Instances>
    <Instances items={edges}><boxGeometry args={[1,ROAD_CONNECTOR_THICKNESS,1]}/><meshStandardMaterial color="#d6cdb5" roughness={1}/></Instances>
    <Instances items={roads} onSelect={onSelectTile} mapTiles><boxGeometry args={[1.78,ROAD_TILE_THICKNESS,1.78]}/><meshStandardMaterial roughness={.94}/></Instances>
    <Instances items={borders}><boxGeometry args={[.12,.015,.24]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={paving}><boxGeometry args={[1,.035,1]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={lots.filter(t=>!detail||game.tiles[t.tileId].kind!=='property')} mapTiles><boxGeometry args={[1.18,.07,1.18]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={simpleHouses}><boxGeometry args={[.78,.8,.78]}/><meshStandardMaterial roughness={.9}/></Instances>
    {detail&&(game.map.id==='classic-24'?<StreetProperties game={game} view={view}/>:<ResidentialBuildings game={game} view={view}/>)}
    <Instances items={selected.flatMap(p=>[-1,1].map(side=>({...p,color:"#fff3a5",x:p.x+Math.cos(p.rotation)*side*.79,z:p.z-Math.sin(p.rotation)*side*.79,y:GROUND_TOP+.1})))}><boxGeometry args={[.055,.05,1.62]}/><meshStandardMaterial color="#fff3a5" emissive="#ffe185" emissiveIntensity={.3}/></Instances>
    <Instances items={selected.flatMap(p=>[-1,1].map(side=>({...p,color:"#fff3a5",x:p.x+Math.sin(p.rotation)*side*.79,z:p.z+Math.cos(p.rotation)*side*.79,y:GROUND_TOP+.1})))}><boxGeometry args={[1.62,.05,.055]}/><meshStandardMaterial color="#fff3a5" emissive="#ffe185" emissiveIntensity={.3}/></Instances>
  </group>;
}
