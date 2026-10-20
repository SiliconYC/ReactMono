import test from 'node:test';
import assert from 'node:assert/strict';
import * as math from '../.test-dist/demo3d/world/camera-math.js';
import { panWorld, worldView } from '../.test-dist/demo3d/world/world-view.js';
import { LEVELS } from '../.test-dist/core/level-data.js';

test('旋转角度限幅，鼠标手势互不重叠',()=>{
  assert.equal(math.pointerAction(0,false),'pan');
  assert.equal(math.pointerAction(0,true),'rotate');
  assert.equal(math.pointerAction(1,false),'rotate');
  assert.equal(math.pointerAction(2,false),null);
  assert.equal(math.clampElevation(-10),Math.PI/6);
  assert.equal(math.clampElevation(10),Math.PI*70/180);
});
test('任意方位和俯仰下平移与屏幕拖动一致',()=>{
  for(const yaw of [0,Math.PI/4,Math.PI/2,Math.PI,Math.PI*1.7])for(const elevation of [Math.PI/6,math.DEFAULT_ELEVATION,Math.PI*70/180]){
    const p=panWorld({x:0,z:0},83,-41,37,yaw,elevation);
    const screen=math.groundToScreen(p,yaw,elevation);
    assert.ok(Math.abs(screen.x*37+83)<1e-8);
    assert.ok(Math.abs(screen.y*37-41)<1e-8);
    const v=worldView({x:70,z:-30},37,{width:1440,height:900},yaw,elevation);
    for(const x of [-720/37,720/37])for(const y of [-450/37,450/37]){
      const corner=math.screenToGround({x,y},yaw,elevation);
      assert.ok(70+corner.x>=v.minX&&70+corner.x<=v.maxX);
      assert.ok(-30+corner.z>=v.minZ&&-30+corner.z<=v.maxZ);
    }
  }
});
test('各朝向的全图投影边界覆盖全部显式场景',()=>{
  for(const {map,world}of LEVELS)for(const yaw of [0,.8,2,3.5,5.8]){
    const b=math.mapProjectionBounds(map,yaw);
    for(const p of [...world.tiles,...world.surfaces.flatMap(s=>s.points)]){
      const screen=math.groundToScreen(p,yaw,Math.PI/2);
      assert.ok(Math.abs(screen.x)*2<b.projectedWidth);
      assert.ok(Math.abs(screen.y)*2<b.projectedDepth);
    }
  }
});
test('数字跟随视角正向，俯仰补偿后仍在旋转路砖内',()=>{
  for(const yaw of [0,.8,2,3.5,5.8])for(const elevation of [Math.PI/6,math.DEFAULT_ELEVATION,Math.PI*70/180]){
    const pose=math.labelPose(yaw,elevation);
    assert.equal(pose.rotation,yaw);
    assert.ok(Math.abs(pose.scaleZ*Math.sin(elevation)-Math.sin(math.DEFAULT_ELEVATION))<1e-9);
    for(const x of [-.22,.22])for(const z of [-.18,.18])assert.ok(Math.hypot(pose.x,pose.z)+Math.hypot(x,z*pose.scaleZ)<.89);
  }
});
test('多圈旋转后回正走最短角度，不反向连转数圈',async()=>{
  const {initialNavigation,resetOrientation}=await import('../.test-dist/demo3d/world/world-navigation.js');
  const n=initialNavigation(true);n.actualYaw=Math.PI*40+.1;n.yaw=n.actualYaw;n.elevation=.9;
  resetOrientation(n);
  assert.ok(Math.abs(n.yaw-n.actualYaw)<=Math.PI);
  assert.ok(Math.abs(Math.sin(n.yaw-math.DEFAULT_YAW))<1e-8);
  assert.equal(n.elevation,math.DEFAULT_ELEVATION);
});
