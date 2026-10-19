export type WorldPoint = Readonly<{ x: number; z: number }>;
import { INTERNAL_TEST_MAP } from '../../core/maps.js';
import type { GameMap } from '../../core/types.js';

/** Shared scene heights keep board pieces grounded on the miniature terrain. */
export const GROUND_TOP = -0.29;
export const ROAD_TILE_THICKNESS = 0.06;
export const ROAD_TILE_TOP = GROUND_TOP + ROAD_TILE_THICKNESS;
export const ROAD_TILE_CENTER_Y = GROUND_TOP + ROAD_TILE_THICKNESS / 2;
export const ROAD_CONNECTOR_THICKNESS = 0.04;
export const ROAD_CONNECTOR_CENTER_Y = GROUND_TOP + ROAD_CONNECTOR_THICKNESS / 2;
export const ACTOR_ANCHOR_Y = ROAD_TILE_TOP - 0.1;
export const LOT_HALF_SIZE = 0.84;

export type MapAnchors = Readonly<{
  tiles: readonly WorldPoint[];
  lots: readonly WorldPoint[];
  edges: readonly (readonly [WorldPoint,WorldPoint])[];
  bounds: Readonly<{ width: number; depth: number }>;
}>;
const anchorsByMap = new WeakMap<GameMap, MapAnchors>();

type RoadEdge=readonly [WorldPoint,WorldPoint];
function roadAreaFree(point:WorldPoint,halfSize:number,tiles:readonly WorldPoint[],edges:readonly RoadEdge[]):boolean{
  return tiles.every(p=>Math.abs(p.x-point.x)>=.92+halfSize||Math.abs(p.z-point.z)>=.92+halfSize)&&edges.every(([a,b])=>
    Math.abs(point.x-(a.x+b.x)/2)>=Math.abs(a.x-b.x)/2+.36+halfSize||
    Math.abs(point.z-(a.z+b.z)/2)>=Math.abs(a.z-b.z)/2+.36+halfSize);
}

/** Layout is independent of rule/save coordinates. Crowded routes get wider streets. */
export function anchorsForMap(map: GameMap): MapAnchors {
  const cached=anchorsByMap.get(map);
  if(cached)return cached;
  for(const spacing of [2,4,6]){
    const tiles=map.cells.map(cell=>({x:(cell.column-(map.columns+1)/2)*spacing,z:(cell.row-(map.rows+1)/2)*spacing}));
    const edges:RoadEdge[]=map.route.map((id,i)=>[tiles[id],tiles[map.route[(i+1)%map.route.length]]]);
    const area=edges.reduce((sum,[a,b])=>sum+a.x*b.z-b.x*a.z,0);
    const candidates:WorldPoint[][]=Array.from({length:tiles.length},()=>[]);
    map.route.forEach((id,i)=>{
      const prev=tiles[map.route[(i+map.route.length-1)%map.route.length]],next=tiles[map.route[(i+1)%map.route.length]];
      const normal={x:(next.z-prev.z)*Math.sign(area),z:-(next.x-prev.x)*Math.sign(area)};
      for(let dx=-1;dx<=1;dx++)for(let dz=-1;dz<=1;dz++){
        if(dx===0&&dz===0)continue;
        const p={x:tiles[id].x+dx*2,z:tiles[id].z+dz*2};
        if(roadAreaFree(p,LOT_HALF_SIZE,tiles,edges))candidates[id].push(p);
      }
      const score=(p:WorldPoint)=>{
        const dx=p.x-tiles[id].x,dz=p.z-tiles[id].z;
        return (dx*normal.x+dz*normal.z)/Math.hypot(dx,dz)-Math.hypot(dx,dz)*.01;
      };
      candidates[id].sort((a,b)=>score(b)-score(a)||a.x-b.x||a.z-b.z);
    });
    // Matching permits crowded corners to displace a neighbour to a second
    // choice. If no local allocation exists, widen the layout rather than
    // moving a property away from its own road or altering saved topology.
    const owners=new Map<string,number>(),lots:WorldPoint[]=Array(tiles.length);
    function assign(id:number,seen:Set<string>):boolean{
      for(const p of candidates[id]){
        const key=`${p.x},${p.z}`;
        if(seen.has(key))continue;
        seen.add(key);
        const owner=owners.get(key);
        if(owner===undefined||assign(owner,seen)){owners.set(key,id);lots[id]=p;return true;}
      }
      return false;
    }
    if(!tiles.every((_,id)=>assign(id,new Set())))continue;
    const all=[...tiles,...lots];
    const result={tiles,lots,edges,bounds:{width:Math.max(...all.map(p=>Math.abs(p.x)))*2+3,depth:Math.max(...all.map(p=>Math.abs(p.z)))*2+3}};
    anchorsByMap.set(map,result);return result;
  }
  throw new Error('此路线无法分配不重叠的局部地产');
}

export const TILE_ANCHORS = anchorsForMap(INTERNAL_TEST_MAP).tiles;
export const LOT_ANCHORS = anchorsForMap(INTERNAL_TEST_MAP).lots;

export function positionForTile(tileId: number, map: GameMap = INTERNAL_TEST_MAP): WorldPoint {
  const point = anchorsForMap(map).tiles[tileId];
  if (point === undefined) throw new Error(`3D 场景不存在格子 ${tileId}`);
  return point;
}

export function lotForTile(tileId: number, map: GameMap = INTERNAL_TEST_MAP): WorldPoint {
  const point = anchorsForMap(map).lots[tileId];
  if (point === undefined) throw new Error(`3D 场景不存在地产 ${tileId}`);
  return point;
}

/** Every door faces its own road, including concave and interior streets. */
export function inwardAngleForTile(tileId: number, map: GameMap = INTERNAL_TEST_MAP): number {
  const { tiles, lots } = anchorsForMap(map);
  const point = tiles[tileId];
  if (point === undefined) throw new Error(`3D 场景不存在格子 ${tileId}`);
  return Math.atan2(point.x-lots[tileId].x,point.z-lots[tileId].z);
}

/** A shared exclusion rule for scenery and cross-lot geometry. */
export function isWorldSpaceFree(point:WorldPoint,halfSize:number,map:GameMap,includeLots=true):boolean{
  const {tiles,lots,edges}=anchorsForMap(map);
  return roadAreaFree(point,halfSize,tiles,edges)&&
    (!includeLots||lots.every(p=>Math.abs(p.x-point.x)>=LOT_HALF_SIZE+halfSize||Math.abs(p.z-point.z)>=LOT_HALF_SIZE+halfSize));
}

export function canJoinLots(a:number,b:number,map:GameMap):boolean{
  const {tiles,lots,edges}=anchorsForMap(map),p=lots[a],q=lots[b];
  if(Math.hypot(p.x-q.x,p.z-q.z)>2.01 || (p.x!==q.x&&p.z!==q.z))return false;
  const center={x:(p.x+q.x)/2,z:(p.z+q.z)/2};
  return roadAreaFree(center,.7,tiles,edges);
}

