import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame } from '../.test-dist/core/game.js';
import { LEVELS } from '../.test-dist/core/level-data.js';
import { rectanglesOverlap, URBAN_SCENERY_KINDS } from '../.test-dist/core/level-world.js';

test('街区部件确定且贴地；不同功能建筑和街边小物保持可读的尺度层级',async()=>{
  const kit=await import('../.test-dist/demo3d/world/urban-kit.js').catch(()=>null);
  assert.ok(kit,'缺少生活街区模型工厂');
  const height=parts=>Math.max(...parts.map(p=>p.y+(p.sy??1)/2));
  for(const kind of ['corner-cafe','hotel','bookshop','bakery','apartment','greenhouse','market-hall','workshop','cypress','birch','willow','umbrella','cafe-table','market-cart','bus-stop','car','van','fountain','hydrant','bicycle']) {
    const p=kit.urbanParts(kind,'#c79578');
    assert.deepEqual(p,kit.urbanParts(kind,'#c79578'));
    assert.ok(p.length>0,kind);
    for(const part of p) {
      assert.ok([part.x,part.y,part.z,part.sx,part.sy,part.sz].every(Number.isFinite),kind);
      assert.ok(Math.min(part.sx,part.sy,part.sz)>0,kind);
      if(!part.rx&&!part.rz)assert.ok(part.y-part.sy/2>=-.012,kind+' 悬空/穿地');
    }
  }
  assert.ok(height(kit.urbanParts('hotel','#c79578'))>height(kit.urbanParts('bakery','#c79578'))+1);
  assert.ok(height(kit.urbanParts('car','#c79578'))<height(kit.urbanParts('corner-cafe','#c79578'))/2);
});

test('生活街区按模型真实占地避开棋盘路线，不沿用小道具的统一半径',async()=>{
  const {urbanParts}=await import('../.test-dist/demo3d/world/urban-kit.js');
  const world=LEVELS.find(l=>l.map.id==='classic-24').world,kinds=new Set(URBAN_SCENERY_KINDS);
  for(const o of world.objects.filter(o=>kinds.has(o.kind))) {
    const p=urbanParts(o.kind,o.color);
    const minX=Math.min(...p.map(q=>q.x-q.sx/2))*o.scale,maxX=Math.max(...p.map(q=>q.x+q.sx/2))*o.scale;
    const minZ=Math.min(...p.map(q=>q.z-q.sz/2))*o.scale,maxZ=Math.max(...p.map(q=>q.z+q.sz/2))*o.scale;
    const c=Math.cos(o.rotation),s=Math.sin(o.rotation),x=(minX+maxX)/2,z=(minZ+maxZ)/2;
    const bounds={x:o.x+c*x+s*z,z:o.z-s*x+c*z,rotation:o.rotation,halfX:(maxX-minX)/2,halfZ:(maxZ-minZ)/2};
    for(const [id,t]of world.tiles.entries()){
      assert.ok(!rectanglesOverlap(bounds,{...t,halfX:.89,halfZ:.89}),`${o.id}侵占路格${id}`);
      const next=world.tiles[(id+1)%world.tiles.length],dx=next.x-t.x,dz=next.z-t.z;
      assert.ok(!rectanglesOverlap(bounds,{x:(t.x+next.x)/2,z:(t.z+next.z)/2,rotation:Math.atan2(dx,dz),halfX:.91,halfZ:Math.hypot(dx,dz)/2}),`${o.id}侵占连续步行街${id}`);
    }
  }
});

test('开放临街地块保持空地语义，住宅成长和产权不侵占相邻地块',async()=>{
  const kit=await import('../.test-dist/demo3d/world/street-property-kit.js').catch(()=>null);
  assert.ok(kit,'未替换墓园式地产');
  const base=createGame(17).tiles[1];
  for(const id of [1,2,4,5,7,8])for(const level of [0,1,2]) {
    const p=kit.streetPropertyParts({...base,id,ownerId:'p1',level},'#ff715b',0);
    for(const q of p){
      assert.equal(q.tileId,id);
      assert.ok(Math.abs(q.x)+q.sx/2<=.84,JSON.stringify(q));
      assert.ok(Math.abs(q.z)+q.sz/2<=.84,JSON.stringify(q));
      assert.ok(q.y-q.sy/2>=-.001,JSON.stringify(q));
    }
    if(level===0)assert.ok(Math.max(...p.map(q=>q.y+q.sy/2))<.9,'空地不能画成住宅');
  }
  const unsold=kit.streetPropertyParts({...base,ownerId:null,level:0},null,0);
  assert.ok(unsold.some(p=>p.label==='待售'));
  assert.ok(!unsold.some(p=>p.shape==='box'&&p.sy>.1&&p.sz>1&&p.sx<.2),'不恢复两侧长围墙');
  const one=kit.streetPropertyParts({...base,ownerId:'p1',level:1},'#ff715b',0);
  const two=kit.streetPropertyParts({...base,ownerId:'p1',level:2},'#ff715b',0);
  assert.ok(Math.max(...two.map(p=>p.y))>Math.max(...one.map(p=>p.y))+.5);
  assert.ok(kit.streetPropertyParts({...base,ownerId:'p1',level:2,mortgaged:true},'#ff715b',0).length>two.length);
});
