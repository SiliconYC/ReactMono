import { useEffect, useMemo, type MutableRefObject } from 'react';
import * as THREE from 'three';
import { GardenTrees, BluePavilion } from './GardenLandmarks.js';
import { GardenHouses } from './GardenHouses.js';
import { LIME_PROPERTY_BLOCKS, propertyRun } from '../../core/property-groups.js';
import type { GameState } from '../../core/game.js';
import { LEVELS, worldForMap } from '../../core/level-data.js';
import type { WorldDefinition } from '../../core/level-world.js';
import { GROUND_TOP, ROAD_TILE_TOP } from './layout.js';
import { Instances, type Instance } from './Instances.js';
import { RoadLabels } from './RoadLabels.js';
import { gardenOwnerColor, gardenRoadColor } from './lime-garden-ownership.js';
import type { Navigation } from './world-navigation.js';
import type { WorldView } from './world-view.js';

function slabGeometry(width:number,depth:number,radius:number,height:number):THREE.BufferGeometry {
  const x=-width/2,z=-depth/2,s=new THREE.Shape();
  s.moveTo(x+radius,z);s.lineTo(x+width-radius,z);s.quadraticCurveTo(x+width,z,x+width,z+radius);
  s.lineTo(x+width,z+depth-radius);s.quadraticCurveTo(x+width,z+depth,x+width-radius,z+depth);
  s.lineTo(x+radius,z+depth);s.quadraticCurveTo(x,z+depth,x,z+depth-radius);
  s.lineTo(x,z+radius);s.quadraticCurveTo(x,z,x+radius,z);
  const g=new THREE.ExtrudeGeometry(s,{depth:height-.02,bevelEnabled:true,bevelSize:.016,bevelThickness:.01,bevelSegments:3,steps:1,curveSegments:8});
  g.rotateX(-Math.PI/2);g.translate(0,.01,0);return g;
}

function grassTexture():THREE.CanvasTexture {
  const canvas=document.createElement('canvas');canvas.width=canvas.height=512;
  const ctx=canvas.getContext('2d')!;ctx.fillStyle='#bddb59';ctx.fillRect(0,0,512,512);
  let seed=41;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
  for(let i=0;i<16000;i++){
    const x=random()*512,y=random()*512;
    ctx.strokeStyle=['#e1ee8b','#aecd49','#a3c343','#d3e87b'][i%4];ctx.globalAlpha=.38+random()*.3;ctx.lineWidth=.6+random()*.65;
    ctx.beginPath();ctx.moveTo(x,y);ctx.quadraticCurveTo(x+random()*2,y-2,x+random()*2-1,y-3-random()*5);ctx.stroke();
  }
  const texture=new THREE.CanvasTexture(canvas);texture.wrapS=texture.wrapT=THREE.RepeatWrapping;
  texture.repeat.set(2500,2500);texture.colorSpace=THREE.SRGBColorSpace;texture.anisotropy=8;return texture;
}

function GardenGround():React.JSX.Element {
  const texture=useMemo(grassTexture,[]);useEffect(()=>()=>texture.dispose(),[texture]);
  return <mesh rotation={[-Math.PI/2,0,0]} position={[0,GROUND_TOP-.004,0]}>
    <planeGeometry args={[20000,20000]}/><meshStandardMaterial map={texture} roughness={1}/>
  </mesh>;
}

function RoundBatch({items,geometry,onSelect}:{items:readonly Instance[];geometry:THREE.BufferGeometry;onSelect?:(id:number)=>void}):React.JSX.Element {
  return <Instances items={items} mapTiles={items.every(p=>p.tileId!==undefined)} onSelect={onSelect}>
    <primitive object={geometry} attach="geometry"/><meshStandardMaterial roughness={.65}/>
  </Instances>;
}

