import { useEffect, useMemo, useRef, useState } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import type { SceneObject } from '../../core/level-world.js';
import { URBAN_SCENERY_KINDS } from '../../core/level-world.js';
import { Instances } from './Instances.js';
import { GROUND_TOP } from './layout.js';
import { GABLE_ROOF_VERTICES } from './town-kit.js';
import { urbanParts, URBAN_LABELS, type UrbanKind, type UrbanPart } from './urban-kit.js';

const kinds=new Set<string>(URBAN_SCENERY_KINDS);
export const isUrbanObject=(object:SceneObject):boolean=>kinds.has(object.kind);

function Material({ghost}:{ghost:boolean}):React.JSX.Element {
  return <meshStandardMaterial transparent={ghost} opacity={ghost?.13:1} depthWrite={!ghost} roughness={.89}/>;
}

function SignBatch({parts,ghost}:{parts:readonly UrbanPart[];ghost:boolean}):React.JSX.Element {
  const texture=useMemo(()=>{
    const canvas=document.createElement('canvas');canvas.width=256;canvas.height=96*URBAN_LABELS.length;
    const context=canvas.getContext('2d')!;
    for(const [i,label]of URBAN_LABELS.entries()) {
      context.fillStyle='#3e5759';context.fillRect(0,i*96,256,96);
      context.strokeStyle='#d3be91';context.lineWidth=2;context.strokeRect(4,i*96+5,248,86);
      context.fillStyle='#fff3d8';context.font='bold 64px "PingFang SC", "Microsoft YaHei", sans-serif';
      context.textAlign='center';context.textBaseline='middle';context.fillText(label,128,i*96+50,234);
    }
    const result=new THREE.CanvasTexture(canvas);result.colorSpace=THREE.SRGBColorSpace;return result;
  },[]);
  const geometry=useMemo(()=>{
    const result=new THREE.PlaneGeometry(1,1);
    result.setAttribute('signRow',new THREE.InstancedBufferAttribute(new Float32Array(parts.map(p=>URBAN_LABELS.indexOf(p.label as typeof URBAN_LABELS[number]))),1));return result;
  },[parts]);
  useEffect(()=>()=>texture.dispose(),[texture]);useEffect(()=>()=>geometry.dispose(),[geometry]);
  return <Instances items={parts}><primitive attach="geometry" object={geometry}/><meshStandardMaterial transparent={ghost} opacity={ghost?.13:1} depthWrite={!ghost} map={texture} roughness={.9} customProgramCacheKey={()=>'urban-chinese-atlas-v1'} onBeforeCompile={program=>{
    program.vertexShader='attribute float signRow;\n'+program.vertexShader;
    program.vertexShader=program.vertexShader.replace('#include <uv_vertex>',`#include <uv_vertex>\n vMapUv.y=(vMapUv.y+${URBAN_LABELS.length-1}.0-signRow)/${URBAN_LABELS.length}.0;`);
  }}/></Instances>;
}

function PartLayer({parts,ghost=false}:{parts:readonly UrbanPart[];ghost?:boolean}):React.JSX.Element {
  const roof=useMemo(()=>{
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(GABLE_ROOF_VERTICES,3));g.computeVertexNormals();return g;
  },[]);
  const arch=useMemo(()=>{
    const s=new THREE.Shape();s.moveTo(-.5,-.5);s.lineTo(.5,-.5);s.lineTo(.5,0);s.absarc(0,0,.5,0,Math.PI,false);s.closePath();
    const g=new THREE.ExtrudeGeometry(s,{depth:1,bevelEnabled:false,curveSegments:8});g.translate(0,0,-.5);return g;
  },[]);
  useEffect(()=>()=>{roof.dispose();arch.dispose();},[roof,arch]);
  const byShape=useMemo(()=>Object.fromEntries(['box','roof','arch','cylinder','cone','leaf','sphere','sign'].map(shape=>[shape,parts.filter(p=>p.shape===shape)])),[parts]);
  return <group name="合批的生活街区模型">
    <Instances items={byShape.box}><boxGeometry/><Material ghost={ghost}/></Instances>
    <Instances items={byShape.roof}><primitive attach="geometry" object={roof}/><Material ghost={ghost}/></Instances>
    <Instances items={byShape.arch}><primitive attach="geometry" object={arch}/><Material ghost={ghost}/></Instances>
    <Instances items={byShape.cylinder}><cylinderGeometry args={[.5,.5,1,12]}/><Material ghost={ghost}/></Instances>
    <Instances items={byShape.cone}><coneGeometry args={[.5,1,8]}/><Material ghost={ghost}/></Instances>
    <Instances items={byShape.leaf}><dodecahedronGeometry args={[.5,0]}/><Material ghost={ghost}/></Instances>
    <Instances items={byShape.sphere}><sphereGeometry args={[.5,10,6]}/><Material ghost={ghost}/></Instances>
    <SignBatch parts={byShape.sign} ghost={ghost}/>
  </group>;
}

