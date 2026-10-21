import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, applyAction } from '../.test-dist/core/game.js';
import { residentialParts } from '../.test-dist/demo3d/world/town-kit.js';

test('住宅细节保持地块身份和占地，四种产权不把整栋墙面染成玩家色', () => {
  const game=applyAction(createGame(17),{type:'start_game',actorId:'p1'}).state;
  for(const level of [0,1,2]) {
    const tile={...game.tiles[1],ownerId:'p1',level};
    const parts=residentialParts(tile,'#ff715b',0);
    assert.ok(parts.length>10);
    for(const p of parts) {
      assert.equal(p.tileId,1);
      assert.ok(Math.abs(p.x)+(p.sx??1)/2<=.84,JSON.stringify(p));
      assert.ok(Math.abs(p.z)+(p.sz??1)/2<=.84,JSON.stringify(p));
      assert.ok(p.y-(p.sy??1)/2>=-.001,JSON.stringify(p));
    }
    if(level>0) assert.ok(parts.some(p=>p.color==='#f4e5c9'));
  }
});
test('升级改变形体与层次，抵押增加独立封条，不能靠整栋换色', () => {
  const game=createGame(17), tile={...game.tiles[1],ownerId:'p1'};
  const stages=[0,1,2].map(level=>residentialParts({...tile,level},'#ff715b',0));
  assert.ok(stages[1].some(p=>p.shape==='roof'));
  assert.ok(Math.max(...stages[2].map(p=>p.y))>Math.max(...stages[1].map(p=>p.y))+.4);
  assert.ok(stages[2].length>stages[1].length);
  const normal=residentialParts({...tile,level:1},'#ff715b',0);
  const mortgage=residentialParts({...tile,level:1,mortgaged:true},'#ff715b',0);
  assert.ok(mortgage.length>normal.length);
  assert.ok(mortgage.some(p=>p.color==='#b56854'));
});
test('山墙屋顶三角面向外，真实背面剔除不能漏掉斜屋面', async () => {
  const { GABLE_ROOF_VERTICES:v }=await import('../.test-dist/demo3d/world/town-kit.js');
  assert.ok(v?.length>=18);
  for(let i=0;i<v.length;i+=9) {
    const a=v.slice(i,i+3),b=v.slice(i+3,i+6),c=v.slice(i+6,i+9);
    const u=b.map((x,j)=>x-a[j]),w=c.map((x,j)=>x-a[j]);
    const n=[u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]];
    assert.ok(n.reduce((sum,x,j)=>sum+x*(a[j]+b[j]+c[j])/3,0)>0,'屋顶存在内向面');
  }
});
test('背窗玻璃必须在后墙之外，旋转到建筑背后仍可读',()=>{
  const t={...createGame(17).tiles[1],ownerId:'p1',level:2};
  const p=residentialParts(t,'#ff715b',0);
  assert.ok(p.some(x=>x.color==='#416b68'&&x.z<-.59));
});
test('场景预算忽略孤立冷帧，慢设备统一降档而大图细路保留像素密度',async()=>{
  const budget=await import('../.test-dist/demo3d/world/render-budget.js').catch(()=>null);
  assert.ok(budget,'缺少实际绘制预算策略');
  assert.equal(budget.chooseRenderBudget([16,17,16,18]),null);
  assert.equal(budget.chooseRenderBudget([16,17,1500,18,16]).mode,'full');
  const slow=budget.chooseRenderBudget([180,167,183,170,180]);
  assert.equal(slow.mode,'efficient');assert.equal(slow.shadowSize,1024);
  assert.equal(budget.renderPixelRatio('full',30,.7,2),2);
  assert.equal(budget.renderPixelRatio('efficient',1,.7,2),2);
  assert.equal(budget.renderPixelRatio('efficient',30,.7,2),.65);
});
