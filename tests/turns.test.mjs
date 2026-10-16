import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, applyAction, nextDie, DEFAULT_CONFIG } from '../dist/core/game.js';

function act(state, type, actorId = state.players[state.currentPlayerIndex].id) {
  const result = applyAction(state, { type, actorId });
  assert.equal(result.ok, true, `${type}: ${result.reason ?? ''}`);
  return result;
}
function start(seed = 42, config = DEFAULT_CONFIG) {
  return act(createGame(seed, config), 'start_game').state;
}
function oneTurn(state) {
  const roll = act(state, 'roll');
  let s = roll.state;
  if (s.phase === 'await_decision') s = act(s, 'decline_property').state;
  assert.equal(s.phase, 'await_end_turn');
  return act(s, 'end_turn').state;
}

test('掷骰将当前玩家推进 1 到 6 格，输出有序的三类事件', () => {
  const state = start(99);
  const before = JSON.stringify(state);
  const die = nextDie(state.randomState);
  const result = act(state, 'roll');
  assert.equal(JSON.stringify(state), before, '原状态必须保持不变');
  assert.equal(result.state.players[0].position, die.value);
  assert.equal(result.state.randomState, die.nextState);
  assert.deepEqual(result.events.map(e => e.type), ['die_rolled', 'player_moved', 'tile_landed']);
  assert.equal(result.events[0].details.value, die.value);
  assert.equal(result.events[1].details.from, 0);
  assert.equal(result.events[1].details.to, die.value);
  assert.equal(result.events[2].details.tileId, die.value);
});

test('跨越棋盘尾格时环绕起点，不越界，格子来自可配置地图', () => {
  const state = start(23);
  const die = nextDie(state.randomState);
  const atEdge = { ...state, players: [{ ...state.players[0], position: state.tiles.length - 2 }, state.players[1]] };
  const result = act(atEdge, 'roll');
  assert.equal(result.state.players[0].position, (state.tiles.length - 2 + die.value) % state.tiles.length);
  assert.ok(result.state.players[0].position >= 0 && result.state.players[0].position < state.tiles.length);
  const mini = { ...DEFAULT_CONFIG, tiles: [{id:0,kind:'start',title:'起点'}, {id:1,kind:'neutral',title:'空地'}] };
  const smallRoll = act(start(23, mini), 'roll');
  assert.equal(smallRoll.state.players[0].position, die.value % 2);
});

test('每轮必须完成到达后的决策，不能重复掷骰或跳过对手', () => {
  const first = start(1);
  const rolled = act(first, 'roll').state;
  assert.equal(rolled.phase, 'await_decision');
  for (const type of ['roll','end_turn']) {
    const result = applyAction(rolled, { type, actorId:'p1' });
    assert.equal(result.ok, false);
    assert.equal(result.reason, 'INVALID_PHASE');
    assert.strictEqual(result.state, rolled);
  }
  assert.equal(applyAction(rolled,{type:'decline_property',actorId:'p2'}).reason,'INVALID_ACTOR');
  const declined = act(rolled, 'decline_property').state;
  assert.equal(declined.phase,'await_end_turn');
  assert.equal(applyAction(declined,{type:'roll',actorId:'p1'}).reason,'INVALID_PHASE');
  const ended = act(declined, 'end_turn').state;
  assert.equal(ended.currentPlayerIndex, 1);
  assert.equal(ended.round, 1);
  assert.equal(ended.phase,'await_roll');
  assert.equal(applyAction(ended,{type:'roll',actorId:'p1'}).reason,'INVALID_ACTOR');
  assert.equal(oneTurn(ended).round, 2);
});

test('落普通格可以直接结束回合，落可购地必须明确跳过购买', () => {
  const map = { ...DEFAULT_CONFIG, tiles: [
    {id:0,kind:'start',title:'起点'},
    {id:1,kind:'neutral',title:'休息'},
    {id:2,kind:'neutral',title:'休息'},
    {id:3,kind:'neutral',title:'休息'},
    {id:4,kind:'neutral',title:'休息'},
    {id:5,kind:'neutral',title:'休息'},
    {id:6,kind:'neutral',title:'休息'}] };
  const state = start(4, map);
  const rolled = act(state,'roll').state;
  assert.equal(rolled.phase,'await_end_turn');
  assert.equal(applyAction(rolled,{type:'decline_property',actorId:'p1'}).reason,'INVALID_PHASE');
  assert.equal(act(rolled,'end_turn').state.currentPlayerIndex,1);
});

test('固定种子与相同操作产生相同骰子、状态和事件', () => {
  let a = start(2026), b = start(2026);
  for(let i=0;i<16;i++){ a=oneTurn(a); b=oneTurn(b); }
  assert.deepEqual(a,b);
  assert.equal(a.round,9);
  assert.ok(a.events.filter(e=>e.type==='die_rolled').length===16);
});

test('多轮无界面运行能够推进到第 60 轮边界并完成退出', () => {
  // 旧 P1 的平局基线使用无随机事件地图；事件结算由 events.test 独立覆盖。
  let state=start(100,{...DEFAULT_CONFIG,eventRules:{tileIds:[],bonus:0,fee:0},cardRules:{tileIds:[],rewardCash:80,moveBonus:2,maxHand:3}});
  let count=0;
  while(state.status!=='finished' && count<140) { state=oneTurn(state); count++; }
  assert.equal(count,120);
  assert.equal(state.status,'finished');
  assert.equal(state.phase,'finished');
  assert.equal(state.round,60);
  assert.equal(state.winnerId,null);
  assert.equal(state.events.at(-1).type,'game_finished');
  const snap=JSON.stringify(state);
  for(const type of ['roll','decline_property','end_turn','start_game']){
    const result=applyAction(state,{type,actorId:state.players[state.currentPlayerIndex].id});
    assert.equal(result.ok,false, type);
    assert.strictEqual(result.state,state);
  }
  assert.equal(JSON.stringify(state),snap);
});
