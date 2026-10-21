import { useMemo } from 'react';
import { visibleDecorations, type WorldDefinition, type SceneObject } from '../../core/level-world.js';
import { Instances } from './Instances.js';
import { GROUND_TOP } from './layout.js';
import type { WorldView } from './world-view.js';
import { BankBuilding, ClockTower, FacilityBuilding, Block } from './SceneryModels.js';

function Landmark({o}:{o:SceneObject}):React.JSX.Element{
  switch(o.kind){
    case 'bank':return <BankBuilding/>;
    case 'clinic':case 'shop':case 'prison':return <FacilityBuilding kind={o.kind} color={o.color}/>;
    case 'tower':return <ClockTower/>;
    case 'bench':return <group>
      {[-.15,0,.15].map(z=><Block key={z} at={[0,.32,z]} size={[1.2,.075,.115]} color="#b3946c"/>)}
      {[.48,.64].map(y=><Block key={y} at={[0,y,-.19]} size={[1.2,.12,.065]} color="#b3946c"/>)}
      {[-.45,.45].map(x=><mesh key={x} position={[x,.15,0]}><boxGeometry args={[.08,.3,.35]}/><meshStandardMaterial color="#55736a"/></mesh>)}
    </group>;
    case 'lamp':return <group>
      <mesh position={[0,.8,0]}><cylinderGeometry args={[.035,.065,1.6,6]}/><meshStandardMaterial color="#47695d"/></mesh>
      <Block at={[0,.045,0]} size={[.2,.09,.2]} color="#698371"/><Block at={[0,1.63,0]} size={[.2,.3,.2]} color="#f1d9a1"/><mesh position={[0,1.85,0]} rotation={[0,Math.PI/4,0]}><coneGeometry args={[.22,.18,4]}/><meshStandardMaterial color="#47695d"/></mesh>{[-.1,.1].flatMap(x=>[-.1,.1].map(z=><Block key={`${x}/${z}`} at={[x,1.63,z]} size={[.025,.32,.025]} color="#47695d"/>))}
    </group>;
    case 'gazebo':return <group>
      <mesh position={[0,.035,0]}><cylinderGeometry args={[.85,.85,.07,6]}/><meshStandardMaterial color="#d9c9a6"/></mesh>
      {[0,1,2,3,4,5].map(i=><mesh key={i} position={[Math.sin(i*Math.PI/3)*.65,.65,Math.cos(i*Math.PI/3)*.65]}><cylinderGeometry args={[.045,.055,1.25,6]}/><meshStandardMaterial color="#c7ad7c"/></mesh>)}
      <mesh position={[0,1.21,0]}><cylinderGeometry args={[.87,.87,.1,6]}/><meshStandardMaterial color="#ddcc9c"/></mesh><mesh position={[0,1.46,0]}><coneGeometry args={[1.05,.5,6]}/><meshStandardMaterial color="#588e7c"/></mesh>
      <mesh position={[0,1.76,0]}><sphereGeometry args={[.075,6,4]}/><meshStandardMaterial color="#d6b26d"/></mesh>
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
  const objectTileIds=useMemo(()=>{
    const lots=new Map(world.tiles.map((p,id)=>[`${p.lotX},${p.lotZ}`,id]));
    return new Map(world.objects.map(o=>[o.id,lots.get(`${o.x},${o.z}`)]));
  },[world]);
  const objects=useMemo(()=>visibleDecorations(world,view),[world,view]);
  const items=(kind:string,y:number,scale=1)=>objects.filter(o=>o.kind===kind).map(o=>({...o,y:GROUND_TOP+y*o.scale,sx:o.scale*scale,sy:o.scale*scale,sz:o.scale*scale}));
  const trunks=objects.filter(o=>o.kind==='tree'||o.kind==='pine').map(o=>({...o,y:GROUND_TOP+.4*o.scale,sx:o.scale,sy:o.scale,sz:o.scale,color:'#947a56'}));
  const detailed=(o:SceneObject)=>world.tiles.length<=24||view.zoom>=17||!o.id.startsWith('站点-');
  const stationSilhouettes=objects.filter(o=>!detailed(o)).map(o=>({...o,tileId:objectTileIds.get(o.id),y:GROUND_TOP+.42*o.scale,sx:o.scale,sy:o.scale,sz:o.scale}));
  const foliage=items('tree',1.1);
  const flowers=objects.filter(o=>o.kind==='flower');
  const petals=flowers.flatMap(o=>[0,1,2,3,4].map(i=>({x:o.x+Math.cos(i*Math.PI*.4)*.19*o.scale,z:o.z+Math.sin(i*Math.PI*.4)*.19*o.scale,y:GROUND_TOP+.34*o.scale,sx:o.scale,sy:o.scale*.4,sz:o.scale,color:o.color})));
  return <group name="逐个指定的景物">
    <Instances items={trunks}><cylinderGeometry args={[.07,.11,.8,6]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={foliage}><dodecahedronGeometry args={[.72,1]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={foliage.map(o=>({...o,x:o.x-.27*o.sx,z:o.z+.19*o.sx,y:o.y-.18*o.sx,sx:o.sx*.65,sy:o.sy*.7,sz:o.sz*.65}))}><dodecahedronGeometry args={[.72,0]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={items('pine',1.15)}><coneGeometry args={[.7,1.9,7]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={items('rock',.23)}><dodecahedronGeometry args={[.4,0]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={items('flower',.13).map(o=>({...o,color:'#6c9161'}))}><cylinderGeometry args={[.03,.035,.26,5]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={items('flower',.045).map(o=>({...o,color:'#cbb68b'}))}><cylinderGeometry args={[.45,.5,.09,8]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={petals}><sphereGeometry args={[.17,6,4]}/><meshStandardMaterial roughness={1}/></Instances>
    <Instances items={items('flower',.35)}><sphereGeometry args={[.1,6,4]}/><meshStandardMaterial color="#e6bd68" roughness={1}/></Instances>
    <Instances items={stationSilhouettes}><boxGeometry args={[1.1,.84,1.1]}/><meshStandardMaterial roughness={1}/></Instances>
    {objects.filter(o=>!['tree','pine','rock','flower'].includes(o.kind)&&detailed(o)).map(o=><group key={o.id} name={o.id} userData={{tileId:objectTileIds.get(o.id)}} position={[o.x,GROUND_TOP,o.z]} rotation={[0,o.rotation,0]} scale={o.scale}><Landmark o={o}/></group>)}
  </group>;
}
