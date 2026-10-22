import { worldForMap } from '../../core/level-data.js';
import { addAfterEffect, Canvas, useFrame, useThree } from "@react-three/fiber";
import { Component, Suspense, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type MutableRefObject, type CSSProperties } from "react";
import * as THREE from "three";
import type { GameState } from "../../core/game.js";
import { RentTransfer } from "./RentTransfer.js";
import { OutcomeCelebration } from "./OutcomeCelebration.js";
import type { OutcomeCue } from "../outcomes.js";
import type { RentCue } from "../presentation.js";
import { Mascot, type MotionCue } from "./Mascot.js";
import { LimeGarden } from "./LimeGarden.js";
import { MiniatureTown } from "./MiniatureTown.js";
import { cameraFrame, type ViewportInsets } from "./camera-layout.js";
import { ACTOR_ANCHOR_Y, anchorsForMap, positionForTile } from "./layout.js";

import { ContinuousGround } from './ContinuousGround.js';
import { worldView, CAMERA_ELEVATION, clampWorldZoom, type WorldView } from './world-view.js';
import { useWorldNavigation, initialNavigation, type ContextRequest, type Navigation } from './world-navigation.js';
import { mapProjectionBounds, screenToGround } from './camera-math.js';
import { WorldInspection } from './WorldInspection.js';
import type { InspectionRequest } from './map-picking.js';
import { WorldNavigation } from './WorldNavigation.js';
import { tileIdForHit } from './map-picking.js';
import { MapContextMenu } from './MapContextMenu.js';
import { chooseRenderBudget, renderPixelRatio, type RenderBudget } from './render-budget.js';
import './world-navigation.css';

type WorldCanvasProps = Readonly<{
  game: GameState;
  selectedTileId?: number | null;
  motion: MotionCue | null;
  dieValue: number | null;
  dieNonce: number;
  reducedMotion: boolean;
  followCurrent: boolean;
  onFollowCurrentChange?: (follow:boolean)=>void;
  rent: RentCue | null;
  outcome?: OutcomeCue | null;
  pendingBankruptIds?: readonly string[];
  paused?: boolean;
  viewportInsets?: ViewportInsets;
  onConstructionBusyChange?: (busy:boolean)=>void;
  onInspectingChange?: (busy:boolean)=>void;
  onMotionComplete: () => void;
  onActorStep: (tileId: number) => void;
  onSelectTile?: (tileId: number) => void;
  onReadyChange?: (ready: boolean) => void;
}>;

function SceneReadiness({onReady,onBudget,nativeDpr,nav}:{onReady:()=>void;onBudget:(budget:RenderBudget)=>RenderBudget;nativeDpr:number;nav:MutableRefObject<Navigation>}):null {
  const {gl,invalidate,scene,camera}=useThree();
  const complete=useRef(false);
  // R3F decides whether to keep its demand loop before after-effects execute.
  // Request warm-up frames inside useFrame so reduced motion cannot stall it.
  useFrame(()=>{if(!complete.current)invalidate();});
  useEffect(()=>{
    complete.current=false;
    let previousFrame=gl.info.render.frame,previousAt:number|null=null,draws=0,settled=0;
    let decision:RenderBudget|null=null;
    const samples:number[]=[];
    const unsubscribe=addAfterEffect(timestamp=>{
      if(gl.info.render.frame===previousFrame)return;
      previousFrame=gl.info.render.frame;draws++;
      const elapsed=previousAt===null?0:timestamp-previousAt;previousAt=timestamp;
      if(!decision){
        // Initial camera-aligned uploads are cold frames, not steady rendering.
        if(draws>2)samples.push(elapsed);
        const candidate=chooseRenderBudget(samples);
        if(candidate)decision=onBudget(candidate);
        invalidate(2);return;
      }
      const light=scene.children.find(object=>object instanceof THREE.DirectionalLight) as THREE.DirectionalLight|undefined;
      const ratio=renderPixelRatio(decision.mode,(camera as THREE.OrthographicCamera).zoom,nav.current.actualElevation,nativeDpr);
      if(light?.shadow.map?.width!==decision.shadowSize||Math.abs(gl.getPixelRatio()-ratio)>.001){settled=0;invalidate(2);return;}
      if(++settled<2){invalidate(2);return;}
      complete.current=true;unsubscribe();onReady();
    });
    invalidate(2);
    return unsubscribe;
  },[gl,invalidate,scene,camera,onReady,onBudget,nativeDpr,nav]);
  return null;
}

