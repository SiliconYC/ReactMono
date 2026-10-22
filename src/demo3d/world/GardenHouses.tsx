import { useEffect, useLayoutEffect, useMemo, useRef, type MutableRefObject } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import type { GameState } from '../../core/game.js';
import type { WorldDefinition } from '../../core/level-world.js';
import { GROUND_TOP } from './layout.js';
import { constructionPose, gardenHouseAccentGeometry, gardenHouseGeometry } from './lime-garden-models.js';
import { propertyRun } from '../../core/property-groups.js';
import { gardenOwnerColor } from './lime-garden-ownership.js';

type ConstructionCues=MutableRefObject<Map<number,number>>;

function HouseBatch({level,terraced,game,world,cues,reducedMotion}:{level:1|2;terraced:boolean;game:GameState;world:WorldDefinition;cues:ConstructionCues;reducedMotion:boolean}):React.JSX.Element {
  const geometry=useMemo(()=>gardenHouseGeometry(level,terraced),[level,terraced]),mesh=useRef<THREE.InstancedMesh>(null);
  const accents=useMemo(()=>gardenHouseAccentGeometry(level,terraced),[level,terraced]),accentMesh=useRef<THREE.InstancedMesh>(null);
  const transform=useMemo(()=>new THREE.Object3D(),[]);
  const items=game.tiles.filter(t=>{
    if(!t.ownerId||t.level!==level)return false;
    const run=propertyRun(game,t.id),index=run.findIndex(p=>p.id===t.id);
    const connected=!!((run[index-1]?.level??0)>0||(run[index+1]?.level??0)>0);
    return connected===terraced;
  });
  useEffect(()=>()=>{geometry.dispose();accents.dispose();},[geometry,accents]);
  useLayoutEffect(()=>{
    if(mesh.current)mesh.current.count=items.length;
    const batch=accentMesh.current;if(!batch)return;
    batch.count=items.length;
    const color=new THREE.Color();
    items.forEach((tile,index)=>batch.setColorAt(index,color.set(gardenOwnerColor(game,tile.ownerId))));
    if(batch.instanceColor)batch.instanceColor.needsUpdate=true;
  },[items,game]);
  useFrame(({clock})=>{
    const batch=mesh.current,trim=accentMesh.current;if(!batch||!trim)return;
    items.forEach((tile,i)=>{
      const p=world.tiles[tile.id],start=cues.current.get(tile.id);
      const pose=constructionPose(start===undefined?1:clock.elapsedTime-start,reducedMotion);
      transform.position.set(p.lotX,GROUND_TOP+.052,p.lotZ);
      transform.rotation.set(0,Math.atan2(p.x-p.lotX,p.z-p.lotZ),0);
      transform.scale.set(1,pose.scaleY,1);transform.updateMatrix();batch.setMatrixAt(i,transform.matrix);trim.setMatrixAt(i,transform.matrix);
    });
    for(const target of [batch,trim]){target.count=items.length;target.instanceMatrix.needsUpdate=true;target.computeBoundingBox();target.computeBoundingSphere();}
  });
  return <><instancedMesh ref={mesh} args={[geometry,undefined,game.tiles.length]} userData={{mapTiles:true,tileIds:items.map(t=>t.id)}} name={terraced?`${level}级共墙联排住宅`:level===1?'一级庭院小屋':'二级阳台住宅'}>
    <meshStandardMaterial vertexColors roughness={.82}/>
  </instancedMesh>
    <instancedMesh ref={accentMesh} args={[accents,undefined,game.tiles.length]} userData={{mapTiles:true,tileIds:items.map(t=>t.id)}} name={`${level}级住宅业主门楣与饰带`}>
      <meshStandardMaterial vertexColors roughness={.82}/>
    </instancedMesh></>;
}

