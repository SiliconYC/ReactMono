import { useMemo } from 'react';
import * as THREE from 'three';
import type { GameMap } from '../../core/types.js';
import { GROUND_TOP } from './layout.js';
import { groundChunks, sceneryForChunks, type WorldView } from './world-view.js';
import { Instances } from './Instances.js';

/** Seamless meadow colour in absolute world coordinates; no moving texture or pedestal edge. */
function meadowShader(shader:THREE.WebGLProgramParametersWithUniforms):void{
  shader.vertexShader='varying vec2 meadowPosition;\n'+shader.vertexShader;
  shader.vertexShader=shader.vertexShader.replace('#include <worldpos_vertex>',`#include <worldpos_vertex>
    vec4 meadowWorld=vec4(transformed,1.0);
    #ifdef USE_INSTANCING
      meadowWorld=instanceMatrix*meadowWorld;
    #endif
    meadowPosition=(modelMatrix*meadowWorld).xz;`);
  shader.fragmentShader='varying vec2 meadowPosition;\n'+shader.fragmentShader;
  shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
    float meadowPatch=sin(meadowPosition.x*.16+sin(meadowPosition.y*.12)*1.8)*sin(meadowPosition.y*.11+cos(meadowPosition.x*.07));
    float grain=sin(meadowPosition.x*9.1+meadowPosition.y*3.7)*sin(meadowPosition.y*8.3);
    float detailFade=1.0-smoothstep(.035,.14,length(fwidth(meadowPosition)));
    diffuseColor.rgb*=.97+meadowPatch*.045+grain*.009*detailFade;`);
}
export function ContinuousGround({view,map}:{view:WorldView;map:GameMap}):React.JSX.Element{
  const chunks=useMemo(()=>groundChunks(view),[view]);
  const ground=useMemo(()=>chunks.map(c=>({...c,y:GROUND_TOP-.03})),[chunks]);
  const scenery=useMemo(()=>sceneryForChunks(chunks,map),[chunks,map]);
  const crowns=useMemo(()=>scenery.map(p=>({...p,y:GROUND_TOP+.84*p.scale,sx:p.scale,sy:p.scale*1.14,sz:p.scale,color:p.tone>.5?'#82ac80':'#6e9d79'})),[scenery]);
  const trunks=useMemo(()=>scenery.map(p=>({...p,y:GROUND_TOP+.28*p.scale,sx:p.scale,sy:p.scale,sz:p.scale})),[scenery]);
  return <group name="连续世界地表">
    <Instances items={ground}><boxGeometry args={[16,.06,16]}/><meshStandardMaterial color="#b5ca98" roughness={1} onBeforeCompile={meadowShader}/></Instances>
    <Instances items={trunks}><cylinderGeometry args={[.055,.09,.6,5]}/><meshStandardMaterial color="#a08b63" roughness={1}/></Instances>
    <Instances items={crowns}><dodecahedronGeometry args={[.54,0]}/><meshStandardMaterial roughness={1}/></Instances>
  </group>;
}
