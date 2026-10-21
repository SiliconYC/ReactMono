import * as THREE from 'three';
import { useEffect, useMemo } from 'react';
import { Instances } from './Instances.js';
import { TOWN } from './town-kit.js';
import { Block } from './StaticBlocks.js';
export { Block } from './StaticBlocks.js';

function Sign({text,color,width=1,y=1.12,z=.59}:{text:string;color:string;width?:number;y?:number;z?:number}):React.JSX.Element {
  const texture=useMemo(()=>{
    const canvas=document.createElement('canvas');canvas.width=512;canvas.height=128;
    const c=canvas.getContext('2d')!;c.fillStyle=color;c.fillRect(0,0,512,128);
    c.strokeStyle='#e7d3a5';c.lineWidth=5;c.strokeRect(8,8,496,112);
    c.fillStyle='#fff3d5';c.font='bold 70px "PingFang SC", "Microsoft YaHei", sans-serif';c.textAlign='center';c.textBaseline='middle';c.fillText(text,256,69);
    const t=new THREE.CanvasTexture(canvas);t.colorSpace=THREE.SRGBColorSpace;return t;
  },[text,color]);
  useEffect(()=>()=>texture.dispose(),[texture]);
  return <mesh position={[0,y,z]}><planeGeometry args={[width,width/4]}/><meshStandardMaterial map={texture} roughness={.9}/></mesh>;
}
function Window({x,y,z=.493}:{x:number;y:number;z?:number}):React.JSX.Element {
  return <group><Block at={[x,y,z]} size={[.28,.4,.045]}/><Block at={[x,y,z+.03]} size={[.21,.31,.024]} color={TOWN.glass}/><Block at={[x,y,z+.048]} size={[.025,.32,.02]}/><Block at={[x,y-.23,z]} size={[.34,.05,.14]}/></group>;
}
export function BankBuilding():React.JSX.Element {
  return <group name="晴湾银行">
    <Block at={[0,.045,0]} size={[1.75,.09,1.46]} color={TOWN.stone}/>
    <Block at={[0,.7,-.08]} size={[1.42,1.3,1.02]} color={TOWN.wall}/>
    <Block at={[0,.19,-.08]} size={[1.48,.16,1.08]} color="#b9b398"/>
    <Block at={[0,1.39,-.08]} size={[1.68,.13,1.22]} color={TOWN.greenRoof}/>
    <Block at={[0,1.52,-.08]} size={[1.46,.13,1.02]} color={TOWN.trim}/>
    <Block at={[0,1.63,-.08]} size={[1.56,.1,1.12]} color={TOWN.greenRoof}/>
    <Block at={[0,.48,.454]} size={[.32,.7,.04]} color={TOWN.glass}/>
    <Block at={[0,.15,.62]} size={[.68,.09,.28]} color={TOWN.stone}/>
    <Block at={[0,.1,.77]} size={[.84,.07,.18]} color={TOWN.trim}/>
    {[-.58,-.35,.35,.58].map(x=><group key={x}><mesh position={[x,.66,.57]}><cylinderGeometry args={[.055,.07,.99,8]}/><meshStandardMaterial color={TOWN.trim} roughness={.9}/></mesh><Block at={[x,.19,.57]} size={[.17,.1,.17]}/><Block at={[x,1.16,.57]} size={[.16,.08,.16]}/></group>)}
    <Block at={[0,1.25,.57]} size={[1.56,.17,.23]} color={TOWN.greenRoof}/>
    <Sign text="晴湾银行" color="#386b60" width={1.24} y={1.27} z={.696}/>
    <mesh position={[0,1.87,0]} rotation={[Math.PI/2,0,0]}><cylinderGeometry args={[.23,.23,.09,16]}/><meshStandardMaterial color="#e4bd68" roughness={.55} metalness={.15}/></mesh>
    <Block at={[0,1.87,.053]} size={[.04,.25,.02]} color={TOWN.trim}/>
    {[-1,1].map(side=><group key={side}><Block at={[side*.723,.75,-.08]} size={[.025,.58,.58]} color={TOWN.trim}/><Block at={[side*.74,.75,-.08]} size={[.02,.44,.44]} color={TOWN.glass}/></group>)}
  </group>;
}

