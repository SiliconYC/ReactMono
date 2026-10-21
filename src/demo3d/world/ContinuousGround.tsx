import { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import type { GameMap } from '../../core/types.js';
import { worldForMap } from '../../core/level-data.js';
import type { ScenePoint } from '../../core/level-world.js';
import { GROUND_TOP } from './layout.js';
import { groundBounds, type WorldView } from './world-view.js';
import { AuthoredScenery } from './AuthoredScenery.js';

function path(points:readonly ScenePoint[]):THREE.Path {
  const p=new THREE.Path();points.forEach((v,i)=>i?p.lineTo(v.x,-v.z):p.moveTo(v.x,-v.z));p.closePath();return p;
}
export function surfaceGeometry(points:readonly ScenePoint[],holes:readonly (readonly ScenePoint[])[],thickness=0):THREE.BufferGeometry{
  const shape=new THREE.Shape(path(points).getPoints());shape.holes=holes.map(path);
  const geometry=thickness?new THREE.ExtrudeGeometry(shape,{depth:thickness,bevelEnabled:false}):new THREE.ShapeGeometry(shape);geometry.rotateX(-Math.PI/2);if(thickness)geometry.translate(0,-thickness,0);return geometry;
}
function waterFinish(program:THREE.WebGLProgramParametersWithUniforms):void {
  program.vertexShader='varying vec2 townSurface;\n'+program.vertexShader;
  program.vertexShader=program.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\n townSurface=position.xz;');
  program.fragmentShader='varying vec2 townSurface;\n'+program.fragmentShader;
  program.fragmentShader=program.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
    float ripple=sin(townSurface.x*2.8+townSurface.y*5.0+sin(townSurface.y*2.0)*0.5);
    float glint=smoothstep(0.96,1.0,ripple);
    diffuseColor.rgb *= 0.98+0.035*sin(townSurface.x*0.8+townSurface.y*1.2);
    diffuseColor.rgb += vec3(0.045,0.052,0.043)*glint;
  `);
}
/** The base material is explicitly chosen by the author; every shoreline comes from JSON. */
export function ContinuousGround({view,map,actor}:{view:WorldView;map:GameMap;actor?:THREE.Vector3}):React.JSX.Element{
  const world=worldForMap(map);
  const surfaces=world?.surfaces??[];
  const geometry=useMemo(()=>{
    // Include all authored water holes even when the camera is browsing beyond the level.
    const points=surfaces.flatMap(s=>s.points);
    const {minX,maxX,minZ,maxZ}=groundBounds(view,points);
    return surfaceGeometry([{x:minX,z:minZ},{x:maxX,z:minZ},{x:maxX,z:maxZ},{x:minX,z:maxZ}],world?.base.kind==='grass'?surfaces.filter(s=>s.kind==='water').map(s=>s.points):[]);
  },[world,view]);
  const islandCaps=useMemo(()=>world?.base.kind==='grass'?surfaces.filter(s=>s.kind==='water').flatMap(s=>s.holes.map(h=>surfaceGeometry(h,[]))):[],[world]);
  useEffect(()=>()=>islandCaps.forEach(g=>g.dispose()),[islandCaps]);
  const terrain=useMemo(()=>surfaces.map(s=>({surface:s,geometry:surfaceGeometry(s.points,s.holes,s.kind==='grass'||s.kind==='sand'?.07:0)})),[world]);
  useEffect(()=>()=>geometry.dispose(),[geometry]);
  useEffect(()=>()=>terrain.forEach(t=>t.geometry.dispose()),[terrain]);
  return <group name="关卡指定地形">
    <mesh geometry={geometry} position={[0,GROUND_TOP-(world?.base.kind==='water'?.07:0),0]}><meshStandardMaterial color={world?.base.color??'#b7cd9a'} roughness={1}/></mesh>
    {islandCaps.map((g,i)=><mesh key={`base-island-${i}`} geometry={g} position={[0,GROUND_TOP,0]}><meshStandardMaterial color={world?.base.color} roughness={1}/></mesh>)}
    {terrain.map(({surface:s,geometry:g})=><mesh key={s.id} name={s.id} geometry={g} position={[0,GROUND_TOP+(s.kind==='water'?-.07:s.kind==='grass'?0.002:.004),0]}>
      <meshStandardMaterial color={s.color} roughness={s.kind==='water'?.48:1} metalness={s.kind==='water'?.06:0} onBeforeCompile={s.kind==='water'?waterFinish:undefined} customProgramCacheKey={()=>s.kind==='water'?'town-water-ripples-v1':'town-terrain'}/>
    </mesh>)}
    {world&&<AuthoredScenery world={world} view={view} actor={actor}/>}
  </group>;
}
