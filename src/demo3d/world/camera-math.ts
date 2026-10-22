import { worldForMap } from '../../core/level-data.js';
import type { GameMap } from '../../core/types.js';
import { anchorsForMap, type WorldPoint } from './layout.js';

export const DEFAULT_YAW=Math.PI/4;
export const DEFAULT_ELEVATION=Math.atan2(12.2,Math.hypot(10.2,10.2));
export const MIN_ELEVATION=Math.PI*12/180;
export const MAX_ELEVATION=Math.PI*82/180;
export const clampElevation=(angle:number):number=>Math.max(MIN_ELEVATION,Math.min(MAX_ELEVATION,angle));
export function pointerAction(button:number,shift:boolean):'pan'|'rotate'|null{
  return button===1||button===0&&shift?'rotate':button===0?'pan':null;
}
export function groundToScreen(p:WorldPoint,yaw:number,elevation:number):{x:number;y:number}{
  return {x:p.x*Math.cos(yaw)-p.z*Math.sin(yaw),y:(p.x*Math.sin(yaw)+p.z*Math.cos(yaw))*Math.sin(elevation)};
}
export function screenToGround(p:{x:number;y:number},yaw:number,elevation:number):WorldPoint{
  return {x:p.x*Math.cos(yaw)+p.y/Math.sin(elevation)*Math.sin(yaw),z:-p.x*Math.sin(yaw)+p.y/Math.sin(elevation)*Math.cos(yaw)};
}
const framingPoints=new WeakMap<GameMap,readonly WorldPoint[]>();
export function mapProjectionBounds(map:GameMap,yaw:number):{width:number;depth:number;projectedWidth:number;projectedDepth:number}{
  const anchors=anchorsForMap(map);
  let points=framingPoints.get(map);
  if(!points){
    const world=worldForMap(map);
    points=[...anchors.tiles,...anchors.lots,...(world?.surfaces.flatMap(s=>s.points)??[]),...(world?.objects.flatMap(o=>[-1,1].flatMap(dx=>[-1,1].map(dz=>({x:o.x+dx*o.scale,z:o.z+dz*o.scale}))))??[])];
    framingPoints.set(map,points);
  }
  let width=0,depth=0;
  for(const p of points){const screen=groundToScreen(p,yaw,Math.PI/2);width=Math.max(width,Math.abs(screen.x));depth=Math.max(depth,Math.abs(screen.y));}
  return {...anchors.bounds,projectedWidth:width*2+4,projectedDepth:depth*2+4};
}
export function labelPose(yaw:number,elevation:number):WorldPoint&{rotation:number;scaleZ:number}{
  // 地面数字需保持正向且抵消俯仰压缩；足迹仍须留在任意朝向路砖的内切圆内。
  const offset=Math.hypot(.36,.36);
  return {x:Math.sin(yaw)*offset,z:Math.cos(yaw)*offset,rotation:yaw,scaleZ:Math.min(1.55,Math.sin(DEFAULT_ELEVATION)/Math.sin(elevation))};
}
