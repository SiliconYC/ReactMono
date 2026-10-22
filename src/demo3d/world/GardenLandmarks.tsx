import { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import type { WorldDefinition } from '../../core/level-world.js';
import { Instances, type Instance } from './Instances.js';
import { GROUND_TOP } from './layout.js';
import { foldedRoofGeometry } from './lime-garden-models.js';

function branch(a:THREE.Vector3,b:THREE.Vector3,thickness:number):Instance {
  const direction=b.clone().sub(a),center=a.clone().add(b).multiplyScalar(.5);
  const rotation=new THREE.Euler().setFromQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0),direction.clone().normalize()),'YXZ');
  return {x:center.x,y:center.y,z:center.z,sx:thickness,sy:direction.length(),sz:thickness,rx:rotation.x,rotation:rotation.y,rz:rotation.z,color:'#b68d51'};
}

export function GardenTrees({world}:{world:WorldDefinition}):React.JSX.Element {
  const trees=world.objects.filter(o=>o.kind==='tree');
  const foliage=useMemo(()=>{
    const g=new THREE.IcosahedronGeometry(1,2),p=g.getAttribute('position');
    for(let i=0;i<p.count;i++){
      const x=p.getX(i),y=p.getY(i),z=p.getZ(i),variation=1+.035*Math.sin(x*13+z*7)*Math.cos(y*11);
      p.setXYZ(i,x*variation,y*variation,z*variation);
    }
    g.computeVertexNormals();return g;
  },[]);
  useEffect(()=>()=>foliage.dispose(),[foliage]);
  const crowns=[[-.27,1.12,.06,.42,.49,.43],[.27,1.24,.02,.43,.5,.42],[-.05,1.46,-.24,.45,.54,.43],[-.12,1.72,.02,.42,.48,.43],[.05,1.31,.28,.45,.47,.43]];
  const leaves=trees.flatMap((o,index)=>crowns.map(([x,y,z,sx,sy,sz],k)=>({x:o.x+x*o.scale,y:GROUND_TOP+y*o.scale,z:o.z+z*o.scale,sx:sx*o.scale,sy:sy*o.scale,sz:sz*o.scale,rotation:index*.63+k*.8,color:new THREE.Color(o.color).offsetHSL((k%2)*.012,0,(k-2)*.026).getStyle()})));
  const limbs=trees.flatMap(o=>{
    const p=(x:number,y:number,z:number)=>new THREE.Vector3(o.x+x*o.scale,GROUND_TOP+y*o.scale,o.z+z*o.scale);
    return [branch(p(0,0,0),p(-.03,1.35,-.03),o.scale),branch(p(-.02,.58,0),p(-.31,1.18,.08),o.scale*.57),branch(p(-.02,.77,0),p(.32,1.25,.01),o.scale*.52),branch(p(0,.86,0),p(.08,1.38,.31),o.scale*.42)];
  });
  return <group name="分枝与簇状树冠">
    <Instances items={limbs}><cylinderGeometry args={[.065,.12,1,9]}/><meshStandardMaterial roughness={.94}/></Instances>
    <Instances items={leaves}><primitive object={foliage} attach="geometry"/><meshStandardMaterial roughness={.82} flatShading/></Instances>
    <Instances items={trees.flatMap((o,i)=>[0,1,2].map(k=>({x:o.x+Math.sin(k*2.1+i)*.49*o.scale,y:GROUND_TOP+(1.14+k*.16)*o.scale,z:o.z+Math.cos(k*2.1+i)*.49*o.scale,sx:o.scale,sy:o.scale,sz:o.scale,color:'#e9d766'})))}>
      <icosahedronGeometry args={[.07,1]}/><meshStandardMaterial roughness={.76}/>
    </Instances>
    <Instances items={trees.flatMap(o=>[0,1,2].map(k=>({x:o.x+Math.sin(k*2.1)*.12*o.scale,y:GROUND_TOP+.035*o.scale,z:o.z+Math.cos(k*2.1)*.12*o.scale,sx:o.scale*.1,sy:o.scale*.025,sz:o.scale*.2,rotation:k*2.1,color:'#a3b95a'})))}>
      <sphereGeometry args={[1,10,6]}/><meshStandardMaterial roughness={1}/>
    </Instances>
  </group>;
}