function SceneResolution({mode,nativeDpr,onChange,nav}:{mode:RenderBudget['mode'];nativeDpr:number;onChange:(ratio:number)=>void;nav:MutableRefObject<Navigation>}):null {
  const {camera}=useThree();
  const last=useRef(0);
  useFrame(()=>{
    const ratio=renderPixelRatio(mode,(camera as THREE.OrthographicCamera).zoom,nav.current.actualElevation,nativeDpr);
    if(ratio!==last.current){last.current=ratio;onChange(ratio);}
  },-2.5);
  return null;
}

class RendererUnavailable extends Error {}

class RendererBoundary extends Component<{children:React.ReactNode;fallback:React.ReactNode},{failure:unknown}> {
  state:{failure:unknown}={failure:null};
  static getDerivedStateFromError(failure:unknown):{failure:unknown}{return {failure};}
  render():React.ReactNode {
    if(this.state.failure!==null){
      if(!(this.state.failure instanceof RendererUnavailable))throw this.state.failure;
      return this.props.fallback;
    }
    return this.props.children;
  }
}

function FallbackContent({game,onSelectTile}:Pick<WorldCanvasProps,'game'|'onSelectTile'>):React.JSX.Element {
  return <div className="scene-error" role="status">
    <strong>当前浏览器无法建立 3D 场景</strong>
    <span>仍可从下方列表查看地块，并使用原有回合操作继续游戏。</span>
    <div className="scene-fallback-grid">{game.tiles.map(tile=><button key={tile.id} type="button" onClick={()=>onSelectTile?.(tile.id)}>{tile.id+1} · {tile.title}</button>)}</div>
  </div>;
}

function OperationalFallback({onReady,motion,onActorStep,onMotionComplete,children}:{onReady:()=>void;children:React.ReactNode}&Pick<WorldCanvasProps,'motion'|'onActorStep'|'onMotionComplete'>):React.JSX.Element {
  useEffect(onReady,[onReady]);
  // Without a renderer there is no actor frame callback to release arrival UI.
  useEffect(()=>{
    if(!motion?.path.length)return;
    onActorStep(motion.path[motion.path.length-1]);onMotionComplete();
  },[motion,onActorStep,onMotionComplete]);
  return <>{children}</>;
}

