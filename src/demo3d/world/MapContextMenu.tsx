import { useEffect, useLayoutEffect, useRef, useState, type MutableRefObject } from 'react';
import { createPortal } from 'react-dom';
import type { GameState } from '../../core/game.js';
import { positionForTile } from './layout.js';
import { resetOrientation, type Navigation, type ContextRequest } from './world-navigation.js';

type Props={game:GameState;request:ContextRequest;nav:MutableRefObject<Navigation>;changed:()=>void;onSelect?: (id:number)=>void;onClose:()=>void;canvas:()=>HTMLCanvasElement|null};
export function MapContextMenu({game,request,nav,changed,onSelect,onClose,canvas}:Props):React.JSX.Element{
  const menu=useRef<HTMLDivElement>(null);
  const [position,setPosition]=useState({x:request.x,y:request.y});
  const tile=request.tileId===null?null:game.tiles[request.tileId];
  const close=(restore=true)=>{onClose();if(restore)canvas()?.focus({preventScroll:true});};
  useLayoutEffect(()=>{
    const box=menu.current!.getBoundingClientRect();
    setPosition({x:Math.max(8,Math.min(request.x,window.innerWidth-box.width-8)),y:Math.max(8,Math.min(request.y,window.innerHeight-box.height-8))});
    menu.current?.querySelector<HTMLButtonElement>('button')?.focus({preventScroll:true});
  },[request]);
  useEffect(()=>{
    const outside=(e:PointerEvent)=>{if(e.target instanceof Node&&!menu.current?.contains(e.target))onClose();};
    const dismiss=()=>onClose();
    document.addEventListener('pointerdown',outside,true);window.addEventListener('resize',dismiss);window.addEventListener('blur',dismiss);
    return ()=>{document.removeEventListener('pointerdown',outside,true);window.removeEventListener('resize',dismiss);window.removeEventListener('blur',dismiss);};
  },[onClose]);
  const act=(action:()=>void)=>{action();changed();close();};
  return createPortal(<div ref={menu} className="map-context-menu" role="menu" aria-label="地图快捷菜单" style={{left:position.x,top:position.y}} onContextMenu={e=>e.preventDefault()} onKeyDown={e=>{
    const buttons=Array.from(menu.current!.querySelectorAll<HTMLButtonElement>('button'));
    const index=buttons.indexOf(document.activeElement as HTMLButtonElement);
    if(['ArrowDown','ArrowUp','Home','End'].includes(e.key)){
      e.preventDefault();e.stopPropagation();const next=e.key==='Home'?0:e.key==='End'?buttons.length-1:(index+(e.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length;buttons[next].focus();
    }else if(e.key==='Escape'){e.preventDefault();e.stopPropagation();close();}else if(e.key==='Tab')close(false);
  }}>
    <div className="map-context-summary">
      <strong>{tile?`${tile.id+1} · ${tile.title}`:'地图操作'}</strong>
      <small>{tile?.kind==='property'?`${tile.ownerId?game.players.find(p=>p.id===tile.ownerId)?.name+'所有':'尚无地主'} · 地价 ${tile.price} · ${tile.level??0} 级` : tile?'公共地块':'在这里浏览你的小镇'}</small>
    </div>
    {tile&&<>
      <button role="menuitem" onClick={()=>act(()=>Object.assign(nav.current,{mode:'browse',center:positionForTile(tile.id,game.map),zoom:Math.max(24,nav.current.actualZoom)}))}>移到此地</button>
      <div role="separator"/>
    </>}
    <button role="menuitem" onClick={()=>act(()=>Object.assign(nav.current,{mode:'follow',center:null,zoom:null}))}>定位当前玩家</button>
    <button role="menuitem" onClick={()=>act(()=>Object.assign(nav.current,{mode:'overview',center:null,zoom:null}))}>查看全图 <kbd>Home</kbd></button>
    <button role="menuitem" onClick={()=>act(()=>resetOrientation(nav.current))}>视角回正 <kbd>R</kbd></button>
    <button role="menuitemcheckbox" aria-checked={nav.current.showNumbers} onClick={()=>act(()=>{nav.current.showNumbers=!nav.current.showNumbers;})}>{nav.current.showNumbers?'隐藏':'显示'}地块编号</button>
    <p className="map-context-help">按住地块或角色查看详情，松开即收起<br/>左键平移 · Shift＋左键旋转<br/>滚轮缩放 · Esc 关闭</p>
  </div>,document.body);
}
