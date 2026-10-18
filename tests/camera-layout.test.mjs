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
