import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';

const distance=(a,b)=>Math.hypot(a.r-b.r,a.g-b.g,a.b-b.b);

test('已购路砖轻染玩家座位色，空地和选中态仍然清楚',async()=>{
  const kit=await import('../.test-dist/demo3d/world/lime-garden-ownership.js');
  assert.equal(typeof kit.gardenRoadColor,'function','路砖提供归属染色');
  const game={players:[{id:'owner-a'},{id:'owner-b'},{id:'owner-c'},{id:'owner-d'}],tiles:[{kind:'property',ownerId:'owner-a'},{kind:'property',ownerId:null},{kind:'facility',ownerId:null},{kind:'property',ownerId:'owner-b'}]};
  const base=new THREE.Color('#fff0ce'),seat=new THREE.Color('#ff715b'),owned=new THREE.Color(kit.gardenRoadColor(game,0,false));
  assert.equal(kit.gardenRoadColor(game,1,false),'#fff0ce');
  assert.equal(kit.gardenRoadColor(game,2,false),'#e8efce');
  assert.notEqual(kit.gardenRoadColor(game,0,false),kit.gardenRoadColor(game,3,false),'不同业主必须有可分辨底色');
  assert.ok(owned.r>.8&&owned.g>.6&&owned.b>.45,'染色后保持浅色路砖');
  assert.ok(distance(owned,base)<distance(seat,base)*.35,'业主色只作轻度混色');
  assert.ok(distance(owned,seat)<distance(base,seat),'底色向业主座位色靠近');
  assert.notEqual(kit.gardenRoadColor(game,0,true),kit.gardenRoadColor(game,0,false),'选中态仍可区分');
});

test('业主座位按玩家数组映射，未知业主返回中性饰色',async()=>{
  const kit=await import('../.test-dist/demo3d/world/lime-garden-ownership.js');
  assert.equal(typeof kit.gardenOwnerColor,'function','饰件颜色使用稳定座位映射');
  const game={players:[{id:'a'},{id:'b'},{id:'c'},{id:'d'}]};
  assert.deepEqual(['a','b','c','d'].map(id=>kit.gardenOwnerColor(game,id)),['#ff715b','#4f7cff','#28a77b','#c45bb4']);
  assert.equal(kit.gardenOwnerColor(game,null),'#f5df9e');
  assert.equal(kit.gardenOwnerColor(game,'missing'),'#f5df9e');
});
