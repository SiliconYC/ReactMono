import { useMemo } from 'react';
import type { GameState } from '../../core/game.js';
import { rowHouses } from '../properties.js';
import { MASCOT_SEAT_COLORS } from './seats.js';
import { Instances } from './Instances.js';
import { anchorsForMap, canJoinLots, GROUND_TOP, inwardAngleForTile } from './layout.js';
import type { WorldView } from './world-view.js';
import { residentialParts, GABLE_ROOF_VERTICES, TOWN, type TownPart } from './town-kit.js';

export function ResidentialBuildings({game,view}:{game:GameState;view:WorldView}):React.JSX.Element {
  const parts=useMemo(()=>{
    const all:TownPart[]=[],anchors=anchorsForMap(game.map);
    const visible=(id:number)=>{const p=anchors.lots[id];return p.x>=view.minX&&p.x<=view.maxX&&p.z>=view.minZ&&p.z<=view.maxZ;};
    for(const tile of game.tiles) {
      if(tile.kind!=='property'||!visible(tile.id))continue;
      const seat=game.players.findIndex(p=>p.id===tile.ownerId),owner=seat<0?null:MASCOT_SEAT_COLORS[seat];
      const lot=anchors.lots[tile.id],rotation=inwardAngleForTile(tile.id,game.map),c=Math.cos(rotation),s=Math.sin(rotation);
      all.push(...residentialParts(tile,owner,Math.max(0,seat)).map(p=>({...p,x:lot.x+c*p.x+s*p.z,z:lot.z-s*p.x+c*p.z,y:GROUND_TOP+p.y,rotation})));
    }
    for(const row of rowHouses(game))for(let i=1;i<row.tileIds.length;i++) {
      const aId=row.tileIds[i-1],id=row.tileIds[i];
      if(!visible(id)||!canJoinLots(aId,id,game.map))continue;
      const a=anchors.lots[aId],b=anchors.lots[id],length=Math.hypot(b.x-a.x,b.z-a.z)-.75;
      const rotation=Math.atan2(b.x-a.x,b.z-a.z),c=Math.cos(rotation),s=Math.sin(rotation);
      const add=(x:number,y:number,z:number,sx:number,sy:number,sz:number,color:string)=>all.push({shape:'box',x:(a.x+b.x)/2+c*x+s*z,z:(a.z+b.z)/2-s*x+c*z,y:GROUND_TOP+y,sx,sy,sz,rotation,color,tileId:id});
      add(0,.04,0,.76,.08,length,TOWN.stone);
      add(0,.45,0,.54,.75,length,TOWN.wall);
      add(0,.86,0,.76,.1,length+.08,TOWN.greenRoof);
      const bays=Math.max(1,Math.floor(length/.48));
      for(let j=0;j<bays;j++)for(const side of [-1,1]) {
        const z=(j+.5)*length/bays-length/2;
        add(side*.282,.48,z,.026,.42,length/bays-.12,TOWN.glass);
        add(side*.304,.48,z,.035,.44,.032,TOWN.trim);
      }
    }
    return all;
  },[game,view]);
  const roofs=useMemo(()=>new Float32Array(GABLE_ROOF_VERTICES),[]);
  return <group name="暖墙彩顶住宅与联廊">
    <Instances items={parts.filter(p=>p.shape==='box')}><boxGeometry/><meshStandardMaterial roughness={.88}/></Instances>
    <Instances items={parts.filter(p=>p.shape==='roof')}><bufferGeometry onUpdate={g=>g.computeVertexNormals()}><bufferAttribute attach="attributes-position" args={[roofs,3]}/></bufferGeometry><meshStandardMaterial roughness={.9}/></Instances>
    <Instances items={parts.filter(p=>p.shape==='leaf')}><dodecahedronGeometry args={[.5,0]}/><meshStandardMaterial roughness={1}/></Instances>
  </group>;
}