function CameraRig({target,reducedMotion,insets,map,nav,onView,changed,onContext,onInspect,playerId}:{
  target:THREE.Vector3;reducedMotion:boolean;insets?:ViewportInsets;map:GameState['map'];
  nav:MutableRefObject<Navigation>;onView:(view:WorldView)=>void;changed:()=>void;
  onContext:(request:ContextRequest)=>void;
  onInspect:(request:InspectionRequest|null)=>void;playerId:string;
}):null {
  const {camera,size,invalidate}=useThree();
  const initialized=useRef(false),lastRegion=useRef('');
  const look=useMemo(()=>new THREE.Vector3(),[]);
  const logical=useMemo(()=>new THREE.Vector3(),[]);
  const direction=useMemo(()=>new THREE.Vector3(Math.cos(CAMERA_ELEVATION)/Math.SQRT2,Math.sin(CAMERA_ELEVATION),Math.cos(CAMERA_ELEVATION)/Math.SQRT2),[]);
  const right=useMemo(()=>new THREE.Vector3(1,0,-1).normalize(),[]);
  useWorldNavigation(nav,changed,onContext,onInspect,{kind:'player',playerId});
  useFrame((_,delta)=>{
    if(!(camera instanceof THREE.OrthographicCamera))return;
    const n=nav.current;
    const blend=reducedMotion||!initialized.current?1:1-Math.exp(-8*Math.min(delta,.1));
    n.actualYaw=THREE.MathUtils.lerp(n.actualYaw,n.yaw,blend);
    n.actualElevation=THREE.MathUtils.lerp(n.actualElevation,n.elevation,blend);
    const yaw=n.actualYaw,elevation=n.actualElevation,bounds=mapProjectionBounds(map,yaw);
    direction.set(Math.sin(yaw)*Math.cos(elevation),Math.sin(elevation),Math.cos(yaw)*Math.cos(elevation));
    right.set(Math.cos(yaw),0,-Math.sin(yaw));
    const safe=insets?{...insets,right:Math.max(insets.right,70)}:undefined;
    const overview=cameraFrame(size,safe,bounds,elevation);
    n.overviewZoom=Math.min(overview.zoom,64);
    const follow=cameraFrame(size,safe,size.width<=600?{width:7,depth:5}:{width:11,depth:9},elevation);
    const zoom=n.zoom===null?clampWorldZoom(n.mode==='follow'?Math.min(follow.zoom,64):overview.zoom,n.overviewZoom):Math.max(.05,Math.min(96,n.zoom));
    const center=n.mode==='browse'&&n.center?n.center:n.mode==='follow'?target:{x:0,z:0};
    const limitX=bounds.width/2+8,limitZ=bounds.depth/2+8;
    camera.zoom=THREE.MathUtils.lerp(camera.zoom,zoom,blend);
    const targetX=Math.max(-limitX,Math.min(limitX,center.x)),targetZ=Math.max(-limitZ,Math.min(limitZ,center.z));
    if(n.mode==='browse')n.center={x:targetX,z:targetZ};
    logical.lerp(new THREE.Vector3(targetX,.3,targetZ),blend);
    look.copy(logical).addScaledVector(right,-overview.offsetX/camera.zoom);
    const groundOffset=screenToGround({x:0,y:overview.offsetY/camera.zoom},yaw,elevation);
    look.x+=groundOffset.x;look.z+=groundOffset.z;
    const v=worldView({x:look.x,z:look.z},camera.zoom,size,yaw,elevation);
    camera.position.copy(look).addScaledVector(direction,v.distance);
    camera.near=.1;camera.far=v.far;camera.lookAt(look);camera.updateProjectionMatrix();
    n.actualCenter={x:logical.x,z:logical.z};n.actualZoom=camera.zoom;
    // Chunk-aligned buffers include every newly visible property during a pan.
    const minX=Math.floor(v.minX/16)*16,maxX=Math.ceil(v.maxX/16)*16;
    const minZ=Math.floor(v.minZ/16)*16,maxZ=Math.ceil(v.maxZ/16)*16;
    const key=[minX,maxX,minZ,maxZ,v.zoom>=17].join('/');
    if(lastRegion.current!==key){lastRegion.current=key;onView({...v,minX,maxX,minZ,maxZ});}
    const element=_.gl.domElement.closest<HTMLElement>('.canvas-shell');
    if(element){
      const hw=(size.width-(safe?.left??0)-(safe?.right??0))/2/camera.zoom;
      const hh=(size.height-(safe?.top??0)-(safe?.bottom??0))/2/camera.zoom;
      const points=[[-hw,-hh],[hw,-hh],[hw,hh],[-hw,hh]].map(([x,y])=>{const p=screenToGround({x,y},yaw,elevation);return `${logical.x+p.x},${logical.z+p.z}`;}).join(' ');
      element.querySelector('[data-world-viewport]')?.setAttribute('points',points);
      element.dataset.cameraInsets=JSON.stringify(safe??{top:0,right:0,bottom:0,left:0});element.dataset.cameraMode=n.mode;element.dataset.cameraZoom=camera.zoom.toFixed(2);element.dataset.cameraCenter=`${logical.x.toFixed(2)},${logical.z.toFixed(2)}`;
      element.dataset.cameraYaw=yaw.toFixed(6);element.dataset.cameraElevation=elevation.toFixed(6);
      element.dataset.cameraProjection=JSON.stringify({zoom:camera.zoom,x:logical.x,z:logical.z,yaw,elevation});
      const arrow=element.querySelector<HTMLElement>('[data-compass-arrow]');if(arrow)arrow.style.transform=`rotate(${yaw}rad)`;
    }
    if(Math.abs(camera.zoom-zoom)>.01||Math.hypot(logical.x-targetX,logical.z-targetZ)>.01||Math.abs(n.actualYaw-n.yaw)>.0001||Math.abs(n.actualElevation-n.elevation)>.0001)invalidate();
    initialized.current=true;
  },-3);
  return null;
}

