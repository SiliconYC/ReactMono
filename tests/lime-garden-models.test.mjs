import test from 'node:test';
import assert from 'node:assert/strict';

test('折瓦圆顶同一圈存在真实瓦垄高差且法线向外',async()=>{
  const kit=await import('../.test-dist/demo3d/world/lime-garden-models.js');
  const g=kit.foldedRoofGeometry();g.computeBoundingBox();
  assert.ok(g.boundingBox.max.x>1.05&&g.boundingBox.max.x<1.15);
  assert.ok(g.boundingBox.max.y>.65&&g.boundingBox.min.y>=0);
  const p=g.getAttribute('position'),n=g.getAttribute('normal');
  let ridge=-Infinity,valley=Infinity,outward=0;
  for(let i=0;i<p.count;i++){
    const r=Math.hypot(p.getX(i),p.getZ(i));
    if(r>.769&&r<.781){ridge=Math.max(ridge,p.getY(i));valley=Math.min(valley,p.getY(i));outward+=p.getX(i)*n.getX(i)+p.getZ(i)*n.getZ(i);}
  }
  assert.ok(ridge-valley>.015,'屋面必须有实际起伏');
  assert.ok(outward>0,'上表面法线不得朝内');
  assert.ok(g.index.count/3<20000,'每层屋面保持可批量渲染的体量');
  g.dispose();
});

test('建造动画从地面展开、短时落定，减少动态直接完成',async()=>{
  const {constructionPose}=await import('../.test-dist/demo3d/world/lime-garden-models.js');
  assert.ok(constructionPose(0,false).scaleY<.1);
  assert.ok(constructionPose(.2,false).scaleY>.1);
  assert.ok(constructionPose(.45,false).scaleY>1);
  assert.deepEqual(constructionPose(1,false),{scaleY:1,dust:0,finished:true});
  assert.deepEqual(constructionPose(0,true),{scaleY:1,dust:0,finished:true});
});

test('两级住宅几何贴地、未侵占邻格，二级体量和轮廓明显增长',async()=>{
  const {gardenHouseGeometry}=await import('../.test-dist/demo3d/world/lime-garden-models.js');
  const a=gardenHouseGeometry(1),b=gardenHouseGeometry(2);
  for(const g of [a,b]){g.computeBoundingBox();assert.ok(Math.abs(g.boundingBox.min.y)<.001);assert.ok(g.boundingBox.min.x>=-.7&&g.boundingBox.max.x<=.7);assert.ok(g.boundingBox.min.z>=-.7&&g.boundingBox.max.z<=.7);}
  assert.ok(b.boundingBox.max.y>a.boundingBox.max.y*1.4);
  assert.ok(b.getAttribute('position').count>a.getAttribute('position').count*1.3);
  a.dispose();b.dispose();
});

test('联排住宅以两米共墙单元相接，屋面不越过地界且两级保留高度差', async()=>{
  const {gardenHouseGeometry}=await import('../.test-dist/demo3d/world/lime-garden-models.js');
  const geometries=[gardenHouseGeometry(1,true),gardenHouseGeometry(2,true)];
  for(const geometry of geometries){
    geometry.computeBoundingBox();const box=geometry.boundingBox;
    assert.ok(Math.abs(box.min.x+1)<.001&&Math.abs(box.max.x-1)<.001);
    assert.ok(Math.abs(box.min.y)<.001);
    assert.ok(box.max.z<.8&&box.min.z>-.8);
    const normals=geometry.getAttribute('normal');
    assert.ok([...normals.array].every(Number.isFinite));
    geometry.dispose();
  }
});

test('联排瓦垄贴合两侧屋面，不从檐口向上翘成尖刺',async()=>{
  const {gardenHouseGeometry}=await import('../.test-dist/demo3d/world/lime-garden-models.js');
  for(const level of [1,2]){
    const geometry=gardenHouseGeometry(level,true),height=level===1?.68:1.3;
    const positions=geometry.getAttribute('position');
    for(let i=0;i<positions.count;i++){
      const y=positions.getY(i),z=positions.getZ(i);
      if(y>height+.055)assert.ok(y<=height+.36-Math.abs(z+.04)*.32/.54,`屋面越界 ${level}/${y}/${z}`);
    }
    geometry.dispose();
  }
});
