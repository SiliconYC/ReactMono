import test from 'node:test';
import assert from 'node:assert/strict';
import {createGame, applyAction, DEFAULT_CONFIG, DEFAULT_CARD_RULES, DEFAULT_EVENT_RULES, resaleValue, netWorth} from '../dist/core/game.js';
import {serializeGame, deserializeGame} from '../dist/core/save.js';
import {runSimulation} from '../dist/core/simulator.js';

const tiles=[
  {id:0,kind:'start',title:'起点'},
  {id:1,kind:'property',title:'高租地',price:100,rent:120},
  {id:2,kind:'property',title:'储备地',price:200,rent:15},
  {id:3,kind:'property',title:'小地',price:50,rent:10}
];
const config=(count=2)=>({...DEFAULT_CONFIG,tiles,initialCash:100,maxRounds:8,automaticLiquidation:true,
  eventRules:{...DEFAULT_EVENT_RULES,tileIds:[]},cardRules:{...DEFAULT_CARD_RULES,tileIds:[]},
  players:Array.from({length:count},(_,i)=>({id:'p'+(i+1),name:'玩家'+(i+1),kind:'human'}))});
const base=(count=2)=>createGame(2,config(count));
const setup=(count=2)=>{const s=base(count);return {...s,status:'playing',phase:'await_roll',
  currentPlayerIndex:1,
  tiles:s.tiles.map(t=>t.id===1?{...t,ownerId:'p1'}:t.id===2?{...t,ownerId:'p2'}:t),
  players:s.players.map((p,i)=>i===1?{...p,cash:10}:p)};
};
test('P3-06: selling upgraded property uses transparent floor(75% land+50% upgrades)',()=>{
  const s=base(),t=s.tiles[2];
  assert.equal(resaleValue(t),150);
  assert.equal(resaleValue({...t,level:1}),200);
  const prepared={...s,status:'playing',phase:'await_end_turn',
    tiles:s.tiles.map(x=>x.id===2?{...x,ownerId:'p1',level:1}:x)};
  const before=netWorth(prepared,'p1');
  const r=applyAction(prepared,{type:'sell_property',actorId:'p1',tileId:2});
  assert.equal(r.ok,true);
  assert.equal(r.state.players[0].cash,s.players[0].cash+200);
  assert.equal(r.state.tiles[2].ownerId,null);
  assert.equal(r.state.tiles[2].level,0);
  assert.equal(netWorth(r.state,'p1'),before-100);
  assert.equal(r.events[0].type,'property_sold');
  assert.deepEqual(deserializeGame(serializeGame(r.state)).game,r.state);
});
test('P3-06: configured resale rates are validated and persisted without changing old defaults',()=>{
  const land=base().tiles[2];
  assert.equal(resaleValue(land,{landPercent:0.5,upgradePercent:0.2}),100);
  assert.equal(resaleValue({...land,level:1},{landPercent:0.5,upgradePercent:0.2}),120);
  const rules={landPercent:0.5,upgradePercent:0.2};
  const s=createGame(1,{...config(),resaleRules:rules});
  assert.deepEqual(s.resaleRules,rules);
  assert.deepEqual(deserializeGame(serializeGame(s)).game,s);
  assert.throws(()=>createGame(1,{...config(),resaleRules:{landPercent:2,upgradePercent:0.5}}),/折价/);
});
test('P3-06: sale rejects phases, other owners, invalid IDs without state changes',()=>{
  const s=setup();
  for(const [action,prepared] of [
    [{type:'sell_property',actorId:'p2',tileId:1},s],
    [{type:'sell_property',actorId:'p2',tileId:-1},{...s,phase:'await_end_turn'}],
    [{type:'sell_property',actorId:'p2',tileId:1},{...s,phase:'await_end_turn'}]
  ]){
    const r=applyAction(prepared,action);
    assert.equal(r.ok,false);assert.equal(r.state,prepared);
  }
});
test('P3-06: rent liquidation sells owned assets before bankruptcy, no double rent',()=>{
  const s=setup();
  const r=applyAction(s,{type:'roll',actorId:'p2'});
  assert.equal(r.ok,true);
  assert.equal(r.state.players[1].bankrupt,false);
  assert.equal(r.state.players[1].cash,40);
  assert.equal(r.state.players[0].cash,220);
  assert.equal(r.state.tiles[2].ownerId,null);
  assert.equal(r.events.filter(e=>e.type==='property_liquidated').length,1);
  assert.equal(r.events.filter(e=>e.type==='rent_paid').length,1);
  assert.equal(r.events.filter(e=>e.type==='player_bankrupt').length,0);
});
test('P3-06: insufficient sale proceeds still bankrupt; remaining multiplayer keeps playing',()=>{
  const s=setup(3);
  const p2tiles=s.tiles.map(t=>t.id===2?{...t,ownerId:null}:t.id===3?{...t,ownerId:'p2'}:t);
  const r=applyAction({...s,tiles:p2tiles},{type:'roll',actorId:'p2'});
  assert.equal(r.ok,true);
  assert.equal(r.state.players[1].bankrupt,true);
  assert.equal(r.state.players[1].cash,0);
  assert.equal(r.state.tiles[3].ownerId,null);
  assert.equal(r.state.status,'playing');
  assert.equal(r.state.currentPlayerIndex,2);
  assert.ok(r.events.some(e=>e.type==='player_bankrupt'));
  assert.ok(r.events.find(e=>e.type==='rent_paid').details.amount<=120);
});
test('P3-06: old two-player simulations and 3/4 player runs remain terminating',()=>{
  for(const n of [2,3,4])for(let seed=0;seed<100;seed++){
    const cfg={...DEFAULT_CONFIG,players:config(n).players,maxRounds:16};
    const r=runSimulation(seed,{config:cfg,maxActions:3000});
    assert.equal(r.finalState.status,'finished');
    assert.equal(r.rejections,0);
    assert.ok(r.finalState.players.every(p=>p.cash>=0));
  }
});
