import test from 'node:test';
import assert from 'node:assert/strict';
import { LEVELS } from '../.test-dist/core/level-data.js';
import { anchorsForMap, inwardAngleForTile, canJoinLots } from '../.test-dist/demo3d/world/layout.js';
import * as view from '../.test-dist/demo3d/world/world-view.js';
test('镜头缩放有可读细节上限，拖动在正交地面上与屏幕位移一致',()=>{
  assert.equal(typeof view.panWorld,'function');
  assert.equal(typeof view.clampWorldZoom,'function');
  const p=view.panWorld({x:0,z:0},100,0,50);
  assert.ok(Math.abs((p.x-p.z)/Math.SQRT2*50+100)<1e-9);
  assert.ok(Math.abs(p.x+p.z)<1e-9);
  assert.equal(view.clampWorldZoom(10000,3),96);
  assert.equal(view.clampWorldZoom(-1,3),3);
});

test('视域分块覆盖缩放、HUD偏移和远端浏览；裁切与雾不吞掉大图',()=>{
  assert.equal(typeof view.worldView,'function');
  for(const zoom of [2,12,48,96]) for(const [width,height] of [[1440,900],[390,844],[844,390]]){
    const v=view.worldView({x:180,z:-110},zoom,{width,height});
    const chunks=view.groundChunks(v);
    for(const [x,z] of [[v.minX,v.minZ],[v.maxX,v.minZ],[v.minX,v.maxZ],[v.maxX,v.maxZ]]){
      assert.ok(chunks.some(c=>x>=c.x-8&&x<=c.x+8&&z>=c.z-8&&z<=c.z+8),'地表未覆盖视域角');
    }
    assert.ok(v.distance>v.depthReach+4,'镜头前后都必须容纳可见地面');
    assert.ok(v.far>v.distance+v.depthReach+4);
    assert.ok(v.fogNear>=v.distance+v.depthReach,'可见地面不得被远景雾抹掉');
    assert.ok(v.shadowRadius>=v.halfExtent,'阴影必须覆盖可见区');
  }
});

test('装饰世界种子稳定且全部通过道路/地产禁入区',()=>{
  assert.equal(typeof view.sceneryForChunks,'function');
  for(const {map} of LEVELS){
    const chunks=view.groundChunks(view.worldView({x:0,z:0},20,{width:900,height:600}));
    const a=view.sceneryForChunks(chunks,map),b=view.sceneryForChunks([...chunks].reverse(),map);
    assert.deepEqual([...a].sort((a,b)=>a.x-b.x||a.z-b.z),[...b].sort((a,b)=>a.x-b.x||a.z-b.z));
    const {tiles,lots}=anchorsForMap(map);
    for(const p of a)for(const q of [...tiles,...lots])assert.ok(Math.abs(p.x-q.x)>1.4||Math.abs(p.z-q.z)>1.4);
  }
});

test('全部内置地图地产在道路旁独立落地，凹角和首尾不侵占任何道路或其他地产',()=>{
  for(const {map} of LEVELS){
    const {tiles,lots}=anchorsForMap(map);
    for(const [id,lot] of lots.entries()){
      assert.ok(Math.hypot(lot.x-tiles[id].x,lot.z-tiles[id].z)>=1.7,`${map.id}/${id} 地产落在行走线上`);
      for(const road of tiles) assert.ok(Math.abs(lot.x-road.x)>=1.7 || Math.abs(lot.z-road.z)>=1.7,`${map.id}/${id} 地产侵占道路`);
      for(const other of lots.slice(0,id)) assert.ok(Math.abs(lot.x-other.x)>=1.7 || Math.abs(lot.z-other.z)>=1.7,`${map.id}/${id} 地产重叠`);
      const angle=inwardAngleForTile(id,map);
      assert.ok(Math.sin(angle)*(tiles[id].x-lot.x)+Math.cos(angle)*(tiles[id].z-lot.z)>1.6,`${map.id}/${id} 门口未朝向所属道路`);
    }
  }
});

test('地产布局跟随真实 route 邻接关系，反向路线仍无占用冲突',()=>{
  for(const {map} of LEVELS){
    const reverse={...map,route:[map.route[0],...map.route.slice(1).reverse()]};
    assert.deepEqual(anchorsForMap(reverse).lots,anchorsForMap(map).lots);
  }
});

test('320格狭长双排路线的地产不占用相邻平行道路，联排不跨路',()=>{
  const cells=[...Array.from({length:160},(_,i)=>({column:i+1,row:1})),...Array.from({length:160},(_,i)=>({column:160-i,row:2}))];
  const map={id:'layout-long-320',version:1,columns:160,rows:2,cells,route:cells.map((_,i)=>i)};
  const {tiles,lots}=anchorsForMap(map);
  assert.equal(lots.length,320);
  assert.equal(new Set(lots.map(p=>`${p.x},${p.z}`)).size,320);
  for(const lot of lots)for(const road of tiles)assert.ok(Math.abs(lot.x-road.x)>=1.7||Math.abs(lot.z-road.z)>=1.7);
  for(const a of map.route){
    const b=(a+1)%320;
    if(canJoinLots(a,b,map)){
      const center={x:(lots[a].x+lots[b].x)/2,z:(lots[a].z+lots[b].z)/2};
      for(const road of tiles)assert.ok(Math.abs(center.x-road.x)>=1.6||Math.abs(center.z-road.z)>=1.6);
    }
  }
});
