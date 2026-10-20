import { DEFAULT_YAW, DEFAULT_ELEVATION, screenToGround } from './camera-math.js';
import { type WorldPoint } from './layout.js';

export const CAMERA_ELEVATION = DEFAULT_ELEVATION;
export type WorldView = ReturnType<typeof worldView>;
export function worldView(center:WorldPoint,zoom:number,viewport:{width:number;height:number},yaw=DEFAULT_YAW,elevation=DEFAULT_ELEVATION) {
  const halfWidth=viewport.width/(2*zoom), halfHeight=viewport.height/(2*zoom);
  const extentX=Math.abs(Math.cos(yaw))*halfWidth+Math.abs(Math.sin(yaw))*halfHeight/Math.sin(elevation)+4;
  const extentZ=Math.abs(Math.sin(yaw))*halfWidth+Math.abs(Math.cos(yaw))*halfHeight/Math.sin(elevation)+4;
  const halfExtent=Math.max(extentX,extentZ);
  const depthReach=halfHeight/Math.tan(elevation)+4;
  const distance=Math.max(28,depthReach+18);
  return {
    center,zoom,halfExtent,depthReach,distance,
    minX:center.x-extentX,maxX:center.x+extentX,
    minZ:center.z-extentZ,maxZ:center.z+extentZ,
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
export function panWorld(center:WorldPoint,dx:number,dy:number,zoom:number,yaw=DEFAULT_YAW,elevation=DEFAULT_ELEVATION):WorldPoint{
  const delta=screenToGround({x:-dx/zoom,y:-dy/zoom},yaw,elevation);
  return {x:center.x+delta.x,z:center.z+delta.z};
}
