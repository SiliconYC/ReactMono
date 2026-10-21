import { useLayoutEffect, useRef } from 'react';
import { useThree } from '@react-three/fiber';
import * as THREE from 'three';
export type Instance = Readonly<{x:number;y:number;z:number;sx?:number;sy?:number;sz?:number;rotation?:number;rx?:number;rz?:number;color?:string;tileId?:number}>;
/** One geometry/material per batch. Bounds include every instance for correct frustum/shadows. */
export function Instances({items,children,onSelect,mapTiles=false,capacity}:{items:readonly Instance[];children:React.ReactNode;onSelect?:(id:number)=>void;mapTiles?:boolean;capacity?:number}):React.JSX.Element {
  const mesh=useRef<THREE.InstancedMesh>(null);
  const invalidate=useThree(s=>s.invalidate);
  const allocated=capacity??items.length;
  useLayoutEffect(()=>{
    if(!mesh.current)return;
    if(items.length>allocated)throw new Error('实例数量超过预留容量');
    mesh.current.count=items.length;
    if(capacity!==undefined&&!mesh.current.instanceColor)mesh.current.instanceColor=new THREE.InstancedBufferAttribute(new Float32Array(allocated*3),3);
    const transform=new THREE.Object3D(),color=new THREE.Color();
    items.forEach((p,i)=>{
      transform.position.set(p.x,p.y,p.z);transform.scale.set(p.sx??1,p.sy??1,p.sz??1);
      transform.rotation.set(p.rx??0,p.rotation??0,p.rz??0,'YXZ');transform.updateMatrix();
      mesh.current!.setMatrixAt(i,transform.matrix);
      if(p.color)mesh.current!.setColorAt(i,color.set(p.color));
    });
    mesh.current.instanceMatrix.needsUpdate=true;
    if(mesh.current.instanceColor)mesh.current.instanceColor.needsUpdate=true;
    mesh.current.computeBoundingSphere();mesh.current.computeBoundingBox();invalidate();
  },[items,invalidate,allocated,capacity]);
  return <instancedMesh key={allocated} ref={mesh} userData={{mapTiles,tileIds:items.map(p=>p.tileId)}} args={[undefined,undefined,allocated]} onClick={onSelect?e=>{e.stopPropagation();if(e.instanceId!==undefined)onSelect(e.instanceId);}:undefined}>{children}</instancedMesh>;
}
