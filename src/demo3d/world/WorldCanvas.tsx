import { worldForMap } from '../../core/level-data.js';
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Suspense, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type MutableRefObject, type CSSProperties } from "react";
import * as THREE from "three";
import type { GameState } from "../../core/game.js";
import { RentTransfer } from "./RentTransfer.js";
import { OutcomeCelebration } from "./OutcomeCelebration.js";
import type { OutcomeCue } from "../outcomes.js";
import type { RentCue } from "../presentation.js";
import { Mascot, type MotionCue } from "./Mascot.js";
import { MiniatureTown } from "./MiniatureTown.js";
import { cameraFrame, type ViewportInsets } from "./camera-layout.js";
import { ACTOR_ANCHOR_Y, anchorsForMap, positionForTile } from "./layout.js";

import { ContinuousGround } from './ContinuousGround.js';
import { worldView, CAMERA_ELEVATION, clampWorldZoom, type WorldView } from './world-view.js';
import { useWorldNavigation, initialNavigation, type ContextRequest, type Navigation } from './world-navigation.js';
import { mapProjectionBounds, screenToGround } from './camera-math.js';
import { WorldNavigation } from './WorldNavigation.js';
import { MapContextMenu } from './MapContextMenu.js';
import './world-navigation.css';

type WorldCanvasProps = Readonly<{
  game: GameState;
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
  onMotionComplete: () => void;
  onActorStep: (tileId: number) => void;
  onSelectTile?: (tileId: number) => void;
}>;

function CameraRig({target,reducedMotion,insets,map,nav,onView,changed,onContext}:{
  target:THREE.Vector3;reducedMotion:boolean;insets?:ViewportInsets;map:GameState['map'];
  nav:MutableRefObject<Navigation>;onView:(view:WorldView)=>void;changed:()=>void;
  onContext:(request:ContextRequest)=>void;
}):null {
  const {camera,size,invalidate}=useThree();
  const initialized=useRef(false),lastRegion=useRef('');
  const look=useMemo(()=>new THREE.Vector3(),[]);
  const logical=useMemo(()=>new THREE.Vector3(),[]);
  const direction=useMemo(()=>new THREE.Vector3(Math.cos(CAMERA_ELEVATION)/Math.SQRT2,Math.sin(CAMERA_ELEVATION),Math.cos(CAMERA_ELEVATION)/Math.SQRT2),[]);
  const right=useMemo(()=>new THREE.Vector3(1,0,-1).normalize(),[]);
  useWorldNavigation(nav,changed,onContext);
  useFrame((_,delta)=>{
    if(!(camera instanceof THREE.OrthographicCamera))return;
    const n=nav.current;
    const blend=reducedMotion||!initialized.current?1:1-Math.exp(-8*Math.min(delta,.1));
    n.actualYaw=THREE.MathUtils.lerp(n.actualYaw,n.yaw,blend);
    n.actualElevation=THREE.MathUtils.lerp(n.actualElevation,n.elevation,blend);
    const yaw=n.actualYaw,elevation=n.actualElevation,bounds=mapProjectionBounds(map,yaw);
    direction.set(Math.sin(yaw)*Math.cos(elevation),Math.sin(elevation),Math.cos(yaw)*Math.cos(elevation));
    right.set(Math.cos(yaw),0,-Math.sin(yaw));
    const phoneOverview=size.width<=600&&n.mode==='overview';
    const safe=insets?{...insets,top:insets.top+(phoneOverview?84:0),right:phoneOverview?insets.right:Math.max(insets.right,size.width<=600?132:202)}:undefined;
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
      const arrow=element.querySelector<HTMLElement>('[data-compass-arrow]');if(arrow)arrow.style.transform=`rotate(${yaw}rad)`;
    }
    if(Math.abs(camera.zoom-zoom)>.01||Math.hypot(logical.x-targetX,logical.z-targetZ)>.01||Math.abs(n.actualYaw-n.yaw)>.0001||Math.abs(n.actualElevation-n.elevation)>.0001)invalidate();
    initialized.current=true;
  },-3);
  return null;
}

