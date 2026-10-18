import test from 'node:test';
import assert from 'node:assert/strict';
import {createGame,applyAction,DEFAULT_CONFIG,HARBOR_CONFIG,nextDie} from '../.test-dist/core/game.js';
import {serializeGame,deserializeGame,SaveError} from '../.test-dist/core/save.js';
import {runSimulation} from '../.test-dist/core/simulator.js';
const cfg=(base=DEFAULT_CONFIG,extra={})=>({...base,strategyEnabled:true,specialEnabled:true,bankEnabled:true,loanEnabled:true,marketEnabled:true,automaticLiquidation:true,...extra});
const start=(seed=17,base=DEFAULT_CONFIG,extra={})=>{
 const s=createGame(seed,cfg(base,extra));
 return applyAction(s,{type:'start_game',actorId:s.players[0].id}).state;
};
const act=(s,action)=>applyAction(s,{actorId:s.players[s.currentPlayerIndex].id,...action});
const remote=(s,dieValue)=>act({...s,players:s.players.map((p,i)=>i===s.currentPlayerIndex?{...p,cards:{...p.cards,remote:1}}:p)},{type:'use_card',cardType:'remote',dieValue}).state;
test('2 maps hospital/prison/shop recognized; opt-in legacy map retains P2 opportunity and card station',()=>{
 for(const base of [DEFAULT_CONFIG,HARBOR_CONFIG]){
  const s=start(17,base);
  assert.equal(s.tiles[3].facility,'hospital');
  assert.equal(s.tiles[9].facility,'prison');
  assert.equal(s.tiles[12].facility,'shop');
  assert.equal(s.tiles[3].eventBonus,undefined);
  assert.equal(s.shops.length,1);
  const legacy=createGame(17,base);
  assert.equal(legacy.tiles[3].facility,undefined);
  assert.equal(legacy.tiles[3].eventBonus,120);
  assert.equal(legacy.tiles[12].cardStation,true);
  assert.deepEqual(deserializeGame(serializeGame(legacy)).game,legacy);
 }
});
test('hospital skip countdown, multi-player switching, release and ability to roll only afterwards',()=>{
 let s=remote(start(),3);
 const landing=act(s,{type:'roll'});
 assert.equal(landing.ok,true);
 s=landing.state;
 assert.equal(s.players[0].position,3);
 assert.deepEqual(s.players[0].detention,{kind:'hospital',remaining:2});
 assert.equal(s.players[0].cash,1450);
 assert.equal(s.phase,'await_end_turn');
 assert.deepEqual(deserializeGame(serializeGame(s)).game,s);
 s=act(s,{type:'end_turn'}).state;
 assert.equal(s.currentPlayerIndex,1);
 // Return to player 1 after opponent turn; opponent should not alter detention.
 s={...s,currentPlayerIndex:0,phase:'await_roll'};
 assert.equal(act(s,{type:'roll'}).ok,false);
 assert.equal(act(s,{type:'use_card',cardType:'reward'}).ok,false);
 let skip=act(s,{type:'skip_turn'});
 assert.equal(skip.ok,true);
 assert.deepEqual(skip.events.map(e=>e.type).slice(0,2),['detention_skipped','turn_ended']);
 assert.equal(skip.state.players[0].detention.remaining,1);
 s={...skip.state,currentPlayerIndex:0,phase:'await_roll'};
 skip=act(s,{type:'skip_turn'});
 assert.equal(skip.ok,true);
 assert.equal(skip.state.players[0].detention,undefined);
 assert.ok(skip.events.some(e=>e.type==='detention_released'));
 s={...skip.state,currentPlayerIndex:0,phase:'await_roll'};
 assert.equal(act(s,{type:'skip_turn'}).ok,false);
 assert.equal(act(s,{type:'roll'}).ok,true);
});
test('prison has own turns and entry fee and keeps multiplayer money valid',()=>{
 let s=start(9);
 s={...s,players:s.players.map((p,i)=>i===0?{...p,position:6}:p)};
 s=remote(s,3);
 const r=act(s,{type:'roll'});
 assert.equal(r.ok,true);
 assert.deepEqual(r.state.players[0].detention,{kind:'prison',remaining:3});
 assert.equal(r.state.players[0].cash,1420);
 assert.deepEqual(deserializeGame(serializeGame(r.state)).game,r.state);
});
test('shop purchase obeys stock, hand limit, funds; return to end turn; illegal remains unchanged',()=>{
 let s=start(43);
 s={...s,players:s.players.map((p,i)=>i===0?{...p,position:6}:p)};
 s=remote(s,6);
 s=act(s,{type:'roll'}).state;
 assert.equal(s.phase,'await_shop');
 assert.equal(s.players[0].position,12);
 const illegal=[
  {type:'buy_shop_card',cardType:'fake'},
  {type:'roll'},{type:'skip_turn'},{type:'buy_shop_card',cardType:'reward',actorId:'p2'}
 ];
 for(const action of illegal){
  const r=act(s,action);assert.equal(r.ok,false);assert.strictEqual(r.state,s);
 }
 const beforeCash=s.players[0].cash;
 const r=act(s,{type:'buy_shop_card',cardType:'remote'});
 assert.equal(r.ok,true);
 assert.equal(r.state.players[0].cash,beforeCash-210);
 assert.equal(r.state.players[0].cards.remote,1);
 assert.equal(r.state.shops[0].cards.remote,1);
 assert.deepEqual(deserializeGame(serializeGame(r.state)).game,r.state);
 s=r.state;
 s=act(s,{type:'buy_shop_card',cardType:'remote'}).state;
 assert.equal(s.shops[0].cards.remote,0);
 assert.equal(act(s,{type:'buy_shop_card',cardType:'remote'}).ok,false);
 const last=act(s,{type:'leave_shop'});
 assert.equal(last.ok,true);assert.equal(last.state.phase,'await_end_turn');
 assert.equal(act(last.state,{type:'buy_shop_card',cardType:'reward'}).ok,false);
});
test('invalid facility config and forged shop/phase/detention save are rejected',()=>{
 assert.throws(()=>createGame(3,{...cfg(),facilityConfig:{hospitalTiles:[4],prisonTiles:[9],shopTiles:[12],hospitalTurns:2,prisonTurns:3,hospitalFee:50,prisonFee:80,prices:{reward:1,stride:1,remote:1,roadblock:1,rent_free:1},stock:{reward:1,stride:1,remote:1,roadblock:1,rent_free:1}}}));
 const s=start();
 for(const forged of [
   {...s,phase:'await_shop'},
   {...s,shops:[{...s.shops[0],tileId:9}]},
   {...s,players:s.players.map((p,i)=>i===0?{...p,detention:{kind:'hospital',remaining:22}}:p)},
   {...s,tiles:s.tiles.map(t=>t.id===3?{...t,facility:'fake'}:t)}
 ])assert.throws(()=>serializeGame(forged),e=>e instanceof SaveError&&e.code==='INVALID_STATE');
});
test('100 seeded complete multiplayer facility games on both maps',()=>{
 for(let seed=1;seed<=100;seed++){
  const base=seed%2===0?HARBOR_CONFIG:DEFAULT_CONFIG;
  const config=cfg(base,{maxRounds:12,players:[
   {id:'p1',name:'甲',kind:'computer'},{id:'p2',name:'乙',kind:'computer'},
   ...(seed%3===0?[{id:'p3',name:'丙',kind:'computer'},{id:'p4',name:'丁',kind:'computer'}]:[])]});
  const r=runSimulation(seed,{config,maxActions:1000});
  assert.equal(r.finalState.status,'finished');
  assert.equal(r.rejections,0);
  assert.ok(r.actions<=1000);
  assert.deepEqual(deserializeGame(serializeGame(r.finalState)).game,r.finalState);
 }
});
