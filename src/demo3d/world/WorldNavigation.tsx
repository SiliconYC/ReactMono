import { WorldMapShapes } from '../../ui/LevelPreview.js';
import { worldForMap } from '../../core/level-data.js';
import { useMemo, useState, type MutableRefObject } from 'react';
import type { GameState } from '../../core/game.js';
import { anchorsForMap } from './layout.js';
import { resetOrientation, type Navigation } from './world-navigation.js';
import { clampWorldZoom } from './world-view.js';
import { MASCOT_SEAT_COLORS } from './seats.js';
export function WorldNavigation({game,nav,changed,disabled}:{game:GameState;nav:MutableRefObject<Navigation>;changed:()=>void;disabled:boolean}):React.JSX.Element{
  const [help,setHelp]=useState(false);
  const [expanded,setExpanded]=useState(false);
  const anchors=anchorsForMap(game.map);
  const bounds=useMemo(()=>{
    const xs=anchors.tiles.map(p=>p.x),zs=anchors.tiles.map(p=>p.z);
    return {x:Math.min(...xs)-4,z:Math.min(...zs)-4,width:Math.max(...xs)-Math.min(...xs)+8,depth:Math.max(...zs)-Math.min(...zs)+8};
  },[anchors]);
  const reset=(mode:'overview'|'follow')=>{Object.assign(nav.current,{mode,center:null,zoom:null});changed();};
  const zoom=(factor:number)=>{if(nav.current.mode==='overview'){nav.current.mode='browse';nav.current.center=nav.current.actualCenter;}nav.current.zoom=clampWorldZoom((nav.current.zoom??nav.current.actualZoom)*factor,Math.min(nav.current.overviewZoom,nav.current.actualZoom));changed();};
  const n=nav.current;
  const marker=Math.max(bounds.width,bounds.depth)/48;
  return <div className="world-navigation" aria-label="地图浏览" hidden={disabled}>
    <div className="world-toolbar">
      <button type="button" aria-label={n.mode==='overview'?'定位当前玩家':'查看全图'} title={n.mode==='overview'?'跟随当前玩家':'查看全图'} onClick={()=>reset(n.mode==='overview'?'follow':'overview')}>{n.mode==='overview'?'定位':'全图'}</button>
      <button type="button" aria-label="地图工具" aria-expanded={expanded} aria-controls="world-controls-panel" onClick={()=>setExpanded(!expanded)}>⌖</button>
    </div>
    {expanded&&<div className="world-controls-panel" id="world-controls-panel">
    <div className="world-minimap">
      <div className="minimap-caption"><span>路线导览</span><small>{game.tiles.length} 格</small></div>
      <svg viewBox={`${bounds.x} ${bounds.z} ${bounds.width} ${bounds.depth}`} role="button" tabIndex={0} aria-label="路线小地图，点击街区放大定位" onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();reset('follow');}}} onClick={e=>{
        const matrix=e.currentTarget.getScreenCTM();if(!matrix)return;
        const p=new DOMPoint(e.clientX,e.clientY).matrixTransform(matrix.inverse());
        const nearest=anchors.tiles.reduce((a,b)=>Math.hypot(a.x-p.x,a.z-p.y)<Math.hypot(b.x-p.x,b.z-p.y)?a:b);
        Object.assign(n,{mode:'browse',center:nearest,zoom:Math.max(24,n.actualZoom)});changed();
      }}>
        <rect x={bounds.x} y={bounds.z} width={bounds.width} height={bounds.depth} fill={worldForMap(game.map)?.base.color??'#b7cd9a'}/>
        <WorldMapShapes world={worldForMap(game.map)}/>
        <polyline points={[...game.map.route,game.map.route[0]].map(id=>`${anchors.tiles[id].x},${anchors.tiles[id].z}`).join(' ')} fill="none" stroke="#fff5dc" strokeWidth={1.2} strokeLinejoin="round"/>
        <circle cx={anchors.tiles[0].x} cy={anchors.tiles[0].z} r={marker} fill="#dfac41"/>
        <polygon data-world-viewport="" fill="#d9ab5530" stroke="#c29443" strokeWidth={marker*.25} pointerEvents="none"/>
        {game.players.filter(p=>!p.bankrupt).sort((a,b)=>Number(a.id===game.players[game.currentPlayerIndex].id)-Number(b.id===game.players[game.currentPlayerIndex].id)).map(p=><circle key={p.id} cx={anchors.tiles[p.position].x} cy={anchors.tiles[p.position].z} r={marker} fill={MASCOT_SEAT_COLORS[game.players.findIndex(q=>p.id===q.id)]} stroke="#fff9e8" strokeWidth={marker*.3}/>)}
        {n.mode==='browse'&&n.center&&<circle cx={n.center.x} cy={n.center.z} r={marker*1.7} fill="none" stroke="#bd7c30" strokeWidth={marker*.3}/>}
      </svg>
      <span className="minimap-mode">{n.mode==='follow'?'跟随当前玩家':n.mode==='overview'?'全图概览':'自由浏览 · 点击定位'}</span>
    </div>
    <div className="world-camera-buttons">
      <button type="button" aria-label="放大地图" title="放大地图（+）" onClick={()=>zoom(1.3)}>＋</button>
      <button type="button" aria-label="缩小地图" title="缩小地图（−）" onClick={()=>zoom(1/1.3)}>−</button>
    </div>
    <div className="world-camera-extras">
      <button type="button" aria-label="视角回正" title="视角回正（R）" onClick={()=>{resetOrientation(nav.current);changed();}}><span data-compass-arrow="" aria-hidden="true">↑</span> 回正</button>
      <button type="button" aria-label="地图操作说明" aria-expanded={help} onClick={()=>setHelp(!help)}>？</button>
    </div>
    {help&&<div className="world-input-help" role="note"><strong>地图操作</strong><span>左键拖动：平移</span><span>Shift＋左键拖动：旋转</span><span>滚轮 / 双指：缩放</span><span>按住地块、房屋或角色：查看</span><span>按住 I：当前角色信息</span><span>右键：地图菜单</span><span>方向键：移动 · R：回正 · Home：全图</span></div>}
    </div>}
  </div>;
}
