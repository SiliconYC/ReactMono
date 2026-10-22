import test from 'node:test';
import assert from 'node:assert/strict';
import * as math from '../.test-dist/demo3d/world/camera-math.js';
import * as layout from '../.test-dist/demo3d/world/layout.js';
import { LEVELS } from '../.test-dist/core/level-data.js';
import * as picking from '../.test-dist/demo3d/world/map-picking.js';
import * as THREE from 'three';

test('俯仰支持12度低角和82度俯视，低角数字仍留在地砖内',()=>{
  assert.equal(math.clampElevation(-1),Math.PI*12/180);
  assert.equal(math.clampElevation(10),Math.PI*82/180);
  for(const angle of [12,20,30,50,82]){
    const pose=math.labelPose(0,angle*Math.PI/180);
    assert.ok(Math.hypot(pose.x,pose.z)+Math.hypot(.22,.18*pose.scaleZ)<.89);
  }
});

test('初始化朝向来自每张图的下一块道路，转角与模拟位置不会共用默认方向',()=>{
  for(const {map} of LEVELS)for(const id of map.route){
    const point=layout.positionForTile(id,map),next=layout.positionForTile(map.route[(map.route.indexOf(id)+1)%map.route.length],map);
    const heading=layout.headingForTile?.(id,map);
    assert.equal(typeof heading,'number');
    assert.ok(Math.abs(Math.sin(heading)*(next.x-point.x)+Math.cos(heading)*(next.z-point.z)-Math.hypot(next.x-point.x,next.z-point.z))<1e-8);
  }
});

test('按住角色优先识别角色，房屋实例保持地块归属，不把角色当道路',()=>{
  const root=new THREE.Group(),mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshBasicMaterial());
  root.userData.playerId='p2';root.add(mesh);
  assert.deepEqual(picking.inspectionForHit?.({object:mesh}),{kind:'player',playerId:'p2'});
  const batch=new THREE.InstancedMesh(new THREE.BoxGeometry(),new THREE.MeshBasicMaterial(),2);
  batch.userData.tileIds=[13,14];
  assert.deepEqual(picking.inspectionForHit?.({object:batch,instanceId:1}),{kind:'tile',tileId:14});
});

test('长按必须持续400ms，松手、拖移和多指取消后不能迟到弹出',async()=>{
  const {InspectionHold}=await import('../.test-dist/demo3d/world/inspection-hold.js');
  const hold=new InspectionHold(),target={kind:'tile',tileId:3};
  hold.begin(1,100,80,target,1000);
  assert.equal(hold.read(1399),null);
  assert.deepEqual(hold.read(1400),{...target,x:100,y:80});
  hold.end();assert.equal(hold.read(2000),null);
  hold.begin(2,100,80,target,2000);hold.move(2,108,80);
  assert.equal(hold.read(3000),null);
  hold.begin(3,100,80,target,3000);hold.move(3,104,84);
  assert.ok(hold.read(3400));
});
