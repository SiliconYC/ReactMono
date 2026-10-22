import { type MutableRefObject, useEffect, useRef } from 'react';
import { useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { clampWorldZoom, panWorld } from './world-view.js';
import { clampElevation, DEFAULT_ELEVATION, DEFAULT_YAW, pointerAction } from './camera-math.js';
import type { WorldPoint } from './layout.js';
import { tileIdForHit, inspectionForHit, type InspectionRequest, type InspectionTarget } from './map-picking.js';
import { InspectionHold, INSPECTION_DELAY } from './inspection-hold.js';
export type Navigation = {
  mode:'follow'|'overview'|'browse';center:WorldPoint|null;zoom:number|null;
  actualCenter:WorldPoint;actualZoom:number;overviewZoom:number;draggedUntil:number;
  yaw:number;elevation:number;actualYaw:number;actualElevation:number;showNumbers:boolean;
};
export type ContextRequest={x:number;y:number;tileId:number|null};
export function resetOrientation(nav:Navigation):void{
  nav.yaw=nav.actualYaw+Math.atan2(Math.sin(DEFAULT_YAW-nav.actualYaw),Math.cos(DEFAULT_YAW-nav.actualYaw));
  nav.elevation=DEFAULT_ELEVATION;
}
export function initialNavigation(follow:boolean):Navigation{
  return {mode:follow?'follow':'overview',center:null,zoom:null,actualCenter:{x:0,z:0},actualZoom:32,overviewZoom:2,draggedUntil:0,yaw:DEFAULT_YAW,elevation:DEFAULT_ELEVATION,actualYaw:DEFAULT_YAW,actualElevation:DEFAULT_ELEVATION,showNumbers:true};
}
export function useWorldNavigation(nav:MutableRefObject<Navigation>,changed:()=>void,onContext:(request:ContextRequest)=>void,onInspect:(request:InspectionRequest|null)=>void,keyboardTarget:InspectionTarget):void{
  const {gl,invalidate,camera,scene}=useThree();
  const contextCallback=useRef(onContext);contextCallback.current=onContext;
  const inspectCallback=useRef(onInspect);inspectCallback.current=onInspect;
  const keyTarget=useRef(keyboardTarget);keyTarget.current=keyboardTarget;
  useEffect(()=>{
    const canvas=gl.domElement,pointers=new Map<number,{x:number;y:number;action:'pan'|'rotate'}>();
    const raycaster=new THREE.Raycaster();
    const hold=new InspectionHold();let holdTimer:ReturnType<typeof setTimeout>|null=null;
    const endInspection=()=>{if(holdTimer!==null)clearTimeout(holdTimer);holdTimer=null;hold.end();inspectCallback.current(null);};
    const pick=(x:number,y:number)=>{const rect=canvas.getBoundingClientRect();raycaster.setFromCamera(new THREE.Vector2((x-rect.left)/rect.width*2-1,-(y-rect.top)/rect.height*2+1),camera);return raycaster.intersectObjects(scene.children,true).map(inspectionForHit).find(hit=>hit!==null)??null;};
    const startInspection=(id:number,x:number,y:number,target:InspectionTarget)=>{hold.begin(id,x,y,target,performance.now());holdTimer=setTimeout(()=>{holdTimer=null;inspectCallback.current(hold.read(performance.now()));},INSPECTION_DELAY);};
    let start:{x:number;y:number}|null=null,dragging=false,pinch=0,gestured=false;
    canvas.tabIndex=0;
    canvas.setAttribute('aria-label','三维地图：左键拖动平移，Shift 加左键或中键拖动旋转，滚轮或双指缩放，右键地图菜单，R 回正，Home 全图');
    const zoom=(factor:number)=>{
      const n=nav.current;if(n.mode==='overview'){n.mode='browse';n.center={...n.actualCenter};}
      n.zoom=clampWorldZoom((n.zoom??n.actualZoom)*factor,Math.min(n.overviewZoom,n.actualZoom));
      invalidate();changed();
    };
    const down=(e:PointerEvent)=>{
      const action=pointerAction(e.button,e.shiftKey);if(!action)return;
      if(e.button===1)e.preventDefault();
      canvas.focus({preventScroll:true});canvas.setPointerCapture(e.pointerId);
      if(pointers.size===0)gestured=false;
      pointers.set(e.pointerId,{x:e.clientX,y:e.clientY,action});
      start={x:e.clientX,y:e.clientY};dragging=false;
      if(pointers.size===2){const [a,b]=[...pointers.values()];pinch=Math.hypot(a.x-b.x,a.y-b.y);}
      endInspection();
      if(pointers.size===1&&action==='pan'){const target=pick(e.clientX,e.clientY);if(target)startInspection(e.pointerId,e.clientX,e.clientY,target);}
    };
    const move=(e:PointerEvent)=>{
      const prev=pointers.get(e.pointerId);if(!prev)return;
      hold.move(e.pointerId,e.clientX,e.clientY);
      pointers.set(e.pointerId,{x:e.clientX,y:e.clientY,action:prev.action});
      if(pointers.size===2){
        const [a,b]=[...pointers.values()],distance=Math.hypot(a.x-b.x,a.y-b.y);
        if(pinch>0)zoom(distance/pinch);pinch=distance;
        gestured=true;nav.current.draggedUntil=performance.now()+400;return;
      }
      if(!start||Math.hypot(e.clientX-start.x,e.clientY-start.y)<7&&!dragging)return;
      endInspection();
      const n=nav.current,dx=e.clientX-prev.x,dy=e.clientY-prev.y;
      if(prev.action==='rotate'){
        if(n.mode==='overview'){n.mode='browse';n.center={...n.actualCenter};}
        n.yaw-=dx*.006;n.elevation=clampElevation(n.elevation+dy*.004);
      }else{
        n.mode='browse';n.center=panWorld(n.center??n.actualCenter,dx,dy,n.actualZoom,n.actualYaw,n.actualElevation);
      }
      // 旋转冻结当前缩放；不能让全景的自动取景偷偷变成第二套中键缩放。
      n.zoom=n.zoom??n.actualZoom;n.draggedUntil=performance.now()+400;
      dragging=true;gestured=true;invalidate();changed();
    };
    const up=(e:PointerEvent)=>{
      endInspection();
      if(gestured)nav.current.draggedUntil=performance.now()+500;
      pointers.delete(e.pointerId);start=pointers.values().next().value??null;pinch=0;dragging=false;
      if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);
    };
    const cancel=()=>{endInspection();pointers.clear();start=null;pinch=0;dragging=false;};
    const wheel=(e:WheelEvent)=>{e.preventDefault();endInspection();zoom(Math.exp(-Math.max(-200,Math.min(200,e.deltaY))*.0018));};
    const context=(e:MouseEvent)=>{
      e.preventDefault();if(hold.read(performance.now()))return;cancel();
      const rect=canvas.getBoundingClientRect();
      const x=e.clientX||rect.left+rect.width/2,y=e.clientY||rect.top+rect.height/2;
      raycaster.setFromCamera(new THREE.Vector2((x-rect.left)/rect.width*2-1,-(y-rect.top)/rect.height*2+1),camera);
      let tileId:number|null=null;
      for(const hit of raycaster.intersectObjects(scene.children,true)){
        tileId=tileIdForHit(hit);
        if(tileId!==null)break;
      }
      contextCallback.current({x,y,tileId});
    };
    const key=(e:KeyboardEvent)=>{
      if(e.metaKey||e.ctrlKey||e.altKey)return;
      if(e.key.toLowerCase()==='i'){e.preventDefault();if(!e.repeat){const box=canvas.getBoundingClientRect();startInspection(-1,box.left+box.width/2,box.top+box.height/2,keyTarget.current);}return;}
      const delta:{[key:string]:[number,number]}={ArrowLeft:[60,0],ArrowRight:[-60,0],ArrowUp:[0,60],ArrowDown:[0,-60]};
      if(delta[e.key]){e.preventDefault();const n=nav.current;n.mode='browse';n.zoom=n.zoom??n.actualZoom;n.center=panWorld(n.center??n.actualCenter,...delta[e.key],n.actualZoom,n.actualYaw,n.actualElevation);changed();invalidate();}
      else if(e.key==='+'||e.key==='='){e.preventDefault();zoom(1.25);}
      else if(e.key==='-'){e.preventDefault();zoom(.8);}
      else if(e.key==='Home'||e.key==='0'){e.preventDefault();Object.assign(nav.current,{mode:'overview',center:null,zoom:null});changed();invalidate();}
      else if(e.key.toLowerCase()==='r'){e.preventDefault();resetOrientation(nav.current);changed();invalidate();}
      else if(e.key==='ContextMenu'||e.key==='F10'&&e.shiftKey){e.preventDefault();context(new MouseEvent('contextmenu'));}
    };
    const middle=(e:MouseEvent)=>{if(e.button===1)e.preventDefault();};
    const keyUp=(e:KeyboardEvent)=>{if(e.key.toLowerCase()==='i')endInspection();};
    canvas.addEventListener('pointerdown',down);canvas.addEventListener('pointermove',move);canvas.addEventListener('pointerup',up);canvas.addEventListener('pointercancel',up);canvas.addEventListener('lostpointercapture',up);
    canvas.addEventListener('wheel',wheel,{passive:false});canvas.addEventListener('keydown',key);canvas.addEventListener('keyup',keyUp);canvas.addEventListener('contextmenu',context);canvas.addEventListener('mousedown',middle);canvas.addEventListener('auxclick',middle);window.addEventListener('blur',cancel);canvas.addEventListener('blur',endInspection);
    return ()=>{cancel();canvas.removeEventListener('pointerdown',down);canvas.removeEventListener('pointermove',move);canvas.removeEventListener('pointerup',up);canvas.removeEventListener('pointercancel',up);canvas.removeEventListener('lostpointercapture',up);canvas.removeEventListener('wheel',wheel);canvas.removeEventListener('keydown',key);canvas.removeEventListener('keyup',keyUp);canvas.removeEventListener('contextmenu',context);canvas.removeEventListener('mousedown',middle);canvas.removeEventListener('auxclick',middle);window.removeEventListener('blur',cancel);canvas.removeEventListener('blur',endInspection);};
  },[gl,invalidate,camera,scene,nav,changed]);
}