function WorldLighting({nav,shadowSize}:{nav:MutableRefObject<Navigation>;shadowSize:number}):React.JSX.Element{
  const light=useRef<THREE.DirectionalLight>(null);
  const target=useMemo(()=>new THREE.Object3D(),[]);
  const {scene,size,camera,gl,clock}=useThree();
  const lastStats=useRef(-1);
  useFrame(()=>{
    if(!light.current||!(camera instanceof THREE.OrthographicCamera))return;
    const direction=new THREE.Vector3();camera.getWorldDirection(direction);
    const n=nav.current;
    const center=camera.position.clone().addScaledVector(direction,worldView(n.actualCenter,camera.zoom,size,n.actualYaw,n.actualElevation).distance);
    const view=worldView({x:center.x,z:center.z},camera.zoom,size,n.actualYaw,n.actualElevation);
    const radius=view.shadowRadius,texel=radius*2/light.current.shadow.mapSize.width;
    center.x=Math.round(center.x/texel)*texel;center.z=Math.round(center.z/texel)*texel;center.y=0;
    target.position.copy(center);target.updateMatrixWorld();
    light.current.position.copy(center).add(new THREE.Vector3(-.43,.8,.4).normalize().multiplyScalar(radius*2.5+20));
    const shadow=light.current.shadow;
    Object.assign(shadow.camera,{left:-radius,right:radius,top:radius,bottom:-radius,near:1,far:radius*5+60});
    shadow.camera.updateProjectionMatrix();
    shadow.normalBias=Math.max(.018,texel*1.15);shadow.bias=-.0001;
    if(scene.fog instanceof THREE.Fog){scene.fog.near=view.fogNear;scene.fog.far=view.fogFar;}
    if(clock.elapsedTime-lastStats.current>.5){
      const element=gl.domElement.closest<HTMLElement>('.canvas-shell');
      if(element)element.dataset.renderStats=JSON.stringify({calls:gl.info.render.calls,triangles:gl.info.render.triangles,geometries:gl.info.memory.geometries,textures:gl.info.memory.textures,programs:gl.info.programs?.length,pixelRatio:gl.getPixelRatio(),shadowType:gl.shadowMap.type,shadowSize:light.current.shadow.mapSize.width});
      lastStats.current=clock.elapsedTime;
    }
    // Central policy also covers meshes mounted later by chunks/LOD/outcomes.
    scene.traverse(object=>{if(object instanceof THREE.Mesh){object.castShadow=true;object.receiveShadow=true;}});
  },-1);
  return <>
    <ambientLight intensity={.7} color="#f3f4dc"/>
    <hemisphereLight args={['#f8fae9','#779566',.8]}/>
    <primitive object={target}/>
    <directionalLight ref={light} target={target} intensity={2.15} color="#fff0d0" castShadow shadow-mapSize-width={shadowSize} shadow-mapSize-height={shadowSize} shadow-intensity={.48} shadow-radius={2}/>
  </>;
}

