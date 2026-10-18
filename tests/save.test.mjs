import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, applyAction, nextDie } from '../.test-dist/core/game.js';
import { serializeGame, deserializeGame, SaveError, MAX_SAVE_CHARS } from '../.test-dist/core/save.js';
const now='2026-10-16T00:00:00.000Z';
function sample() {
  let state=applyAction(createGame(17),{type:'start_game',actorId:'p1'}).state;
  state=applyAction(state,{type:'roll',actorId:'p1'}).state;
  if(state.phase==='await_decision') state=applyAction(state,{type:'buy_property',actorId:'p1'}).state;
  return state;
}
test('v1 固定种子游戏无损往返，随机数进度及后续行动完全相同',()=>{
  const game=sample(),raw=serializeGame(game,{now}),stored=deserializeGame(raw);
  assert.deepEqual(stored.game,game);
  assert.equal(stored.rulesVersion,4);
  assert.equal(stored.formatVersion,1);
  assert.equal(stored.game.randomState,game.randomState);
  const action={type:'end_turn',actorId:'p1'};
  assert.deepEqual(applyAction(stored.game,action),applyAction(game,action));
  assert.equal(serializeGame(stored.game,{createdAt:stored.createdAt,now}),raw);
});
test('拒绝 JSON 损坏、缺失、未来版本、过大文件',()=>{
  const raw=serializeGame(sample(),{now});
  assert.throws(()=>deserializeGame('truncated'),e=>e instanceof SaveError && e.code==='INVALID_JSON');
  assert.throws(()=>deserializeGame('x'.repeat(MAX_SAVE_CHARS+1)),e=>e.code==='TOO_LARGE');
  for(const patch of [
    x=>{delete x.game.round;},x=>{x.game.players[0].cash=-1;},
    x=>{x.game.players[0].position=999;},x=>{x.game.tiles[1].ownerId='bogus';},
    x=>{x.game.players[0].cash=null;},x=>{x.game.randomState=0;},
    x=>{x.game.randomState=4294967296;},x=>{x.game.phase='setup';}
  ]) {
    const data=JSON.parse(raw);patch(data);
    assert.throws(()=>deserializeGame(JSON.stringify(data)),SaveError);
  }
  for(const [field,value] of [['formatVersion',99],['formatVersion',0],['rulesVersion',5]]) {
    const data=JSON.parse(raw);data[field]=value;
    assert.throws(()=>deserializeGame(JSON.stringify(data)),e=>e.code==='INCOMPATIBLE_VERSION');
  }
});
test('篡改合法范围内随机数亦被拒绝，原游戏不变',()=>{
  const game=sample(),snapshot=JSON.stringify(game),data=JSON.parse(serializeGame(game,{now}));
  data.game.randomState=(data.game.randomState+1)>>>0 || 1;
  assert.throws(()=>deserializeGame(JSON.stringify(data)),e=>e.code==='INVALID_CHECKSUM');
  assert.equal(JSON.stringify(game),snapshot);
});
test('多存档相互隔离，校验不依赖浏览器环境',()=>{
  const a=deserializeGame(serializeGame(sample(),{now}));
  const b=deserializeGame(serializeGame(createGame(42),{now}));
  assert.notDeepEqual(a.game,b.game);
  assert.equal(a.game.players[0].id,b.game.players[0].id);
  assert.notEqual(a.game.randomState,b.game.randomState);
});
