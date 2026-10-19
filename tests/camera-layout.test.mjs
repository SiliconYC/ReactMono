import test from 'node:test';
import assert from 'node:assert/strict';
import { cameraFrame } from '../.test-dist/demo3d/world/camera-layout.js';

test('全景相机把地图投影完整放入 HUD 实际安全区',()=>{
  for(const [width,height,insets] of [[1440,900,{top:80,left:256,right:24,bottom:190}],[360,640,{top:150,left:24,right:24,bottom:260}],[844,390,{top:128,left:24,right:24,bottom:130}]]){
    const frame=cameraFrame({width,height},insets,{width:18,depth:14});
    const {zoom,offsetX,offsetY,projectedWidth,projectedHeight}=frame;
    const cx=width/2+offsetX,cy=height/2-offsetY;
    assert.ok(cx-projectedWidth*zoom/2>=insets.left-.01);
    assert.ok(cx+projectedWidth*zoom/2<=width-insets.right+.01);
    assert.ok(cy-projectedHeight*zoom/2>=insets.top-.01);
    assert.ok(cy+projectedHeight*zoom/2<=height-insets.bottom+.01);
    assert.ok(Number.isFinite(zoom)&&zoom>0);
  }
});
test('没有 HUD 参数时仍可供独立 demo 使用',()=>{
 const frame=cameraFrame({width:1280,height:720},undefined,{width:10,depth:10});
 assert.equal(frame.offsetX,0);assert.equal(frame.offsetY,0);assert.ok(frame.zoom>0);
});
test('曲线地图按实际投影轮廓取景，手机不为轴对齐包围盒留下大块空白',async()=>{
 const {LEVELS}=await import('../.test-dist/core/level-data.js');
 const {anchorsForMap}=await import('../.test-dist/demo3d/world/layout.js');
 for(const {map,world}of LEVELS.filter(l=>l.playable)){
  const bounds=anchorsForMap(map).bounds;
  const viewport={width:390,height:844},insets={top:200,left:18,right:18,bottom:244};
  const actual=cameraFrame(viewport,insets,bounds),old=cameraFrame(viewport,insets,{width:bounds.width,depth:bounds.depth});
  assert.ok(actual.zoom>old.zoom*1.08,map.id+' 仍然按照空白矩形取景');
  for(const p of world.tiles){
   assert.ok(Math.abs((p.x-p.z)/Math.SQRT2)*2<actual.projectedWidth);
   assert.ok(Math.abs((p.x+p.z)/Math.SQRT2)*2*Math.sin(Math.atan2(12.2,Math.hypot(10.2,10.2)))<actual.projectedHeight);
  }
 }
});
