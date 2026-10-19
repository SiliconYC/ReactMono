import { type WorldPoint } from './layout.js';

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
    shadowRadius:halfExtent*Math.SQRT2+5
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
export function clampWorldZoom(zoom:number,overview:number):number{
  return Math.max(Math.min(overview,96),Math.min(96,zoom));
}
export function panWorld(center:WorldPoint,dx:number,dy:number,zoom:number):WorldPoint{
  return {x:center.x+(-dx-dy/Math.sin(CAMERA_ELEVATION))/Math.SQRT2/zoom,z:center.z+(dx-dy/Math.sin(CAMERA_ELEVATION))/Math.SQRT2/zoom};
}
