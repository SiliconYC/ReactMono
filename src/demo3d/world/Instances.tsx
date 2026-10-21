import { useLayoutEffect, useRef } from 'react';
import { useThree } from '@react-three/fiber';
import * as THREE from 'three';
export type Instance = Readonly<{x:number;y:number;z:number;sx?:number;sy?:number;sz?:number;rotation?:number;rx?:number;rz?:number;color?:string;tileId?:number}>;
/** One geometry/material per batch. Bounds include every instance for correct frustum/shadows. */
export function Instances({items,children,onSelect,mapTiles=false}:{items:readonly Instance[];children:React.ReactNode;onSelect?:(id:number)=>void;mapTiles?:boolean}):React.JSX.Element {
  const mesh=useRef<THREE.InstancedMesh>(null);
  const invalidate=useThree(s=>s.invalidate);
  useLayoutEffect(()=>{
    if(!mesh.current)return;
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
  },[items,invalidate]);
  return <instancedMesh key={items.length} ref={mesh} userData={{mapTiles,tileIds:items.map(p=>p.tileId)}} args={[undefined,undefined,items.length]} onClick={onSelect?e=>{e.stopPropagation();if(e.instanceId!==undefined)onSelect(e.instanceId);}:undefined}>{children}</instancedMesh>;
}
