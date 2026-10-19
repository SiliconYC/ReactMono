import { useMemo } from 'react';
import { visibleDecorations, type WorldDefinition, type SceneObject } from '../../core/level-world.js';
import { Instances } from './Instances.js';
import { GROUND_TOP } from './layout.js';
import type { WorldView } from './world-view.js';
import { BankBuilding, ClockTower } from './SceneryModels.js';

function Landmark({o}:{o:SceneObject}):React.JSX.Element{
  switch(o.kind){
    case 'bank':return <BankBuilding/>;
    case 'clinic':case 'shop':case 'prison':return <group>
      <mesh position={[0,.48,0]}><boxGeometry args={[1.15,.96,.9]}/><meshStandardMaterial color={o.kind==='prison'?'#b2bdb1':'#f2e3c2'}/></mesh>
      <mesh position={[0,1.02,0]}><boxGeometry args={[1.35,.12,1.12]}/><meshStandardMaterial color={o.color}/></mesh>
      <mesh position={[0,.32,.46]}><boxGeometry args={[.24,.64,.025]}/><meshStandardMaterial color="#4e7166"/></mesh>
      {o.kind==='clinic'?<group position={[0,.78,.47]}>
        <mesh><boxGeometry args={[.36,.10,.03]}/><meshStandardMaterial color="#d77d69"/></mesh>
        <mesh><boxGeometry args={[.1,.36,.03]}/><meshStandardMaterial color="#d77d69"/></mesh>
      </group>:o.kind==='shop'?<mesh position={[0,.76,.61]} rotation={[.2,0,0]}><boxGeometry args={[1.2,.12,.4]}/><meshStandardMaterial color={o.color}/></mesh>:
        [-.36,-.18,.18,.36].map(x=><mesh key={x} position={[x,.65,.47]}><boxGeometry args={[.035,.3,.035]}/><meshStandardMaterial color="#526861"/></mesh>)}
    </group>;
    case 'tower':return <ClockTower/>;
    case 'bench':return <group>
      <mesh position={[0,.32,0]}><boxGeometry args={[1.2,.12,.42]}/><meshStandardMaterial color="#b38961"/></mesh>
      <mesh position={[0,.57,-.17]}><boxGeometry args={[1.2,.4,.08]}/><meshStandardMaterial color="#b38961"/></mesh>
      {[-.45,.45].map(x=><mesh key={x} position={[x,.15,0]}><boxGeometry args={[.08,.3,.35]}/><meshStandardMaterial color="#55736a"/></mesh>)}
    </group>;
    case 'lamp':return <group>
      <mesh position={[0,.8,0]}><cylinderGeometry args={[.035,.065,1.6,6]}/><meshStandardMaterial color="#47695d"/></mesh>
      <mesh position={[0,1.65,0]}><octahedronGeometry args={[.17]}/><meshStandardMaterial color="#f6deb0" emissive="#e1bc70" emissiveIntensity={.25}/></mesh>
    </group>;
    case 'gazebo':return <group>
      <mesh position={[0,.035,0]}><cylinderGeometry args={[.85,.85,.07,6]}/><meshStandardMaterial color="#d9c9a6"/></mesh>
      {[0,1,2,3,4,5].map(i=><mesh key={i} position={[Math.sin(i*Math.PI/3)*.65,.65,Math.cos(i*Math.PI/3)*.65]}><cylinderGeometry args={[.045,.055,1.25,6]}/><meshStandardMaterial color="#c7ad7c"/></mesh>)}
      <mesh position={[0,1.46,0]}><coneGeometry args={[1.05,.5,6]}/><meshStandardMaterial color="#588e7c"/></mesh>
    </group>;
    case 'boat':return <group position={[0,-.04,0]}>
      <mesh position={[0,.1,0]} scale={[.52,.22,1]}><sphereGeometry args={[1,8,6]}/><meshStandardMaterial color="#b58763"/></mesh>
      <mesh position={[0,.8,0]}><cylinderGeometry args={[.025,.035,1.5,5]}/><meshStandardMaterial color="#9d855f"/></mesh>
      <mesh position={[.22,1,0]} rotation={[0,0,-.15]}><coneGeometry args={[.47,1,3]}/><meshStandardMaterial color={o.color}/></mesh>
    </group>;
    case 'dock':return <group position={[0,-.01,0]}>
      <mesh position={[0,0,0]}><boxGeometry args={[1.1,.08,3]}/><meshStandardMaterial color={o.color}/></mesh>
      {[-.45,.45].flatMap(x=>[-1.25,1.25].map(z=><mesh key={`${x}/${z}`} position={[x,-.12,z]}><cylinderGeometry args={[.07,.08,.5,6]}/><meshStandardMaterial color="#9b805f"/></mesh>))}
    </group>;
    default:return <group/>;
  }
}
/** Culling selects existing records. It never creates or moves a plant. */
export function AuthoredScenery({world,view}:{world:WorldDefinition;view:WorldView}):React.JSX.Element{
  const objects=useMemo(()=>visibleDecorations(world,view),[world,view]);
  const items=(kind:string,y:number,scale=1)=>objects.filter(o=>o.kind===kind).map(o=>({...o,y:GROUND_TOP+y*o.scale,sx:o.scale*scale,sy:o.scale*scale,sz:o.scale*scale}));
  const trunks=objects.filter(o=>o.kind==='tree'||o.kind==='pine').map(o=>({...o,y:GROUND_TOP+.4*o.scale,sx:o.scale,sy:o.scale,sz:o.scale,color:'#947a56'}));
  const detailed=(o:SceneObject)=>view.zoom>=17||!o.id.startsWith('站点-');
  const stationSilhouettes=objects.filter(o=>!detailed(o)).map(o=>({...o,y:GROUND_TOP+.42*o.scale,sx:o.scale,sy:o.scale,sz:o.scale}));
  const foliage=items('tree',1.1);
  const flowers=objects.filter(o=>o.kind==='flower');
  const petals=flowers.flatMap(o=>[0,1,2,3,4].map(i=>({x:o.x+Math.cos(i*Math.PI*.4)*.19*o.scale,z:o.z+Math.sin(i*Math.PI*.4)*.19*o.scale,y:GROUND_TOP+.34*o.scale,sx:o.scale,sy:o.scale*.4,sz:o.scale,color:o.color})));
  return <group name="逐个指定的景物">
    <Instances items={trunks}><cylinderGeometry args={[.07,.11,.8,6]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={foliage}><dodecahedronGeometry args={[.72,1]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={foliage.map(o=>({...o,x:o.x-.27*o.sx,z:o.z+.19*o.sx,y:o.y-.18*o.sx,sx:o.sx*.65,sy:o.sy*.7,sz:o.sz*.65}))}><dodecahedronGeometry args={[.72,0]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={items('pine',1.15)}><coneGeometry args={[.7,1.9,7]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={items('rock',.23)}><dodecahedronGeometry args={[.4,0]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={items('flower',.13)}><cylinderGeometry args={[.03,.035,.26,5]}/><meshStandardMaterial color="#6c9161" roughness={1}/></Instances>
    <Instances items={petals}><sphereGeometry args={[.17,6,4]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={items('flower',.35)}><sphereGeometry args={[.1,6,4]}/><meshStandardMaterial color="#e6bd68" roughness={1}/></Instances>
    <Instances items={stationSilhouettes}><boxGeometry args={[1.1,.84,1.1]}/><meshStandardMaterial roughness={1}/></Instances>
    {objects.filter(o=>!['tree','pine','rock','flower'].includes(o.kind)&&detailed(o)).map(o=><group key={o.id} name={o.id} position={[o.x,GROUND_TOP,o.z]} rotation={[0,o.rotation,0]} scale={o.scale}><Landmark o={o}/></group>)}
  </group>;
}
