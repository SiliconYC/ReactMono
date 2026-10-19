import test from 'node:test';
import assert from 'node:assert/strict';
import { visibleDecorations, rectanglesOverlap } from '../.test-dist/core/level-world.js';
import { LEVELS } from '../.test-dist/core/level-data.js';
import { anchorsForMap, inwardAngleForTile, canJoinLots } from '../.test-dist/demo3d/world/layout.js';
import * as view from '../.test-dist/demo3d/world/world-view.js';
import * as THREE from 'three';

test('竖屏远景四角在真实光源投影内，不能只覆盖世界包围盒半宽',()=>{
  const v=view.worldView({x:0,z:0},1.16,{width:390,height:844});
  const light=new THREE.DirectionalLight();
  light.position.copy(new THREE.Vector3(-.43,.8,.4).normalize().multiplyScalar(v.shadowRadius*2.5+20));
  Object.assign(light.shadow.camera,{left:-v.shadowRadius,right:v.shadowRadius,top:v.shadowRadius,bottom:-v.shadowRadius,near:1,far:v.shadowRadius*5+60});
  light.updateMatrixWorld();light.target.updateMatrixWorld();light.shadow.camera.updateProjectionMatrix();light.shadow.updateMatrices(light);
  const hw=390/2/1.16,hh=844/2/1.16;
  for(const x of [-hw,hw])for(const y of [-hh,hh]){
    const point=new THREE.Vector3((x-y/Math.sin(view.CAMERA_ELEVATION))/Math.SQRT2,0,(-x-y/Math.sin(view.CAMERA_ELEVATION))/Math.SQRT2).project(light.shadow.camera);
    assert.ok(Math.abs(point.x)<=1&&Math.abs(point.y)<=1,'可见角落超出统一阴影相机');
  }
});
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

test('景物完全来自关卡记录，改变视域只裁切而不改变位置/数量',()=>{
  for(const {world} of LEVELS){
    const all=visibleDecorations(world,{minX:-100000,maxX:100000,minZ:-100000,maxZ:100000});
    assert.deepEqual(all,world.objects);
    const bounds={minX:-20,maxX:20,minZ:-20,maxZ:20};
    for(const object of visibleDecorations(world,bounds))assert.ok(world.objects.includes(object));
    assert.deepEqual(visibleDecorations(world,bounds),visibleDecorations(world,bounds));
  }
});

test('任意朝向的道路与地产按真实旋转足迹检查，无碰撞且门口朝向所属道路',()=>{
  for(const {map,world} of LEVELS){
    const {tiles,lots}=anchorsForMap(map);
    const roadRects=tiles.map((p,id)=>({...p,rotation:world.tiles[id].rotation,halfX:.89,halfZ:.89}));
    const lotRects=lots.map((p,id)=>({...p,rotation:inwardAngleForTile(id,map),halfX:.6,halfZ:.6}));
    for(const [id,lot] of lots.entries()){
      assert.ok(Math.hypot(lot.x-tiles[id].x,lot.z-tiles[id].z)>=1.7,`${map.id}/${id} 地产落在行走线上`);
      for(const road of roadRects)assert.ok(!rectanglesOverlap(lotRects[id],road),`${map.id}/${id} 地产侵占道路`);
      for(const other of lotRects.slice(0,id))assert.ok(!rectanglesOverlap(lotRects[id],other),`${map.id}/${id} 地产重叠`);
      for(const [a,b] of anchorsForMap(map).edges){
        const edge={x:(a.x+b.x)/2,z:(a.z+b.z)/2,rotation:Math.atan2(b.x-a.x,b.z-a.z),halfX:.36,halfZ:Math.hypot(a.x-b.x,a.z-b.z)/2};
        assert.ok(!rectanglesOverlap(lotRects[id],edge),`${map.id}/${id} 地产侵占道路连接`);
      }
      const angle=inwardAngleForTile(id,map);
      assert.ok(Math.sin(angle)*(tiles[id].x-lot.x)+Math.cos(angle)*(tiles[id].z-lot.z)>1.6);
    }
    for(let i=0;i<roadRects.length;i++)for(let j=i+1;j<roadRects.length;j++)assert.ok(!rectanglesOverlap(roadRects[i],roadRects[j]),`${map.id} 路格${i}/${j}重叠`);
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

test('320格密集蛇形路线仍在本格旁分配地产，不把内部地产甩到地图远端',()=>{
  const cells=[];
  for(let x=1;x<=20;x++)cells.push({column:x,row:1});
  for(let z=2;z<=16;z++)for(let i=0;i<19;i++)cells.push({column:z%2===0?20-i:i+2,row:z});
  for(let z=16;z>=2;z--)cells.push({column:1,row:z});
  const map={id:'layout-dense-320',version:1,columns:20,rows:16,cells,route:cells.map((_,i)=>i)};
  const {tiles,lots}=anchorsForMap(map);
  for(let id=0;id<cells.length;id++)assert.ok(Math.hypot(tiles[id].x-lots[id].x,tiles[id].z-lots[id].z)<=2.84,`内部地产 ${id} 远离所属路格`);
  for(const lot of lots)for(const road of tiles)assert.ok(Math.abs(lot.x-road.x)>=1.7||Math.abs(lot.z-road.z)>=1.7);
});