function Scene(props: WorldCanvasProps & {shadowSize:number;nav:MutableRefObject<Navigation>;changed:()=>void;navigationRevision:number;onContext:(request:ContextRequest)=>void;onInspect:(request:InspectionRequest|null)=>void}): React.JSX.Element {
  const [view,setView]=useState(()=>worldView({x:0,z:0},32,{width:1280,height:720}));
  const invalidate = useThree((state) => state.invalidate);
  const scene = useThree((state) => state.scene);
  useLayoutEffect(() => {
    // Three.js does not inherit shadow flags from parent groups. Apply one
    // scene-wide rule so height, mesh role, and material never create exceptions.
    scene.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        object.castShadow = true;
        object.receiveShadow = true;
      }
    });
    // Imperative actor/camera targets and useFrame callbacks are not host props;
    // request a demand frame after their layout effects have synchronized them.
    invalidate();
  }, [
    scene,
    invalidate,
    props.game,
    props.motion,
    props.rent,
    props.outcome,
    props.followCurrent,
    props.reducedMotion,
    props.paused,
    props.viewportInsets,
    props.navigationRevision,
  ]);
  const actor = props.game.players[props.game.currentPlayerIndex];
  const focusId =
    props.outcome?.stage === "draw"
      ? null
      : (props.outcome?.actorId ??
        props.motion?.actorId ??
        props.rent?.fromId ??
        actor.id);
  const focusActor =
    props.game.players.find((player) => player.id === focusId) ?? actor;
  const point = positionForTile(focusActor.position, props.game.map);
  const trackedPosition = useMemo(
    () => new THREE.Vector3(point.x, ACTOR_ANCHOR_Y, point.z),
    [],
  );
  return (
    <>
      <color attach="background" args={[worldForMap(props.game.map)?.background??'#b7cd9a']} />
      <fog attach="fog" args={[worldForMap(props.game.map)?.background??'#b7cd9a',100,200]} />
      <WorldLighting nav={props.nav} shadowSize={props.shadowSize}/>
      <CameraRig target={trackedPosition} reducedMotion={props.reducedMotion} insets={props.viewportInsets} map={props.game.map} nav={props.nav} onView={setView} changed={props.changed} onContext={props.onContext} onInspect={props.onInspect} playerId={actor.id}/>
      <group>
      {props.game.map.id==='lime-garden-30'?<LimeGarden onConstructionBusyChange={props.onConstructionBusyChange} reducedMotion={props.reducedMotion} selectedTileId={props.selectedTileId} game={props.game} view={view} nav={props.nav}/>:<>
      <ContinuousGround view={view} map={props.game.map} actor={trackedPosition}/>
      <MiniatureTown selectedTileId={props.selectedTileId} game={props.game} view={view} nav={props.nav}/>
      </>}
      </group>
      {props.game.players.map((player, seat) => (
        <Mascot
          key={player.id}
          id={player.id}
          seat={seat}
          tileId={player.position}
          map={props.game.map}
          active={player.id === focusId}
          bankrupt={player.bankrupt}
          awaitingExit={props.pendingBankruptIds?.includes(player.id) ?? false}
          outcome={props.outcome}
          motion={props.motion}
          reducedMotion={props.reducedMotion}
          onMotionComplete={props.onMotionComplete}
          onStep={props.onActorStep}
          dieValue={props.dieValue}
          dieNonce={props.dieNonce}
          trackedPosition={trackedPosition}
        />
      ))}
      {props.outcome && (
        <OutcomeCelebration
          key={`${props.outcome.stage}-${props.outcome.actorId}-${props.outcome.nonce}`}
          game={props.game}
          cue={props.outcome}
          reducedMotion={props.reducedMotion}
        />
      )}
      {props.rent && (
        <RentTransfer
          game={props.game}
          cue={props.rent}
          reducedMotion={props.reducedMotion}
        />
      )}
    </>
  );
}

