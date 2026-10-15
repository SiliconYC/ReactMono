import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, applyAction, nextDie, DEFAULT_CONFIG } from '../dist/core/game.js';

test('初始化两名玩家、24 格地图及版本化状态', () => {
  const state = createGame(1234);
  assert.equal(state.schemaVersion, 1);
  assert.equal(state.status, 'setup');
  assert.equal(state.phase, 'setup');
  assert.equal(state.currentPlayerIndex, 0);
  assert.equal(state.players.length, 2);
  assert.deepEqual(state.players.map(p => p.kind), ['human', 'computer']);
  assert.deepEqual(state.players.map(p => p.cash), [1500,1500]);
  assert.equal(state.tiles.length, 24);
  assert.equal(state.tiles.filter(t => t.kind==='start').length,1);
  assert.equal(state.tiles.filter(t => t.kind==='property').length,16);
  assert.equal(state.tiles.filter(t => t.kind==='neutral').length,7);
  assert.equal(state.tiles[0].kind,'start');
  assert.equal(DEFAULT_CONFIG.maxRounds,60);
});

test('开始动作通过纯函数切换状态并提供可观察事件', () => {
  const before = createGame(42);
  const result = applyAction(before,{type:'start_game',actorId:'p1'});
  assert.equal(result.ok,true);
  assert.equal(before.status,'setup');
  assert.equal(result.state.status,'playing');
  assert.equal(result.state.phase,'await_roll');
  assert.deepEqual(result.events.map(e=>e.type),['game_started']);
  assert.equal(result.state.revision,1);
  assert.notStrictEqual(result.state,before);
});

test('非法动作与错误行动者明确拒绝，绝不篡改状态', () => {
  const before = createGame(42);
  const snapshot = JSON.stringify(before);
  const forbidden = [
    {type:'start_game',actorId:'p2'},
    {type:'roll',actorId:'p1'},
    {type:'buy_property',actorId:'p1'},
    {type:'end_turn',actorId:'p1'}
  ];
  for(const action of forbidden){
    const result=applyAction(before,action);
    assert.equal(result.ok,false,JSON.stringify(action));
    assert.strictEqual(result.state,before);
    assert.equal(result.events.length,0);
    assert.ok(result.reason);
    assert.equal(JSON.stringify(before),snapshot);
  }
});

test('开始游戏不能重复，地产购买需要正确阶段', () => {
  const started=applyAction(createGame(7),{type:'start_game',actorId:'p1'}).state;
  const twice=applyAction(started,{type:'start_game',actorId:'p1'});
  assert.equal(twice.ok,false);
  assert.equal(twice.reason,'INVALID_PHASE');
  const roll=applyAction(started,{type:'roll',actorId:'p1'});
  assert.equal(roll.ok,true);
  assert.equal(roll.events[0].type,'die_rolled');
  const buy=applyAction(roll.state,{type:'buy_property',actorId:'p1'});
  if (roll.state.phase === 'await_decision') {
    assert.equal(buy.ok,true);
    assert.equal(buy.state.tiles[buy.state.players[0].position].ownerId,'p1');
  } else {
    assert.equal(buy.reason,'INVALID_PHASE');
  }
});

test('固定种子骰子可复现且只产生 1 至 6；零种子也可以运行', () => {
  for(const seed of [0,1,42,999999]){
    const one=[]; const two=[];
    let a=seed,b=seed;
    for(let i=0;i<100;i++){
      const x=nextDie(a),y=nextDie(b);
      one.push(x.value);two.push(y.value);a=x.nextState;b=y.nextState;
      assert.ok(x.value>=1&&x.value<=6);
    }
    assert.deepEqual(one,two);
    assert.ok(new Set(one).size>=4);
  }
});

test('拒绝非法地图、重复玩家和非有限种子', () => {
  assert.throws(()=>createGame(Number.NaN),/种子/);
  assert.throws(()=>createGame(1,{...DEFAULT_CONFIG,tiles:[]} ),/地图/);
  assert.throws(()=>createGame(1,{...DEFAULT_CONFIG,players:[{id:'p1',name:'人'},{id:'p1',name:'电脑'}]}),/玩家/);
});
