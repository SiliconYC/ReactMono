import test from 'node:test';import assert from 'node:assert/strict';
import {createGame,applyAction,nextDie} from '../dist/core/game.js';
import {serializeGame,deserializeGame} from '../dist/core/save.js';
import {chooseComputerAction} from '../dist/core/agent.js';
import {runSimulation} from '../dist/core/simulator.js';
const act=(s,a)=>applyAction(s,{actorId:s.players[s.currentPlayerIndex].id,...a});
const start=()=>act(createGame(17),{type:'start_game'}).state;
const withCards=(k='reward')=>{let s=start();return {...s,players:s.players.map((p,i)=>i===0?{...p,cards:{reward:k==='reward'?1:0,stride:k==='stride'?1:0}}:p)}};
test('奖励卡合法使用一次、库存归零、现金收益；非法阶段、目标和重复用卡不能修改状态',()=>{
 let s=withCards(),before=s.players[0].cash;
 const r=act(s,{type:'use_card',cardType:'reward'});assert.equal(r.ok,true);
 assert.equal(r.state.players[0].cash,before+80);assert.equal(r.state.players[0].cards.reward,0);
 assert.equal(r.events[0].type,'card_used');
 const forbidden=[
  act(r.state,{type:'use_card',cardType:'reward'}),
  act(s,{type:'use_card',cardType:'reward',targetId:'p2'}),
  act({...s,phase:'await_end_turn'},{type:'use_card',cardType:'reward'}),
  act(s,{type:'use_card',cardType:'unrecognized'})
 ];
 for(const x of forbidden){assert.equal(x.ok,false);assert.deepEqual(x.events,[]);}
 assert.equal(s.players[0].cash,before);
});
test('步数卡修正下一次掷骰而非跳过地块结算，单回合不能叠加',()=>{
 let s=withCards('stride'),die=nextDie(s.randomState).value;
 let used=act(s,{type:'use_card',cardType:'stride'});assert.equal(used.ok,true);
 assert.equal(used.state.pendingMoveBonus,2);
 assert.equal(act(used.state,{type:'use_card',cardType:'stride'}).ok,false);
 const rolled=act(used.state,{type:'roll'});assert.equal(rolled.ok,true);
 assert.equal(rolled.state.players[0].position,(die+2)%24);
 assert.equal(rolled.state.pendingMoveBonus,0);
 assert.equal(rolled.events.find(e=>e.type==='die_rolled').details.bonus,2);
 assert.ok(rolled.events.some(e=>e.type==='tile_landed'));
 assert.deepEqual(deserializeGame(serializeGame(rolled.state)).game,rolled.state);
});
test('卡片站按随机种子稳定发卡，库存上限有效',()=>{
 let s=start(),roll=nextDie(s.randomState).value;
 s={...s,players:s.players.map((p,i)=>i===0?{...p,position:(6-roll+24)%24}:p)};
 const a=act(s,{type:'roll'}),b=act(s,{type:'roll'});
 assert.deepEqual(a,b);assert.equal(a.ok,true);
 assert.equal(a.events.filter(e=>e.type==='card_received').length,1);
 assert.equal((a.state.players[0].cards.reward+a.state.players[0].cards.stride),1);
 let full={...s,players:s.players.map((p,i)=>i===0?{...p,cards:{reward:3,stride:0}}:p)};
 assert.equal(act(full,{type:'roll'}).events.some(e=>e.type==='card_received'),false);
});
test('电脑先用合法卡片再掷骰，固定种子整局无无限用卡',()=>{
 let s=withCards();s={...s,currentPlayerIndex:1,players:s.players.map((p,i)=>i===1?{...p,cards:{reward:1,stride:1}}:p)};
 assert.equal(chooseComputerAction(s).type,'use_card');
 s=act(s,chooseComputerAction(s)).state;
 assert.equal(chooseComputerAction(s).cardType,'stride');
 s=act(s,chooseComputerAction(s)).state;
 assert.equal(chooseComputerAction(s).type,'roll');
 for(let i=0;i<100;i++){const r=runSimulation(i);assert.equal(r.finalState.status,'finished');assert.ok(r.actions<720);}
});