export function FacilityBuilding({kind,color}:{kind:'clinic'|'shop'|'prison';color:string}):React.JSX.Element {
  const prison=kind==='prison',shop=kind==='shop';
  return <group name={shop?'花园商店':prison?'小镇拘留所':'晴湾医院'}>
    <Block at={[0,.04,0]} size={[1.64,.08,1.36]} color={TOWN.stone}/>
    <Block at={[0,.63,-.08]} size={[1.3,1.16,1]} color={prison?'#c9c9b7':TOWN.wall}/>
    <Block at={[0,.16,-.08]} size={[1.39,.15,1.08]} color="#b8b39b"/>
    <Block at={[0,1.25,-.08]} size={[1.52,.12,1.2]} color={color}/>
    <Block at={[0,1.39,-.08]} size={[1.35,.16,1.04]} color={prison?'#7b8a7d':TOWN.trim}/>
    <Block at={[0,.4,.442]} size={[.3,.62,.045]} color={TOWN.glass}/>
    <Block at={[0,.1,.56]} size={[.52,.09,.24]} color={TOWN.trim}/>
    {[-.44,.44].map(x=><Window key={x} x={x} y={.66} z={.443}/>)}
    {[-1,1].map(side=><Block key={side} at={[side*.66,.68,-.13]} size={[.025,.45,.4]} color={TOWN.glass}/>)}
    <Sign text={shop?'花园商店':prison?'拘留所':'晴湾医院'} color={prison?'#5e746b':shop?'#927352':'#648c83'} width={1.17} y={1.11} z={.53}/>
    {shop?<group>
      {[-.6,-.4,-.2,0,.2,.4,.6].map((x,i)=><group key={x}><mesh position={[x,.91,.64]} rotation={[.28,0,0]}><boxGeometry args={[.2,.07,.55]}/><meshStandardMaterial color={i%2?TOWN.trim:'#c78864'} roughness={1}/></mesh><Block at={[x,.81,.9]} size={[.19,.13,.05]} color={i%2?TOWN.trim:'#c78864'}/></group>)}
      <Block at={[-.47,.26,.68]} size={[.47,.28,.3]} color="#a28a61"/>
      {[-.61,-.45,-.3].map((x,i)=><mesh key={x} position={[x,.46,.68]}><dodecahedronGeometry args={[.1,0]}/><meshStandardMaterial color={i%2?'#deb663':'#c97a62'}/></mesh>)}
    </group>:prison?<group>
      {[-.44,.44].map(x=>[-.08,0,.08].map(dx=><Block key={`${x}/${dx}`} at={[x+dx,.66,.487]} size={[.026,.33,.03]} color="#5a7066"/>))}
      {[-.66,.66].map(x=><group key={x}><Block at={[x,1.46,-.33]} size={[.29,.4,.36]} color="#a8b3a4"/><Block at={[x,1.69,-.33]} size={[.36,.08,.43]} color="#657b71"/><Block at={[x,1.49,-.14]} size={[.13,.1,.03]} color={TOWN.glass}/></group>)}
      <Block at={[0,1.51,.27]} size={[.37,.13,.06]} color="#e2c78c"/>
    </group>:<group>
      <Block at={[0,1.61,.04]} size={[.58,.43,.18]}/>
      <Block at={[0,1.61,.143]} size={[.36,.1,.035]} color="#bb715f"/>
      <Block at={[0,1.61,.143]} size={[.1,.31,.036]} color="#bb715f"/>
      {[-.63,.63].map(x=><Block key={x} at={[x,.45,.6]} size={[.065,.7,.065]} color="#78988d"/>)}
      <Block at={[0,.86,.62]} size={[1.46,.1,.47]} color="#86aaa0"/>
    </group>}
  </group>;
}

export function ClockTower():React.JSX.Element {
  return <group name="花街四面钟楼">
    <mesh position={[0,.04,0]}><cylinderGeometry args={[1.8,1.85,.08,12]}/><meshStandardMaterial color="#c8c5ac" roughness={1}/></mesh>
    <mesh position={[0,.1,0]}><cylinderGeometry args={[1.32,1.45,.12,8]}/><meshStandardMaterial color="#e2d4b2" roughness={1}/></mesh>
    <Block at={[0,.24,0]} size={[1.54,.25,1.54]} color={TOWN.stone}/>
    <Block at={[0,1.47,0]} size={[1.15,2.3,1.15]} color="#efd8a3"/>
    {[0,Math.PI/2,Math.PI,-Math.PI/2].map(angle=><group key={angle} rotation={[0,angle,0]}>
      <Block at={[0,.85,.587]} size={[.29,.64,.04]} color={TOWN.glass}/>
      {[-.53,.53].map(x=><Block key={x} at={[x,1.38,.59]} size={[.1,1.98,.065]} color={TOWN.trim}/>)}
      <mesh position={[0,2.03,.59]} rotation={[Math.PI/2,0,0]}><cylinderGeometry args={[.39,.39,.05,24]}/><meshStandardMaterial color="#8b805f" roughness={.8}/></mesh>
      <mesh position={[0,2.03,.622]}><circleGeometry args={[.335,24]}/><meshStandardMaterial color="#fff3cf" roughness={.9}/></mesh>

      <Block at={[0,2.12,.642]} size={[.035,.2,.023]} color="#526d62"/>
      <mesh position={[-.075,1.99,.642]} rotation={[0,0,-1.05]}><boxGeometry args={[.03,.2,.026]}/><meshStandardMaterial color="#526d62"/></mesh>
    </group>)}
    <Instances items={[0,Math.PI/2,Math.PI,-Math.PI/2].flatMap(angle=>Array.from({length:12},(_,i)=>{
      const x=Math.sin(i*Math.PI/6)*.276,z=.628;
      return {x:Math.cos(angle)*x+Math.sin(angle)*z,y:2.03+Math.cos(i*Math.PI/6)*.276,z:-Math.sin(angle)*x+Math.cos(angle)*z};
    }))}><sphereGeometry args={[.021,5,3]}/><meshStandardMaterial color="#796d50" roughness={1}/></Instances>
    <Block at={[0,1.49,0]} size={[1.24,.09,1.24]} color={TOWN.trim}/>
    <Block at={[0,2.66,0]} size={[1.45,.15,1.45]} color={TOWN.trim}/>
    <mesh position={[0,3.04,0]} rotation={[0,Math.PI/4,0]}><coneGeometry args={[1.1,.68,4]}/><meshStandardMaterial color={TOWN.roof} roughness={.9}/></mesh>
    <mesh position={[0,3.48,0]}><sphereGeometry args={[.12,8,6]}/><meshStandardMaterial color="#dcbb72" roughness={.6}/></mesh>
  </group>;
}