function GardenGate({x,z,scale}:{x:number;z:number;scale:number}):React.JSX.Element {
  return <group position={[x,GROUND_TOP,z]} scale={scale} name="春日牌坊">
    {[-.85,.85].map(v=><group key={v} position={[v,0,0]}>
      <mesh position={[0,.08,0]}><boxGeometry args={[.48,.16,.55]}/><meshStandardMaterial color="#c8eafa"/></mesh>
      <mesh position={[0,1.25,0]}><boxGeometry args={[.24,2.4,.3]}/><meshStandardMaterial color="#84c2f5"/></mesh>
    </group>)}
    <mesh position={[0,2.05,0]}><boxGeometry args={[1.8,.36,.22]}/><meshStandardMaterial color="#fae8b6"/></mesh>
    <mesh position={[0,1.1,0]}><boxGeometry args={[1.35,1.8,.12]}/><meshStandardMaterial color="#f0836b"/></mesh>
    {[-.24,.24].map(v=><mesh key={v} position={[v,1.08,.075]}><sphereGeometry args={[.045,12,8]}/><meshStandardMaterial color="#ffe690"/></mesh>)}
    <mesh position={[0,2.42,0]} rotation={[0,Math.PI/4,0]}><coneGeometry args={[1.55,.58,4]}/><meshStandardMaterial color="#519be8"/></mesh>
    <mesh position={[0,2.18,0]}><boxGeometry args={[2.5,.1,.82]}/><meshStandardMaterial color="#8acaf4"/></mesh>
  </group>;
}

function GardenAccents({world,slab}:{world:WorldDefinition;slab:THREE.BufferGeometry}):React.JSX.Element {
  const flowers=world.objects.filter(o=>o.kind==='flower');
  const petals=flowers.flatMap(o=>[0,1,2,3,4].map(k=>({x:o.x+Math.cos(k*Math.PI*.4)*.16*o.scale,y:GROUND_TOP+.11*o.scale,z:o.z+Math.sin(k*Math.PI*.4)*.16*o.scale,sx:.14*o.scale,sy:.055*o.scale,sz:.14*o.scale,color:o.color})));
  return <>
    <Instances items={petals}><sphereGeometry args={[1,12,8]}/><meshStandardMaterial roughness={.7}/></Instances>
    <Instances items={flowers.map(o=>({x:o.x,y:GROUND_TOP+.13*o.scale,z:o.z,sx:o.scale*.095,sy:o.scale*.05,sz:o.scale*.095,color:'#ffc94f'}))}><sphereGeometry args={[1,12,8]}/><meshStandardMaterial roughness={.7}/></Instances>
    {world.objects.filter(o=>o.kind==='bench').map(o=><group key={o.id} position={[o.x,GROUND_TOP,o.z]} rotation={[0,o.rotation,0]} scale={o.scale}>
      <RoundBatch geometry={slab} items={[{x:0,y:.32,z:0,sx:.8,sy:1,sz:.3,color:o.color},{x:0,y:.58,z:-.24,sx:.8,sy:3,sz:.08,color:o.color}]}/>
      <Instances items={[-.5,.5].map(x=>({x,y:.16,z:0,color:'#98bf73'}))}><boxGeometry args={[.07,.32,.45]}/><meshStandardMaterial/></Instances>
    </group>)}
  </>;
}

function tileIcon(game:GameState,id:number):string {
  const tile=game.tiles[id];
  if(id===0)return '↗';
  if(tile.facility==='hospital')return '✚';
  if(tile.facility==='prison')return '☾';
  if(tile.facility==='shop')return '▣';
  if(LEVELS.find(l=>l.map.id===game.map.id)?.cardRules.tileIds.includes(id))return '✉';
  if(LEVELS.find(l=>l.map.id===game.map.id)?.eventRules.tileIds.includes(id))return '✦';
  return '●';
}

