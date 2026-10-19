import { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import type { GameMap } from '../../core/types.js';
import { anchorsForMap, labelForTile, ROAD_TILE_TOP } from './layout.js';
import type { WorldView } from './world-view.js';
import { Instances } from './Instances.js';

/** One atlas and one draw for legible local tile numbers; no hundreds of DOM labels. */
export function RoadLabels({map,view}:{map:GameMap;view:WorldView}):React.JSX.Element|null{
  const columns=Math.ceil(Math.sqrt(map.cells.length));
  const atlas=useMemo(()=>{
    const canvas=document.createElement('canvas');canvas.width=canvas.height=columns*64;
    const ctx=canvas.getContext('2d');
    if(ctx){
      ctx.font='600 42px "PingFang SC",sans-serif';ctx.fillStyle='#68816c';ctx.textAlign='center';ctx.textBaseline='middle';
      map.cells.forEach((_,i)=>ctx.fillText(String(i+1),(i%columns+.5)*64,(Math.floor(i/columns)+.5)*64));
    }
    const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;
    texture.anisotropy=4;return texture;
  },[map.id,map.cells.length,columns]);
  useEffect(()=>()=>atlas.dispose(),[atlas]);
  const visible=useMemo(()=>anchorsForMap(map).tiles.map((p,id)=>({...p,id})).filter(p=>p.x>=view.minX&&p.x<=view.maxX&&p.z>=view.minZ&&p.z<=view.maxZ),[map,view]);
  const geometry=useMemo(()=>{
    const g=new THREE.PlaneGeometry(.44,.36);g.rotateX(-Math.PI/2);g.rotateY(Math.PI/4);
    const offsets=new Float32Array(visible.length*2);
    visible.forEach((p,i)=>{offsets[i*2]=p.id%columns;offsets[i*2+1]=columns-1-Math.floor(p.id/columns);});
    g.setAttribute('atlasCell',new THREE.InstancedBufferAttribute(offsets,2));return g;
  },[visible,columns]);
  useEffect(()=>()=>geometry.dispose(),[geometry]);
  const labels=useMemo(()=>visible.map(p=>({...labelForTile(p.id,map),y:ROAD_TILE_TOP+.008})),[visible]);
  const shader=(program:THREE.WebGLProgramParametersWithUniforms)=>{
    program.vertexShader='attribute vec2 atlasCell;\n'+program.vertexShader;
    program.vertexShader=program.vertexShader.replace('#include <uv_vertex>',`#include <uv_vertex>\n vMapUv=(vMapUv+atlasCell)/${columns.toFixed(1)};`);
  };
  if(view.zoom<17)return null;
  return <Instances items={labels}><primitive object={geometry} attach="geometry"/><meshStandardMaterial key={columns} customProgramCacheKey={()=>`road-labels-${columns}`} map={atlas} transparent alphaTest={.2} roughness={1} onBeforeCompile={shader}/></Instances>;
}