function WorldLighting({nav}:{nav:MutableRefObject<Navigation>}):React.JSX.Element{
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
    const radius=view.shadowRadius,texel=radius*2/2048;
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
      if(element)element.dataset.renderStats=JSON.stringify({calls:gl.info.render.calls,triangles:gl.info.render.triangles,geometries:gl.info.memory.geometries,textures:gl.info.memory.textures,programs:gl.info.programs?.length,pixelRatio:gl.getPixelRatio(),shadowType:gl.shadowMap.type});
      lastStats.current=clock.elapsedTime;
    }
    // Central policy also covers meshes mounted later by chunks/LOD/outcomes.
    scene.traverse(object=>{if(object instanceof THREE.Mesh){object.castShadow=true;object.receiveShadow=true;}});
  },-1);
  return <>
    <ambientLight intensity={.95} color="#f3f4dc"/>
    <hemisphereLight args={['#f8fae9','#779566',.85]}/>
    <primitive object={target}/>
    <directionalLight ref={light} target={target} intensity={2.35} color="#fff0d0" castShadow shadow-mapSize-width={2048} shadow-mapSize-height={2048} shadow-intensity={.48} shadow-radius={2}/>
  </>;
}

function Scene(props: WorldCanvasProps & {nav:MutableRefObject<Navigation>;changed:()=>void;navigationRevision:number;onContext:(request:ContextRequest)=>void}): React.JSX.Element {
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
  useLayoutEffect(()=>{
    if(!props.motion&&!props.rent&&!props.outcome)return;
    Object.assign(props.nav.current,{mode:props.outcome?.stage==='draw'?'overview':'follow',center:null,zoom:null});
    props.changed();
  },[props.motion?.nonce,props.rent,props.outcome?.stage,props.outcome?.nonce,props.nav,props.changed]);
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
      <WorldLighting nav={props.nav}/>
      <CameraRig target={trackedPosition} reducedMotion={props.reducedMotion} insets={props.viewportInsets} map={props.game.map} nav={props.nav} onView={setView} changed={props.changed} onContext={props.onContext}/>
      <ContinuousGround view={view} map={props.game.map}/>
      <MiniatureTown game={props.game} view={view} nav={props.nav} onSelectTile={props.onSelectTile}/>
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
  const [navigationRevision,setNavigationRevision]=useState(0);
  const nav=useRef<Navigation>(initialNavigation(props.followCurrent));
  const [context,setContext]=useState<ContextRequest|null>(null);
  const shell=useRef<HTMLDivElement>(null);
  const canOpenContext=!props.paused&&!props.motion&&!props.rent&&!props.outcome;
  const openContext=useCallback((request:ContextRequest)=>{if(canOpenContext)setContext(request);},[canOpenContext]);
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
  // A financial modal has no visible scene interaction. Reduced-motion idle
  // scenes only need a fresh frame when React changes the game or camera.
  const frameLoop = props.paused
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
      data-frameloop={frameLoop}
      data-show-numbers={String(nav.current.showNumbers)}
      data-safe-insets={
        props.viewportInsets ? JSON.stringify(props.viewportInsets) : undefined
      }
    >
      {!ready && (
        <div className="scene-loading" role="status">
          <span />
          正在搭建晴湾小镇…
        </div>
      )}
      <Canvas
        aria-label="晴湾小镇 3D 棋盘"
        data-testid="world-canvas"
        orthographic
        frameloop={frameLoop}
        shadows={{type:THREE.PCFShadowMap}}
        dpr={[1, 2]}
        camera={{ position: [10.2, 12.5, 10.2], zoom: 48, near: 0.1, far: 80 }}
        gl={{
          antialias: true,
          alpha: false,
          powerPreference: "high-performance",
        }}
        onCreated={() => setReady(true)}
        fallback={
          <div className="scene-error" role="status">
            <strong>当前浏览器无法建立 3D 场景</strong>
            <span>仍可从下方列表查看地块，并使用原有回合操作继续游戏。</span>
            <div className="scene-fallback-grid">
              {props.game.tiles.map((tile) => (
                <button
                  key={tile.id}
                  type="button"
                  onClick={() => props.onSelectTile?.(tile.id)}
                >
                  {tile.id + 1} · {tile.title}
                </button>
              ))}
            </div>
          </div>
        }
      >
        <Suspense fallback={null}>
          <Scene {...props} nav={nav} changed={changed} navigationRevision={navigationRevision} onContext={openContext}/>
        </Suspense>
      </Canvas>
      <WorldNavigation game={props.game} nav={nav} changed={changed} disabled={props.paused??false}/>
      {context&&canOpenContext&&<MapContextMenu game={props.game} request={context} nav={nav} changed={changed} onSelect={props.onSelectTile} onClose={()=>setContext(null)} canvas={()=>shell.current?.querySelector('canvas')??null}/>}
    </div>
  );
}
