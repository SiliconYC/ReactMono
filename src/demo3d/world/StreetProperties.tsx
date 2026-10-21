import { useMemo } from 'react';
import type { GameState } from '../../core/game.js';
import { rowHouses } from '../properties.js';
import { MASCOT_SEAT_COLORS } from './seats.js';
import { anchorsForMap, canJoinLots, GROUND_TOP, inwardAngleForTile } from './layout.js';
import type { WorldView } from './world-view.js';
import { UrbanParts } from './UrbanScenery.js';
import { UrbanModel, type UrbanPart } from './urban-kit.js';
import { streetPropertyParts } from './street-property-kit.js';

export function StreetProperties({game,view}:{game:GameState;view:WorldView}):React.JSX.Element {
  const parts=useMemo(()=>{
    const result:UrbanPart[]=[],anchors=anchorsForMap(game.map);
    const visible=(id:number)=>{const p=anchors.lots[id];return p.x>=view.minX&&p.x<=view.maxX&&p.z>=view.minZ&&p.z<=view.maxZ;};
    const place=(parts:readonly UrbanPart[],x:number,z:number,rotation:number,tileId:number)=>{
      const c=Math.cos(rotation),s=Math.sin(rotation);
      result.push(...parts.map(p=>({...p,tileId,x:x+c*p.x+s*p.z,z:z-s*p.x+c*p.z,y:GROUND_TOP+p.y,rotation:rotation+(p.rotation??0)})));
    };
    for(const tile of game.tiles){
      if(tile.kind!=='property'||!visible(tile.id))continue;
      const seat=game.players.findIndex(p=>p.id===tile.ownerId),owner=seat<0?null:MASCOT_SEAT_COLORS[seat],p=anchors.lots[tile.id];
      place(streetPropertyParts(tile,owner,Math.max(0,seat)),p.x,p.z,inwardAngleForTile(tile.id,game.map),tile.id);
    }
    for(const row of rowHouses(game))for(let i=1;i<row.tileIds.length;i++){
      const aId=row.tileIds[i-1],id=row.tileIds[i];if(!visible(id)||!canJoinLots(aId,id,game.map))continue;
      const a=anchors.lots[aId],b=anchors.lots[id],distance=Math.hypot(b.x-a.x,b.z-a.z),length=distance-1.3;
      const m=new UrbanModel(),count=Math.max(1,Math.round(length/.75));
      m.box(0,.025,0,.78,.05,length,'#c6c4b4');
      for(let j=0;j<count;j++){
        const z=(j+.5)*length/count-length/2,w=length/count;
        m.box(0,.59,z,.83,1.12,w-.025,j%2?'#d6c5aa':'#d6b8a0');
        m.box(0,1.18,z,.98,.08,w+.02,'#eee7d2');
        m.add('roof',0,1.4,z,1.05,.37,w+.08,j%2?'#7f9692':'#ba7b62');
        for(const side of [-1,1]){
          m.box(side*.432,.69,z,.035,.56,w*.58,'#eee7d2');m.box(side*.46,.69,z,.025,.45,w*.43,'#486f77');
          m.box(side*.48,.69,z,.025,.45,.025,'#eee7d2');m.box(side*.48,.37,z,.09,.055,w*.7,'#eee7d2');
        }
      }
      const seat=game.players.findIndex(p=>p.id===row.ownerId);m.box(0,.1,0,.85,.05,length,MASCOT_SEAT_COLORS[seat]);
      place(m.parts,(a.x+b.x)/2,(a.z+b.z)/2,Math.atan2(b.x-a.x,b.z-a.z),id);
    }
    return result;
  },[game,view]);
  return <UrbanParts parts={parts}/>;
}