export function WorldCanvas(props: WorldCanvasProps): React.JSX.Element {
  const [ready, setReady] = useState(false);
  const [inspection,setInspection]=useState<InspectionRequest|null>(null);
  const inspectionCallback=useRef(props.onInspectingChange);inspectionCallback.current=props.onInspectingChange;
  const inspect=useCallback((request:InspectionRequest|null)=>{if(request)inspectionCallback.current?.(true);setInspection(request);},[]);
  useEffect(()=>{inspect(null);},[props.game.revision,props.game.map.id,props.paused,props.motion?.nonce,inspect]);
  const nativeDpr=Math.max(1,Math.min(2,window.devicePixelRatio));
  const [pixelRatio,setPixelRatio]=useState(nativeDpr);
  const [budget,setBudget]=useState<RenderBudget|null>(null);
  const chosenBudget=useRef<RenderBudget|null>(null);
  const applyBudget=useCallback((candidate:RenderBudget):RenderBudget=>{
    const chosen=chosenBudget.current?.mode==='efficient'?chosenBudget.current:candidate;
    chosenBudget.current=chosen;setBudget(chosen);return chosen;
  },[]);
  const markReady=useCallback(()=>setReady(true),[]);
  useLayoutEffect(()=>{setReady(false);},[props.game.map.id,props.game.map.version]);
  useLayoutEffect(()=>{props.onReadyChange?.(ready);},[ready,props.onReadyChange]);
  const [navigationRevision,setNavigationRevision]=useState(0);
  const nav=useRef<Navigation>(initialNavigation(props.followCurrent));
  const [context,setContext]=useState<ContextRequest|null>(null);
  useEffect(()=>{inspectionCallback.current?.(inspection!==null||context!==null);},[inspection,context]);
  const shell=useRef<HTMLDivElement>(null);
  const canOpenContext=!props.paused&&!props.motion&&!props.rent&&!props.outcome;
  const openContext=useCallback((request:ContextRequest)=>{if(canOpenContext){inspectionCallback.current?.(true);setContext(request);}},[canOpenContext]);
  useEffect(()=>{setContext(null);},[props.game.map.id,props.game.currentPlayerIndex,canOpenContext]);
  const appliedFollow=useRef(props.followCurrent);
  const onFollowChange=useRef(props.onFollowCurrentChange);onFollowChange.current=props.onFollowCurrentChange;
  const changed=useCallback(()=>{
    const following=nav.current.mode==='follow';
    if(appliedFollow.current!==following){appliedFollow.current=following;onFollowChange.current?.(following);}
    setNavigationRevision(n=>n+1);
  },[]);
  useEffect(()=>{
    if(appliedFollow.current===props.followCurrent)return;
    appliedFollow.current=props.followCurrent;
    Object.assign(nav.current,{mode:props.followCurrent?'follow':'overview',center:null,zoom:null});
    setNavigationRevision(n=>n+1);
  },[props.followCurrent]);
  useEffect(()=>{
    Object.assign(nav.current,{mode:props.followCurrent?'follow':'overview',center:null,zoom:null});
    setNavigationRevision(n=>n+1);
  },[props.game.map.id,props.game.map.version]);
  // 弹窗可暂停已就绪的场景；批量模拟替换出的新场景仍须先完成上传与暖帧，避免永久卡在加载中。
  const frameLoop = !ready
    ? "demand"
    : props.paused
    ? "never"
    : props.reducedMotion && !props.motion && !props.rent && !props.outcome
      ? "demand"
      : "always";
  return (
    <div
      className="canvas-shell"
      ref={shell}
      style={{'--world-safe-top':`${props.viewportInsets?.top??80}px`,'--world-safe-right':`${props.viewportInsets?.right??20}px` } as CSSProperties}
      onClickCapture={event=>{if(event.target instanceof HTMLCanvasElement&&performance.now()<nav.current.draggedUntil){event.preventDefault();event.stopPropagation();}}}
      data-ready={String(ready)}
      data-render-budget={budget?JSON.stringify(budget):undefined}
      data-frameloop={frameLoop}
      data-show-numbers={String(nav.current.showNumbers)}
      data-safe-insets={
        props.viewportInsets ? JSON.stringify(props.viewportInsets) : undefined
      }
    >
      {!ready && (
        <div className="scene-loading" role="status">
          <span />
          正在搭建棋盘…
        </div>
      )}
      <RendererBoundary fallback={<OperationalFallback key={`${props.game.map.id}/${props.game.map.version}`} onReady={markReady} motion={props.motion} onActorStep={props.onActorStep} onMotionComplete={props.onMotionComplete}><FallbackContent game={props.game} onSelectTile={props.onSelectTile}/></OperationalFallback>}>
      <Canvas
        aria-label="大富翁 2026 3D 棋盘"
        data-testid="world-canvas"
        orthographic
        frameloop={frameLoop}
        shadows={{type:THREE.PCFShadowMap}}
        dpr={pixelRatio}
        camera={{ position: [10.2, 12.5, 10.2], zoom: 48, near: 0.1, far: 80 }}
        gl={canvas=>{
          try{return new THREE.WebGLRenderer({canvas,antialias:true,alpha:false,powerPreference:'high-performance'});}
          catch(cause){throw new RendererUnavailable('无法创建三维绘图环境',{cause});}
        }}
        fallback={<FallbackContent game={props.game} onSelectTile={props.onSelectTile}/>}
      >
        <Suspense fallback={null}>
          <Scene {...props} shadowSize={budget?.shadowSize??2048} nav={nav} changed={changed} navigationRevision={navigationRevision} onContext={openContext} onInspect={inspect}/>
          <SceneResolution mode={budget?.mode??'full'} nativeDpr={nativeDpr} onChange={setPixelRatio} nav={nav}/>
          <SceneReadiness key={`${props.game.map.id}/${props.game.map.version}`} onReady={markReady} onBudget={applyBudget} nativeDpr={nativeDpr} nav={nav}/>
        </Suspense>
      </Canvas>
      </RendererBoundary>
      <WorldNavigation game={props.game} nav={nav} changed={changed} disabled={props.paused??false}/>
      {inspection&&!props.paused&&<WorldInspection game={props.game} request={inspection}/>}
      {context&&canOpenContext&&<MapContextMenu game={props.game} request={context} nav={nav} changed={changed} onSelect={props.onSelectTile} onClose={()=>setContext(null)} canvas={()=>shell.current?.querySelector('canvas')??null}/>}
    </div>
  );
}
