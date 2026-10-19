import { type MutableRefObject, useEffect } from 'react';
import { useThree } from '@react-three/fiber';
import { clampWorldZoom, panWorld } from './world-view.js';
import type { WorldPoint } from './layout.js';
export type Navigation = {
  mode:'follow'|'overview'|'browse';center:WorldPoint|null;zoom:number|null;
  actualCenter:WorldPoint;actualZoom:number;overviewZoom:number;draggedUntil:number;
};
/** Native canvas input also works on touch devices and reduced-motion demand frames. */
export function useWorldNavigation(nav:MutableRefObject<Navigation>,changed:()=>void):void{
  const {gl,invalidate}=useThree();
  useEffect(()=>{
    const canvas=gl.domElement,pointers=new Map<number,{x:number;y:number}>();
    let start:{x:number;y:number}|null=null,dragging=false,pinch=0,gestured=false;
    canvas.tabIndex=0;
    canvas.setAttribute('aria-label','三维地图：拖动浏览，滚轮或双指缩放，方向键移动，Home 查看全图');
    const zoom=(factor:number)=>{
      const n=nav.current;if(n.mode==='overview'){n.mode='browse';n.center=n.actualCenter;}n.zoom=clampWorldZoom((n.zoom??n.actualZoom)*factor,n.overviewZoom);
      invalidate();changed();
    };
    const down=(e:PointerEvent)=>{
      if(e.button!==0)return;
      canvas.focus({preventScroll:true});canvas.setPointerCapture(e.pointerId);
      if(pointers.size===0)gestured=false;
      pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
      start={x:e.clientX,y:e.clientY};dragging=false;
      if(pointers.size===2){const [a,b]=[...pointers.values()];pinch=Math.hypot(a.x-b.x,a.y-b.y);}
    };
    const move=(e:PointerEvent)=>{
      const prev=pointers.get(e.pointerId);if(!prev)return;
      pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
      if(pointers.size===2){
        const [a,b]=[...pointers.values()],distance=Math.hypot(a.x-b.x,a.y-b.y);
        if(pinch>0)zoom(distance/pinch);pinch=distance;
        gestured=true;nav.current.draggedUntil=performance.now()+400;return;
      }
      if(!start||Math.hypot(e.clientX-start.x,e.clientY-start.y)<6&&!dragging)return;
      const n=nav.current;n.mode='browse';n.center=panWorld(n.center??n.actualCenter,e.clientX-prev.x,e.clientY-prev.y,n.actualZoom);
      n.zoom=n.zoom??n.actualZoom;n.draggedUntil=performance.now()+400;
      dragging=true;gestured=true;invalidate();changed();
    };
    const up=(e:PointerEvent)=>{if(gestured)nav.current.draggedUntil=performance.now()+500;pointers.delete(e.pointerId);start=null;pinch=0;if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);};
    const wheel=(e:WheelEvent)=>{e.preventDefault();zoom(Math.exp(-Math.max(-200,Math.min(200,e.deltaY))*.0018));};
    const key=(e:KeyboardEvent)=>{
      const delta:{[key:string]:[number,number]}={ArrowLeft:[60,0],ArrowRight:[-60,0],ArrowUp:[0,60],ArrowDown:[0,-60]};
      if(delta[e.key]){e.preventDefault();const n=nav.current;n.mode='browse';n.zoom=n.zoom??n.actualZoom;n.center=panWorld(n.center??n.actualCenter,...delta[e.key],n.actualZoom);changed();invalidate();}
      else if(e.key==='+'||e.key==='='){e.preventDefault();zoom(1.25);}
      else if(e.key==='-'){e.preventDefault();zoom(.8);}
      else if(e.key==='Home'||e.key==='0'){e.preventDefault();Object.assign(nav.current,{mode:'overview',center:null,zoom:null});changed();invalidate();}
    };
    canvas.addEventListener('pointerdown',down);canvas.addEventListener('pointermove',move);canvas.addEventListener('pointerup',up);canvas.addEventListener('pointercancel',up);
    canvas.addEventListener('wheel',wheel,{passive:false});canvas.addEventListener('keydown',key);
    return ()=>{canvas.removeEventListener('pointerdown',down);canvas.removeEventListener('pointermove',move);canvas.removeEventListener('pointerup',up);canvas.removeEventListener('pointercancel',up);canvas.removeEventListener('wheel',wheel);canvas.removeEventListener('keydown',key);};
  },[gl,invalidate,nav,changed]);
}