export function BluePavilion({x,z,scale}:{x:number;z:number;scale:number}):React.JSX.Element {
  const roof=useMemo(foldedRoofGeometry,[]);useEffect(()=>()=>roof.dispose(),[roof]);
  const radial=(count:number,radius:number,y:number)=>Array.from({length:count},(_,i)=>({x:Math.sin(i/count*Math.PI*2)*radius,y,z:Math.cos(i/count*Math.PI*2)*radius,rotation:i/count*Math.PI*2}));
  return <group position={[x,GROUND_TOP,z]} scale={scale} name="叠檐折瓦蓝瓷圆亭">
    <mesh position={[0,.045,0]}><cylinderGeometry args={[1.2,1.25,.09,64]}/><meshStandardMaterial color="#a1d7e9" roughness={.8}/></mesh>
    <mesh position={[0,.115,0]}><cylinderGeometry args={[1.07,1.16,.05,64]}/><meshStandardMaterial color="#d9ece3" roughness={.8}/></mesh>
    <mesh position={[0,.155,0]}><cylinderGeometry args={[1.01,1.06,.03,64]}/><meshStandardMaterial color="#f5edce" roughness={.8}/></mesh>
    <mesh position={[0,.43,0]}><cylinderGeometry args={[.68,.71,.53,32]}/><meshStandardMaterial color="#df826b" roughness={.8}/></mesh>
    <Instances items={radial(12,.73,.49)}><cylinderGeometry args={[.037,.043,.65,10]}/><meshStandardMaterial color="#fff3c7" roughness={.85}/></Instances>
    <Instances items={radial(12,.69,.44)}><boxGeometry args={[.13,.29,.045]}/><meshStandardMaterial color="#bc594c" roughness={.85}/></Instances>
    <Instances items={radial(12,.72,.455)}><boxGeometry args={[.018,.32,.018]}/><meshStandardMaterial color="#edbb70" roughness={.7}/></Instances>
    <Instances items={radial(32,.98,.255)}><cylinderGeometry args={[.018,.026,.18,7]}/><meshStandardMaterial color="#f8f2d7" roughness={.85}/></Instances>
    {[.19,.34].map(y=><mesh key={y} position={[0,y,0]} rotation={[Math.PI/2,0,0]}><torusGeometry args={[.98,.022,6,64]}/><meshStandardMaterial color="#f8f2d7" roughness={.8}/></mesh>)}
    {[{y:.74,s:1},{y:1.28,s:.78},{y:1.76,s:.52}].map(({y,s},i)=><group key={y} position={[0,y,0]} scale={s}>
      <mesh geometry={roof}><meshStandardMaterial color={['#4c9fe8','#478fda','#5ca6e5'][i]} vertexColors roughness={.6}/></mesh>
      <mesh position={[0,.02,0]}><cylinderGeometry args={[1.045,1.015,.04,128]}/><meshStandardMaterial color="#407bc3" roughness={.65}/></mesh>
      <mesh position={[0,.071,0]} rotation={[Math.PI/2,0,0]}><torusGeometry args={[1.075,.013,6,128]}/><meshStandardMaterial color="#a9d7f6" roughness={.65}/></mesh>
      <Instances items={radial(64,1.075,.059)}><sphereGeometry args={[.022,8,6]}/><meshStandardMaterial color="#91c7ef" roughness={.7}/></Instances>
    </group>)}
    <mesh position={[0,1.27,0]}><cylinderGeometry args={[.39,.43,.23,32]}/><meshStandardMaterial color="#e1be7f" roughness={.8}/></mesh>
    <mesh position={[0,1.73,0]}><cylinderGeometry args={[.24,.29,.18,32]}/><meshStandardMaterial color="#f3d99b" roughness={.8}/></mesh>
    <mesh position={[0,2.17,0]}><cylinderGeometry args={[.065,.08,.12,16]}/><meshStandardMaterial color="#edd29a" roughness={.7}/></mesh>
    <mesh position={[0,2.27,0]}><sphereGeometry args={[.11,20,12]}/><meshStandardMaterial color="#f3d6a5" roughness={.55}/></mesh>
  </group>;
}
