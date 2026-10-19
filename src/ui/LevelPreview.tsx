import type { GameMap } from '../core/types.js';
import { worldForMap } from '../core/level-data.js';
import type { WorldDefinition } from '../core/level-world.js';

/** Shared cartography: previews and navigation consume the actual authored contours. */
export function WorldMapShapes({world}:{world:WorldDefinition|undefined}):React.JSX.Element{
  return <g aria-hidden="true">{world?.surfaces.map(s=><path key={s.id} d={[s.points,...s.holes].map(r=>r.map((p,i)=>`${i?'L':'M'}${p.x},${p.z}`).join(' ')+'Z').join(' ')} fill={s.color} fillRule="evenodd"/>)}
    {world?.objects.filter(o=>o.kind==='tree'||o.kind==='pine').map(o=><circle key={o.id} cx={o.x} cy={o.z} r={o.scale*.7} fill={o.color}/>)}
  </g>;
}
export function LevelPreview({map}:{map:GameMap}):React.JSX.Element{
  const world=worldForMap(map);
  const tiles=world?.tiles??map.cells.map(p=>({x:p.column,z:p.row}));
  const all=[...tiles,...(world?.surfaces.flatMap(s=>s.points)??[])];
  const minX=Math.min(...all.map(p=>p.x))-3,minZ=Math.min(...all.map(p=>p.z))-3;
  const width=Math.max(...all.map(p=>p.x))-minX+3,depth=Math.max(...all.map(p=>p.z))-minZ+3;
  return <svg className="map-route-preview" viewBox={`${minX} ${minZ} ${width} ${depth}`} aria-hidden="true">
    <rect x={minX} y={minZ} width={width} height={depth} fill={world?.base.color??'#b7cd9a'}/>
    <WorldMapShapes world={world}/>
    <polyline points={[...map.route,map.route[0]].map(id=>`${tiles[id].x},${tiles[id].z}`).join(' ')} fill="none" stroke="#fff6dd" strokeWidth="3" vectorEffect="non-scaling-stroke" strokeLinejoin="round"/>
    <circle cx={tiles[0].x} cy={tiles[0].z} r={Math.max(width,depth)*.025} fill="#dc9355"/>
  </svg>;
}
