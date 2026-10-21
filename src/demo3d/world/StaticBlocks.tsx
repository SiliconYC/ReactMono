import { createContext, useContext, useLayoutEffect, useMemo, useRef, type ReactNode } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';

type Registry = {parts:Map<THREE.Object3D,string>;dirty:boolean};
const BlocksContext=createContext<Registry|null>(null);
const CAPACITY=4096;

/** Static architectural trim shares geometry/material, while retaining world transforms and picking. */
export function StaticBlocks({children,revision}:{children:ReactNode;revision:object}):React.JSX.Element {
  const registry=useMemo<Registry>(()=>({parts:new Map(),dirty:true}),[]);
  const mesh=useRef<THREE.InstancedMesh>(null);
  const scratch=useMemo(()=>({inverse:new THREE.Matrix4(),matrix:new THREE.Matrix4(),color:new THREE.Color()}),[]);
  const invalidate=useThree(state=>state.invalidate);
  useLayoutEffect(()=>{if(mesh.current)mesh.current.count=0;},[]);
  useLayoutEffect(()=>{registry.dirty=true;invalidate();},[registry,revision,invalidate]);
  useFrame(()=>{
    const batch=mesh.current;if(!batch||!registry.dirty)return;
    if(registry.parts.size>CAPACITY)throw new Error('静态建筑细节超过实例容量');
    batch.updateWorldMatrix(true,false);scratch.inverse.copy(batch.matrixWorld).invert();
    const tileIds:(number|undefined)[]=[];
    let index=0;
    for(const [part,color] of registry.parts){
      part.updateWorldMatrix(true,false);
      scratch.matrix.multiplyMatrices(scratch.inverse,part.matrixWorld);
      batch.setMatrixAt(index,scratch.matrix);batch.setColorAt(index,scratch.color.set(color));
      let ancestor:THREE.Object3D|null=part;
      while(ancestor&&!Number.isInteger(ancestor.userData.tileId))ancestor=ancestor.parent;
      tileIds.push(ancestor?.userData.tileId);index++;
    }
    batch.count=index;batch.userData.tileIds=tileIds;
    batch.instanceMatrix.needsUpdate=true;
    if(batch.instanceColor)batch.instanceColor.needsUpdate=true;
    batch.computeBoundingBox();batch.computeBoundingSphere();registry.dirty=false;
  },-1.5);
  return <BlocksContext.Provider value={registry}>{children}
    <instancedMesh ref={mesh} args={[undefined,undefined,CAPACITY]}>
      <boxGeometry/><meshStandardMaterial roughness={.86}/>
    </instancedMesh>
  </BlocksContext.Provider>;
}

export function Block({at,size,color='#fff3da'}:{at:[number,number,number];size:[number,number,number];color?:string}):React.JSX.Element {
  const registry=useContext(BlocksContext),ref=useRef<THREE.Object3D>(null),invalidate=useThree(s=>s.invalidate);
  if(!registry)throw new Error('建筑部件需要统一静态实例批次');
  useLayoutEffect(()=>{
    const part=ref.current!;
    registry.parts.set(part,color);registry.dirty=true;invalidate();
    return ()=>{registry.parts.delete(part);registry.dirty=true;invalidate();};
  },[registry,color,...at,...size,invalidate]);
  return <object3D ref={ref} position={at} scale={size}/>;
}
