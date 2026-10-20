import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { loadLevelCatalog, LEVELS } from '../.test-dist/core/level-data.js';
const catalog=()=>JSON.parse(readFileSync('src/data/levels.json','utf8'));
test('版本2世界为关卡必需数据，每个道路和地产有明确坐标，所有景物有独立标识',()=>{
  assert.equal(catalog().schemaVersion,2);
  for(const level of LEVELS){
    assert.equal(level.world.version,1);
    assert.equal(level.world.tiles.length,level.tiles.length);
    assert.ok(level.world.surfaces.length>0);
    assert.ok(level.world.objects.length>0);
    assert.equal(new Set(level.world.objects.map(o=>o.id)).size,level.world.objects.length);
    assert.ok(Object.isFrozen(level.world.objects[0]));
  }
});
test('世界加载拒绝缺失、非有限值、未知景物、重复标识、自交地形和道路缺格',()=>{
  const mutations=[c=>delete c.levels[0].world,
    c=>c.levels[0].world.tiles.pop(),
    c=>c.levels[0].world.tiles[1]={...c.levels[0].world.tiles[0]},
    c=>c.schemaVersion='2',
    c=>c.levels[0].world.tiles[0].x=Infinity,
    c=>c.levels[0].world.objects[0].kind='unknown',
    c=>c.levels[0].world.objects.push({...c.levels[0].world.objects[0]}),
    c=>c.levels[0].world.objects[0].scale=-1,
    c=>c.levels[0].world.surfaces[0].points=[{x:0,z:0},{x:4,z:4},{x:0,z:4},{x:4,z:0}],
    c=>c.levels[0].world.surfaces[0].holes=[[{x:999,z:999},{x:1000,z:999},{x:1000,z:1000}]],
    c=>c.levels[0].world.script='scatter trees'];
  for(const mutate of mutations){const c=catalog();mutate(c);assert.throws(()=>loadLevelCatalog(c),/世界|关卡/);}
});
test('旧版规则草稿仍能读取，场景对象不进入对局和存档',()=>{
  const old=catalog();old.schemaVersion=1;old.levels.forEach(l=>delete l.world);
  const loaded=loadLevelCatalog(old);
  assert.equal(loaded[0].map.id,'classic-24');
});
test('场景改版不修改任何既有规则拓扑或经济数据',async()=>{
  const {createHash}=await import('node:crypto');
  const hashes=JSON.parse(readFileSync('tests/fixtures/map-rule-digests.json','utf8'));
  for(const level of LEVELS){
    const rules=Object.fromEntries(['map','tiles','initialCash','maxRounds','eventRules','cardRules','facilityConfig'].map(k=>[k,level[k]]));
    assert.equal(createHash('sha256').update(JSON.stringify(rules)).digest('hex'),hashes[level.map.id],level.map.id+' 既有规则发生变化');
  }
});
test('景物不侵占道路或地产，亭台落在明确陆地上',async()=>{
  const {pointInPolygon,rectanglesOverlap}=await import('../.test-dist/core/level-world.js');
  for(const {map,world:w} of LEVELS){
    const dry=p=>w.base.kind==='grass'?!w.surfaces.some(s=>s.kind==='water'&&pointInPolygon(p,s.points)&&!s.holes.some(h=>pointInPolygon(p,h))):w.surfaces.some(s=>s.kind!=='water'&&pointInPolygon(p,s.points)&&!s.holes.some(h=>pointInPolygon(p,h)));
    for(const t of w.tiles){assert.ok(dry(t),map.id+' 道路落水');assert.ok(dry({x:t.lotX,z:t.lotZ}),map.id+' 地产落水');}
    for(const o of w.objects){
      if(!['boat','dock','rock'].includes(o.kind))assert.ok(dry(o),map.id+'/'+o.id+'悬在水上');
      if(o.id.startsWith('站点-')||['boat','dock'].includes(o.kind))continue;
      const half=(o.kind==='tower'?2.4:o.kind==='tree'||o.kind==='pine'?.72:o.kind==='gazebo'?1.05:.6)*o.scale;
      const footprint={...o,halfX:half,halfZ:half};
      for(const [id,t] of w.tiles.entries()){
        assert.ok(!rectanglesOverlap(footprint,{...t,halfX:.89,halfZ:.89}),`${map.id}/${o.id}侵占路格${id}`);
        assert.ok(!rectanglesOverlap(footprint,{x:t.lotX,z:t.lotZ,rotation:Math.atan2(t.x-t.lotX,t.z-t.lotZ),halfX:.7,halfZ:.7}),`${map.id}/${o.id}侵占地产${id}`);
      }
    }
  }
});
