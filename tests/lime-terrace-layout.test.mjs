import test from 'node:test';
import assert from 'node:assert/strict';
import { LEVELS } from '../.test-dist/core/level-data.js';
import { rectanglesOverlap } from '../.test-dist/core/level-world.js';
import { LIME_PROPERTY_BLOCKS } from '../.test-dist/core/property-groups.js';
const level=LEVELS.find(l=>l.map.id==='lime-garden-30');

test('青柠每个街区土地按2米方格紧贴排列，正对自己的道路且不侵占路线',()=>{
  const seen=new Set();
  for(const block of LIME_PROPERTY_BLOCKS){
    const first=level.world.tiles[block.tileIds[0]];
    for(const [index,id] of block.tileIds.entries()){
      assert.equal(level.tiles[id].kind,'property');
      assert.ok(!seen.has(id));seen.add(id);
      const p=level.world.tiles[id];
      assert.equal(Math.round(Math.hypot(p.x-p.lotX,p.z-p.lotZ)*100),215);
      assert.ok(Math.abs(p.x-p.lotX)<.00001||Math.abs(p.z-p.lotZ)<.00001);
      if(index){
        const prev=level.world.tiles[block.tileIds[index-1]];
        assert.ok(Math.abs(Math.hypot(p.lotX-prev.lotX,p.lotZ-prev.lotZ)-2)<1e-6);
        assert.ok(p.lotX===first.lotX||p.lotZ===first.lotZ);
        assert.equal(p.x-p.lotX,first.x-first.lotX);
        assert.equal(p.z-p.lotZ,first.z-first.lotZ);
      }
      for(const road of level.world.tiles)assert.equal(rectanglesOverlap(
        {x:p.lotX,z:p.lotZ,rotation:0,halfX:1,halfZ:1},
        {...road,halfX:.89,halfZ:.89}),false,`地块 ${id} 道路交叠`);
    }
  }
  assert.equal(seen.size,level.tiles.filter(t=>t.kind==='property').length);
});
