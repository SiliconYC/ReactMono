/** Author-specified scene data. Geometry helpers never invent scene objects. */
export type ScenePoint = Readonly<{x:number;z:number}>;
export type SceneSurface = Readonly<{id:string;kind:'grass'|'sand'|'water'|'plaza';color:string;points:readonly ScenePoint[];holes:readonly (readonly ScenePoint[])[]}>;
export const SCENERY_KINDS=['tree','pine','flower','rock','bench','lamp','tower','bank','clinic','shop','prison','gazebo','boat','dock'] as const;
export type SceneObject=ScenePoint&Readonly<{id:string;kind:typeof SCENERY_KINDS[number];rotation:number;scale:number;color:string}>;
export type WorldDefinition=Readonly<{
  version:1;background:string;base:Readonly<{kind:'grass'|'water';color:string}>;
  tiles:readonly (ScenePoint&Readonly<{lotX:number;lotZ:number;rotation:number}>)[];
  surfaces:readonly SceneSurface[];objects:readonly SceneObject[];
}>;
const record=(v:unknown):v is Record<string,unknown>=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const fields=(v:Record<string,unknown>,names:string[])=>names.every(k=>Object.hasOwn(v,k))&&Object.keys(v).every(k=>names.includes(k));
const finite=(v:unknown):v is number=>typeof v==='number'&&Number.isFinite(v)&&Math.abs(v)<=100000;
const color=(v:unknown)=>typeof v==='string'&&/^#[\da-fA-F]{6}$/.test(v);
function fail():never{throw new Error('关卡世界数据无效');}
const cross=(a:ScenePoint,b:ScenePoint,c:ScenePoint)=>(b.x-a.x)*(c.z-a.z)-(b.z-a.z)*(c.x-a.x);
export function segmentsIntersect(a:ScenePoint,b:ScenePoint,c:ScenePoint,d:ScenePoint):boolean{
  const on=(p:ScenePoint,q:ScenePoint,r:ScenePoint)=>Math.abs(cross(p,q,r))<1e-8&&r.x>=Math.min(p.x,q.x)-1e-8&&r.x<=Math.max(p.x,q.x)+1e-8&&r.z>=Math.min(p.z,q.z)-1e-8&&r.z<=Math.max(p.z,q.z)+1e-8;
  return (cross(a,b,c)*cross(a,b,d)<0&&cross(c,d,a)*cross(c,d,b)<0)||on(a,b,c)||on(a,b,d)||on(c,d,a)||on(c,d,b);
}
export function pointInPolygon(p:ScenePoint,points:readonly ScenePoint[]):boolean{
  let inside=false;
  for(let i=0,j=points.length-1;i<points.length;j=i++){
    const a=points[i],b=points[j];
    if((a.z>p.z)!==(b.z>p.z)&&p.x<(b.x-a.x)*(p.z-a.z)/(b.z-a.z)+a.x)inside=!inside;
  }
  return inside;
}
function polygon(value:unknown):asserts value is ScenePoint[]{
  if(!Array.isArray(value)||value.length<3||value.length>1024)fail();
  for(const p of value)if(!record(p)||!fields(p,['x','z'])||!finite(p.x)||!finite(p.z))fail();
  const p=value as ScenePoint[];
  let area=0;
  for(let i=0;i<p.length;i++){
    const a=p[i],b=p[(i+1)%p.length];area+=a.x*b.z-b.x*a.z;
    if(Math.hypot(a.x-b.x,a.z-b.z)<1e-5)fail();
    for(let j=i+1;j<p.length;j++)if(j!==i+1&&!(i===0&&j===p.length-1)&&segmentsIntersect(a,b,p[j],p[(j+1)%p.length]))fail();
  }
  if(Math.abs(area)<1e-5)fail();
}
export function validateWorld(value:unknown,tileCount:number):asserts value is WorldDefinition{
  if(!record(value)||!fields(value,['version','background','base','tiles','surfaces','objects'])||value.version!==1||!color(value.background)||
    !record(value.base)||!fields(value.base,['kind','color'])||!['grass','water'].includes(String(value.base.kind))||!color(value.base.color)||
    !Array.isArray(value.tiles)||value.tiles.length!==tileCount||!Array.isArray(value.surfaces)||value.surfaces.length>128||!Array.isArray(value.objects)||value.objects.length>10000)fail();
  for(const p of value.tiles)if(!record(p)||!fields(p,['x','z','lotX','lotZ','rotation'])||!Object.values(p).every(finite))fail();
  const positions=value.tiles as unknown as WorldDefinition['tiles'];
  if(new Set(positions.map(p=>`${p.x},${p.z}`)).size!==tileCount||new Set(positions.map(p=>`${p.lotX},${p.lotZ}`)).size!==tileCount||positions.some(p=>Math.hypot(p.x-p.lotX,p.z-p.lotZ)<1.7))fail();
  const ids=new Set<string>();
  for(const surface of value.surfaces){
    if(!record(surface)||!fields(surface,['id','kind','color','points','holes'])||typeof surface.id!=='string'||!surface.id.length||ids.has(surface.id)||!['grass','sand','water','plaza'].includes(String(surface.kind))||!color(surface.color)||!Array.isArray(surface.holes)||surface.holes.length>64)fail();
    ids.add(surface.id);polygon(surface.points);
    const outer=surface.points;
    const holes=surface.holes;
    for(const hole of holes){
      polygon(hole);
      if(!hole.every(p=>pointInPolygon(p,outer)))fail();
      for(let i=0;i<hole.length;i++)for(let j=0;j<outer.length;j++)if(segmentsIntersect(hole[i],hole[(i+1)%hole.length],outer[j],outer[(j+1)%outer.length]))fail();
    }
    for(let i=0;i<holes.length;i++)for(let j=i+1;j<holes.length;j++){
      const a=holes[i] as ScenePoint[],b=holes[j] as ScenePoint[];
      if(pointInPolygon(a[0],b)||pointInPolygon(b[0],a))fail();
      for(let k=0;k<a.length;k++)for(let l=0;l<b.length;l++)if(segmentsIntersect(a[k],a[(k+1)%a.length],b[l],b[(l+1)%b.length]))fail();
    }
  }
  for(const o of value.objects){
    if(!record(o)||!fields(o,['id','kind','x','z','rotation','scale','color'])||typeof o.id!=='string'||!o.id.length||ids.has(o.id)||!SCENERY_KINDS.includes(o.kind as SceneObject['kind'])||!['x','z','rotation','scale'].every(k=>finite(o[k]))||Number(o.scale)<=0||Number(o.scale)>10||!color(o.color))fail();
    ids.add(o.id);
  }
}
export function visibleDecorations(world:WorldDefinition,bounds:{minX:number;maxX:number;minZ:number;maxZ:number}):readonly SceneObject[]{
  return world.objects.filter(o=>o.x+o.scale*3>=bounds.minX&&o.x-o.scale*3<=bounds.maxX&&o.z+o.scale*3>=bounds.minZ&&o.z-o.scale*3<=bounds.maxZ);
}
/** Separating-axis test for the actual rotated footprints, including a caller's safety margin. */
export function rectanglesOverlap(a:ScenePoint&{rotation:number;halfX:number;halfZ:number},b:ScenePoint&{rotation:number;halfX:number;halfZ:number}):boolean{
  const axes=(r:number)=>[{x:Math.cos(r),z:-Math.sin(r)},{x:Math.sin(r),z:Math.cos(r)}];
  const aa=axes(a.rotation),bb=axes(b.rotation);
  for(const axis of [...aa,...bb]){
    const dot=(p:ScenePoint)=>Math.abs(axis.x*p.x+axis.z*p.z);
    const reach=a.halfX*dot(aa[0])+a.halfZ*dot(aa[1])+b.halfX*dot(bb[0])+b.halfZ*dot(bb[1]);
    if(Math.abs((b.x-a.x)*axis.x+(b.z-a.z)*axis.z)>=reach-1e-5)return false;
  }
  return true;
}