function GardenSymbols({game,world}:{game:GameState;world:WorldDefinition}):React.JSX.Element {
  const texture=useMemo(()=>{
    const c=document.createElement('canvas');c.width=1024;c.height=512;const ctx=c.getContext('2d')!;
    ctx.textAlign='center';ctx.textBaseline='middle';
    game.tiles.forEach((t,i)=>{
      const x=(i%8)*128,y=Math.floor(i/8)*128;
      ctx.fillStyle=t.kind==='property'?'#e4b63f':i===0?'#e48b62':['#57a9d4','#8ab64b','#a5a1df'][i%3];
      if(t.kind==='property'){
        for(const [dx,dy,r] of [[0,-5,20],[-18,14,13],[20,16,11]]){ctx.beginPath();ctx.arc(x+64+dx,y+58+dy,r,0,Math.PI*2);ctx.fill();}
        ctx.fillStyle='#ffe58c';ctx.beginPath();ctx.arc(x+58,y+44,6,0,Math.PI*2);ctx.fill();
      }else{ctx.font='bold 66px "PingFang SC",sans-serif';ctx.fillText(tileIcon(game,i),x+64,y+62);}
    });
    const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=4;return t;
  },[game.map.id,game.tiles.map(t=>t.facility).join('/')]);
  useEffect(()=>()=>texture.dispose(),[texture]);
  const geometry=useMemo(()=>{
    const g=new THREE.PlaneGeometry(.88,.88);g.rotateX(-Math.PI/2);
    g.setAttribute('gardenCell',new THREE.InstancedBufferAttribute(new Float32Array(game.tiles.flatMap((_,i)=>[i%8,3-Math.floor(i/8)])),2));return g;
  },[game.map.id]);
  useEffect(()=>()=>geometry.dispose(),[geometry]);
  const shader=(p:THREE.WebGLProgramParametersWithUniforms)=>{
    p.vertexShader='attribute vec2 gardenCell;\n'+p.vertexShader;
    p.vertexShader=p.vertexShader.replace('#include <uv_vertex>','#include <uv_vertex>\n vMapUv=(vMapUv+gardenCell)/vec2(8.0,4.0);');
  };
  return <Instances items={world.tiles.map((t,i)=>({x:t.x,y:ROAD_TILE_TOP+.003,z:t.z,tileId:i}))} mapTiles>
    <primitive object={geometry} attach="geometry"/><meshStandardMaterial map={texture} transparent alphaTest={.3} roughness={.8} onBeforeCompile={shader} customProgramCacheKey={()=>'lime-garden-symbols'}/>
  </Instances>;
}

function GardenProperties({game,world,reducedMotion,onConstructionBusyChange}:{game:GameState;world:WorldDefinition;reducedMotion:boolean;onConstructionBusyChange?:(busy:boolean)=>void}):React.JSX.Element {
  const color=(owner:string|null|undefined)=>gardenOwnerColor(game,owner);
  const properties=game.tiles.filter(t=>t.kind==='property');
  const owned=properties.filter(t=>t.ownerId);
  const paving=LIME_PROPERTY_BLOCKS.flatMap((block,index)=>block.tileIds.map(id=>({x:world.tiles[id].lotX,y:GROUND_TOP+.02,z:world.tiles[id].lotZ,tileId:id,color:['#f3e8bf','#f3d6ba','#e6e7ba','#f1dfb9','#dce6bf','#ecd4bc','#dbe5c6','#f3e8bf'][index]})));
  const dividers=LIME_PROPERTY_BLOCKS.flatMap(block=>block.tileIds.flatMap(id=>{
    const p=world.tiles[id],vertical=p.x!==p.lotX;
    return [-1,1].map(side=>({x:p.lotX+(vertical?0:side*.98),y:GROUND_TOP+.044,z:p.lotZ+(vertical?side*.98:0),sx:vertical?2:.025,sy:.008,sz:vertical?.025:2,color:'#c0be91'}));
  }));
  return <>
    <Instances items={paving} mapTiles><boxGeometry args={[2,.04,2]}/><meshStandardMaterial roughness={.9}/></Instances>
    <Instances items={owned.map(t=>({x:world.tiles[t.id].lotX,y:GROUND_TOP+.046,z:world.tiles[t.id].lotZ,color:color(t.ownerId),tileId:t.id}))} mapTiles>
      <boxGeometry args={[1.94,.012,1.94]}/><meshStandardMaterial roughness={.8}/>
    </Instances>
    <Instances items={dividers}><boxGeometry args={[1,1,1]}/><meshStandardMaterial roughness={.9}/></Instances>
    <Instances items={properties.map(t=>{const p=world.tiles[t.id];return {x:(p.x+p.lotX)/2,y:GROUND_TOP+.015,z:(p.z+p.lotZ)/2,sx:p.x===p.lotX?.5:.44,sz:p.x===p.lotX?.44:.5,color:t.ownerId?color(t.ownerId):'#e4d8ad',tileId:t.id};})} mapTiles>
      <boxGeometry args={[1,.03,1]}/><meshStandardMaterial roughness={.85}/>
    </Instances>
    <GardenHouses game={game} world={world} reducedMotion={reducedMotion} onConstructionBusyChange={onConstructionBusyChange}/>
  </>;
}