function ConstructionDust({world,cues,reducedMotion}:{world:WorldDefinition;cues:ConstructionCues;reducedMotion:boolean}):React.JSX.Element {
  const mesh=useRef<THREE.InstancedMesh>(null),material=useRef<THREE.MeshStandardMaterial>(null),transform=useMemo(()=>new THREE.Object3D(),[]);
  useFrame(({clock})=>{
    const batch=mesh.current;if(!batch||!material.current)return;
    let index=0,opacity=0;
    for(const [id,start] of cues.current){
      const elapsed=clock.elapsedTime-start,pose=constructionPose(elapsed,reducedMotion),p=world.tiles[id];
      if(pose.finished)continue;
      opacity=Math.max(opacity,pose.dust*.5);
      for(let k=0;k<6;k++){
        const angle=k*Math.PI/3,radius=.37+elapsed*.35;
        transform.position.set(p.lotX+Math.sin(angle)*radius,GROUND_TOP+.06+pose.dust*.12,p.lotZ+Math.cos(angle)*radius);
        transform.scale.setScalar((.07+k%2*.035)*pose.dust);transform.rotation.set(0,angle,0);transform.updateMatrix();batch.setMatrixAt(index++,transform.matrix);
      }
    }
    batch.count=index;batch.instanceMatrix.needsUpdate=true;material.current.opacity=opacity;batch.computeBoundingBox();batch.computeBoundingSphere();
  });
  return <instancedMesh ref={mesh} args={[undefined,undefined,world.tiles.length*6]} name="建设落定轻尘">
    <icosahedronGeometry args={[1,1]}/><meshStandardMaterial ref={material} color="#f8edca" transparent opacity={0} depthWrite={false} roughness={1}/>
  </instancedMesh>;
}

export function GardenHouses({game,world,reducedMotion,onConstructionBusyChange}:{game:GameState;world:WorldDefinition;reducedMotion:boolean;onConstructionBusyChange?:(busy:boolean)=>void}):React.JSX.Element {
  const previous=useRef(game),cues=useRef(new Map<number,number>());
  const busyCallback=useRef(onConstructionBusyChange),lastBusy=useRef<boolean>();
  busyCallback.current=onConstructionBusyChange;
  const publishBusy=()=>{
    const busy=cues.current.size>0;
    if(lastBusy.current!==busy){lastBusy.current=busy;busyCallback.current?.(busy);}
  };
  const {clock,invalidate,gl}=useThree();
  useLayoutEffect(()=>{
    const before=previous.current;
    // 只呈现连续的一次实际升级；读档、批量调试和首次挂载均直接显示最终模型。
    if(!reducedMotion&&before.map.id===game.map.id&&game.revision===before.revision+1){
      for(const event of game.events.slice(before.events.length)){
        const id=event.details?.tileId;
        if(event.type==='property_upgraded'&&typeof id==='number'&&(game.tiles[id]?.level??0)>(before.tiles[id]?.level??0))cues.current.set(id,clock.elapsedTime);
      }
    }else cues.current.clear();
    previous.current=game;publishBusy();invalidate();
  },[game,reducedMotion,clock,invalidate]);
  useFrame(()=>{
    for(const [id,start] of cues.current)if(constructionPose(clock.elapsedTime-start,reducedMotion).finished)cues.current.delete(id);
    publishBusy();
    const shell=gl.domElement.closest<HTMLElement>('.canvas-shell');
    if(shell)shell.dataset.constructionTiles=[...cues.current.keys()].join(',');
    if(cues.current.size)invalidate();
  },-.5);
  useEffect(()=>()=>{const shell=gl.domElement.closest<HTMLElement>('.canvas-shell');if(shell)delete shell.dataset.constructionTiles;},[gl]);
  return <group name="游园住宅与真实建设">
    {[1,2].flatMap(level=>[false,true].map(terraced=><HouseBatch key={`${level}/${terraced}`} level={level as 1|2} terraced={terraced} game={game} world={world} cues={cues} reducedMotion={reducedMotion}/>))}
    <ConstructionDust world={world} cues={cues} reducedMotion={reducedMotion}/>
  </group>;
}