export function UrbanParts({parts}:{parts:readonly UrbanPart[]}):React.JSX.Element {
  const opaque=useMemo(()=>parts.filter(p=>(p.alpha??1)===1),[parts]);
  const ghost=useMemo(()=>parts.filter(p=>(p.alpha??1)<1),[parts]);
  return <><PartLayer parts={opaque}/>{ghost.length>0&&<PartLayer parts={ghost} ghost/>}</>;
}

export function UrbanScenery({objects,actor}:{objects:readonly SceneObject[];actor?:THREE.Vector3}):React.JSX.Element {
  const {camera,gl}=useThree();
  const [occluded,setOccluded]=useState('');
  const previous=useRef('');
  const assets=useMemo(()=>objects.filter(isUrbanObject).map(o=>{
    const c=Math.cos(o.rotation),s=Math.sin(o.rotation);
    const parts=urbanParts(o.kind as UrbanKind,o.color).map(p=>({...p,
      x:o.x+(c*p.x+s*p.z)*o.scale,z:o.z+(-s*p.x+c*p.z)*o.scale,y:GROUND_TOP+p.y*o.scale,
      sx:p.sx*o.scale,sy:p.sy*o.scale,sz:p.sz*o.scale,rotation:o.rotation+(p.rotation??0)
    }));
    const box=new THREE.Box3();
    for(const p of parts){const cos=Math.abs(Math.cos(p.rotation)),sin=Math.abs(Math.sin(p.rotation)),hx=(cos*p.sx+sin*p.sz)/2,hz=(sin*p.sx+cos*p.sz)/2;box.expandByPoint(new THREE.Vector3(p.x-hx,p.y-p.sy/2,p.z-hz));box.expandByPoint(new THREE.Vector3(p.x+hx,p.y+p.sy/2,p.z+hz));}
    return {id:o.id,parts,box,tall:['corner-cafe','hotel','bookshop','bakery','apartment','greenhouse','market-hall','workshop'].includes(o.kind)};
  }),[objects]);
  const scratch=useMemo(()=>({ray:new THREE.Ray(),direction:new THREE.Vector3(),origin:new THREE.Vector3(),hit:new THREE.Vector3()}),[]);
  useFrame(()=>{
    if(!actor)return;
    camera.getWorldDirection(scratch.direction).negate();
    const ids=assets.filter(a=>a.tall&&[.4,1.1].some(height=>{
      scratch.origin.copy(actor);scratch.origin.y+=height;scratch.ray.set(scratch.origin,scratch.direction);
      return scratch.ray.intersectBox(a.box,scratch.hit)!==null&&scratch.hit.distanceTo(scratch.origin)>.35;
    })).map(a=>a.id).sort().join('|');
    if(ids!==previous.current){previous.current=ids;setOccluded(ids);}
    const shell=gl.domElement.closest<HTMLElement>('.canvas-shell');if(shell)shell.dataset.cutawayBuildings=ids;
  });
  // Fade only the obstructing architectural body. Every instance still uses
  // the global cast/receive policy; no object gets a shadow exception.
  const parts=useMemo(()=>{const ids=new Set(occluded.split('|'));return assets.flatMap(a=>a.parts.map(p=>({...p,alpha:ids.has(a.id)?.17:1})));},[assets,occluded]);
  return <UrbanParts parts={parts}/>;
}
