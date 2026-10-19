import type { GameMap } from '../../core/types.js';
import { isWorldSpaceFree, type WorldPoint } from './layout.js';

export const CAMERA_ELEVATION = Math.atan2(12.2, Math.hypot(10.2,10.2));
export const CHUNK_SIZE = 16;
export type WorldView = ReturnType<typeof worldView>;
export function worldView(center:WorldPoint,zoom:number,viewport:{width:number;height:number}) {
  const halfWidth=viewport.width/(2*zoom), halfHeight=viewport.height/(2*zoom);
  const halfExtent=(halfWidth+halfHeight/Math.sin(CAMERA_ELEVATION))/Math.SQRT2+4;
  const depthReach=halfHeight/Math.tan(CAMERA_ELEVATION)+4;
  const distance=Math.max(28,depthReach+18);
  return {
    center,zoom,halfExtent,depthReach,distance,
    minX:center.x-halfExtent,maxX:center.x+halfExtent,
    minZ:center.z-halfExtent,maxZ:center.z+halfExtent,
    far:distance+depthReach+40,
    fogNear:distance+depthReach+8,fogFar:distance+depthReach+80,
    shadowRadius:halfExtent+5
  };
}
export type GroundChunk=Readonly<{x:number;z:number}>;
export function groundChunks(v:WorldView):GroundChunk[]{
  const chunks:GroundChunk[]=[];
  for(let x=Math.floor(v.minX/CHUNK_SIZE);x<=Math.floor(v.maxX/CHUNK_SIZE);x++)
    for(let z=Math.floor(v.minZ/CHUNK_SIZE);z<=Math.floor(v.maxZ/CHUNK_SIZE);z++)
      chunks.push({x:(x+.5)*CHUNK_SIZE,z:(z+.5)*CHUNK_SIZE});
  return chunks;
}
/** Coordinate hash: independent of the game's PRNG and of chunk traversal order. */
function noise(x:number,z:number,salt:number):number{
  let n=Math.imul(x^salt,374761393)^Math.imul(z,668265263);
  n=Math.imul(n^(n>>>13),1274126177);
  return ((n^(n>>>16))>>>0)/4294967296;
}
export type Scenery=WorldPoint&Readonly<{scale:number;tone:number}>;
export function sceneryForChunks(chunks:readonly GroundChunk[],map:GameMap):Scenery[]{
  const result:Scenery[]=[];
  for(const chunk of chunks){
    const cx=Math.floor(chunk.x/16),cz=Math.floor(chunk.z/16);
    // Low contrast groves leave open meadow between neighbourhoods.
    if(noise(cx,cz,71)>.6)continue;
    for(let i=0;i<7;i++){
      const x=chunk.x+(noise(cx,cz,100+i*3)-.5)*13;
      const z=chunk.z+(noise(cx,cz,101+i*3)-.5)*13;
      const p={x,z,scale:.55+noise(cx,cz,102+i*3)*.5,tone:noise(cx,cz,200+i)};
      if(isWorldSpaceFree(p,.65,map)&&(!isWorldSpaceFree({x:0,z:0},2.7,map)||Math.hypot(x,z)>3.7))result.push(p);
    }
  }
  return result;
}
export function clampWorldZoom(zoom:number,overview:number):number{
  return Math.max(Math.min(overview,96),Math.min(96,zoom));
}
export function panWorld(center:WorldPoint,dx:number,dy:number,zoom:number):WorldPoint{
  return {x:center.x+(-dx-dy/Math.sin(CAMERA_ELEVATION))/Math.SQRT2/zoom,z:center.z+(dx-dy/Math.sin(CAMERA_ELEVATION))/Math.SQRT2/zoom};
}