/** 探索关卡使用独立表现分支，避免试验材质、模型和路线铺装影响既有关卡。 */
export function LimeGarden({game,view,nav,selectedTileId,onSelectTile,reducedMotion,onConstructionBusyChange}:{game:GameState;view:WorldView;nav:MutableRefObject<Navigation>;selectedTileId?:number|null;onSelectTile?:(id:number)=>void;reducedMotion:boolean;onConstructionBusyChange?:(busy:boolean)=>void}):React.JSX.Element {
  const world=worldForMap(game.map)!;
  const slab=useMemo(()=>slabGeometry(1.74,1.74,.24,.06),[]);useEffect(()=>()=>slab.dispose(),[slab]);
  const pavilion=world.objects.find(o=>o.kind==='gazebo')!,gate=world.objects.find(o=>o.kind==='tower')!;
  const selected=selectedTileId==null?undefined:world.tiles[selectedTileId];
  const selectedRun=selectedTileId==null?[]:propertyRun(game,selectedTileId);
  return <group name="青柠游园独立风格">
    <GardenGround/>
    <RoundBatch geometry={slab} onSelect={onSelectTile} items={world.tiles.map((p,id)=>({x:p.x,y:GROUND_TOP,z:p.z,tileId:id,color:gardenRoadColor(game,id,id===selectedTileId)}))}/>
    <GardenSymbols game={game} world={world}/>
    <GardenProperties game={game} world={world} reducedMotion={reducedMotion} onConstructionBusyChange={onConstructionBusyChange}/>
    {selectedRun.length>0&&<Instances items={selectedRun.map(t=>({x:world.tiles[t.id].lotX,y:GROUND_TOP+.06,z:world.tiles[t.id].lotZ,rx:-Math.PI/2,color:'#ffe88d',tileId:t.id}))} mapTiles><ringGeometry args={[.86,.9,4,1,Math.PI/4]}/><meshStandardMaterial roughness={.8}/></Instances>}
    <GardenTrees world={world}/>
    <BluePavilion x={pavilion.x} z={pavilion.z} scale={pavilion.scale}/>
    <GardenGate x={gate.x} z={gate.z} scale={gate.scale}/>
    <GardenAccents world={world} slab={slab}/>
    <RoadLabels map={game.map} view={view} nav={nav}/>
    {selected&&<Instances items={[{x:selected.x,y:ROAD_TILE_TOP+.014,z:selected.z,rx:-Math.PI/2,color:'#f9ad4b'}]}><torusGeometry args={[.79,.025,6,40]}/><meshStandardMaterial roughness={.6}/></Instances>}
  </group>;
}
