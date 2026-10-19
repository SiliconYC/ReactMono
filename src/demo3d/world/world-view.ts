import { type WorldPoint } from './layout.js';

export const CAMERA_ELEVATION = Math.atan2(12.2, Math.hypot(10.2,10.2));
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
/** Bounds are geometry-only: the author's base fill extends across the view; no content is created. */
export function groundBounds(v:WorldView,points:readonly WorldPoint[]){
  const bounds={minX:v.minX-16,maxX:v.maxX+16,minZ:v.minZ-16,maxZ:v.maxZ+16};
  for(const p of points){bounds.minX=Math.min(bounds.minX,p.x-1);bounds.maxX=Math.max(bounds.maxX,p.x+1);bounds.minZ=Math.min(bounds.minZ,p.z-1);bounds.maxZ=Math.max(bounds.maxZ,p.z+1);}
  return bounds;
}
export function clampWorldZoom(zoom:number,overview:number):number{
  return Math.max(Math.min(overview,96),Math.min(96,zoom));
}
export function panWorld(center:WorldPoint,dx:number,dy:number,zoom:number):WorldPoint{
  return {x:center.x+(-dx-dy/Math.sin(CAMERA_ELEVATION))/Math.SQRT2/zoom,z:center.z+(dx-dy/Math.sin(CAMERA_ELEVATION))/Math.SQRT2/zoom};
}
