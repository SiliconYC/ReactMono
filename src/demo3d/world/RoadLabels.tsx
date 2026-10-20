import { useEffect, useLayoutEffect, useMemo, useRef, type MutableRefObject } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import type { GameMap } from '../../core/types.js';
import { anchorsForMap, ROAD_TILE_TOP } from './layout.js';
import { labelPose } from './camera-math.js';
import type { WorldView } from './world-view.js';
import type { Navigation } from './world-navigation.js';

export function RoadLabels({map,view,nav}:{map:GameMap;view:WorldView;nav:MutableRefObject<Navigation>}):React.JSX.Element|null{
  const mesh=useRef<THREE.InstancedMesh>(null),lastPose=useRef('');
  const gl=useThree(s=>s.gl);
  const transform=useMemo(()=>new THREE.Object3D(),[]);
  const columns=Math.ceil(Math.sqrt(map.cells.length));
  const atlas=useMemo(()=>{
    const canvas=document.createElement('canvas');canvas.width=canvas.height=columns*64;
    const ctx=canvas.getContext('2d');
    if(ctx){
      ctx.font='600 42px "PingFang SC",sans-serif';ctx.fillStyle='#48624f';ctx.textAlign='center';ctx.textBaseline='middle';
      map.cells.forEach((_,i)=>ctx.fillText(String(i+1),(i%columns+.5)*64,(Math.floor(i/columns)+.5)*64));
    }
    const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;
    texture.anisotropy=4;return texture;
  },[map.id,map.cells.length,columns]);
  useEffect(()=>()=>atlas.dispose(),[atlas]);
  const visible=useMemo(()=>anchorsForMap(map).tiles.map((p,id)=>({...p,id})).filter(p=>p.x>=view.minX&&p.x<=view.maxX&&p.z>=view.minZ&&p.z<=view.maxZ),[map,view]);
  const geometry=useMemo(()=>{
    const g=new THREE.PlaneGeometry(.44,.36);g.rotateX(-Math.PI/2);
    const offsets=new Float32Array(visible.length*2);
    visible.forEach((p,i)=>{offsets[i*2]=p.id%columns;offsets[i*2+1]=columns-1-Math.floor(p.id/columns);});
    g.setAttribute('atlasCell',new THREE.InstancedBufferAttribute(offsets,2));return g;
  },[visible,columns]);
  useEffect(()=>()=>geometry.dispose(),[geometry]);
  useLayoutEffect(()=>{lastPose.current='';},[visible,nav.current.showNumbers]);
  useLayoutEffect(()=>{
    const root=gl.domElement.closest<HTMLElement>('.canvas-shell');
    if(root)root.dataset.visibleRoadLabels=String(view.zoom>=17&&nav.current.showNumbers?visible.length:0);
  },[gl,view.zoom,visible,nav.current.showNumbers]);
  useFrame(()=>{
    const instance=mesh.current;if(!instance)return;
    const n=nav.current,key=`${n.actualYaw}/${n.actualElevation}`;if(lastPose.current===key)return;
    const pose=labelPose(n.actualYaw,n.actualElevation);
    visible.forEach((p,i)=>{
      transform.position.set(p.x+pose.x,ROAD_TILE_TOP+.008,p.z+pose.z);
      transform.rotation.set(0,pose.rotation,0);transform.scale.set(1,1,pose.scaleZ);transform.updateMatrix();instance.setMatrixAt(i,transform.matrix);
    });
    instance.instanceMatrix.needsUpdate=true;instance.computeBoundingSphere();lastPose.current=key;
    const root=gl.domElement.closest<HTMLElement>('.canvas-shell'),matrix=instance.instanceMatrix.array;
    if(root&&visible.length){root.dataset.labelYaw=String(Math.atan2(matrix[8],matrix[10]));root.dataset.labelScaleZ=String(Math.hypot(matrix[8],matrix[10]));}
  },-2);
  const shader=(program:THREE.WebGLProgramParametersWithUniforms)=>{
    program.vertexShader='attribute vec2 atlasCell;\n'+program.vertexShader;
    program.vertexShader=program.vertexShader.replace('#include <uv_vertex>',`#include <uv_vertex>\n vMapUv=(vMapUv+atlasCell)/${columns.toFixed(1)};`);
  };
  if(view.zoom<17||!nav.current.showNumbers)return null;
  return <instancedMesh ref={mesh} args={[geometry,undefined,visible.length]} userData={{roadLabels:true}}>
    <meshStandardMaterial key={columns} customProgramCacheKey={()=>`road-labels-${columns}`} map={atlas} transparent alphaTest={.2} roughness={1} onBeforeCompile={shader}/>
  </instancedMesh>;
}
