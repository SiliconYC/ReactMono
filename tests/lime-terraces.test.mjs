import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, applyAction } from '../.test-dist/core/game.js';
import { levelConfig } from '../.test-dist/core/level-data.js';
import { serializeGame, deserializeGame, validateGameState } from '../.test-dist/core/save.js';
import { propertyRun, propertyRent, quotePropertyUpgrade } from '../.test-dist/core/property-groups.js';
import { choosePhaseAction } from '../.test-dist/core/agent.js';
import { chooseStyledAction } from '../.test-dist/core/strategic-agent.js';

function fixture(levels=[0,0,0],landed=1,cash=3000,legacy=false) {
  const config={...levelConfig('lime-garden-30'),initialCash:3000,propertyVisitOnly:true,strategyEnabled:true,bankEnabled:true,loanEnabled:true,
    players:[{id:'p1',name:'玩家',kind:'human'},{id:'p2',name:'对手',kind:'human'}]};
  let state=applyAction(createGame(17,config),{type:'start_game',actorId:'p1'}).state;
  state={...state,phase:'await_end_turn',players:state.players.map(p=>p.id==='p1'?{...p,position:landed,cash}:p),
    tiles:state.tiles.map(t=>[1,2,3].includes(t.id)?{...t,ownerId:'p1',level:levels[t.id-1]}:t),
    events:[...state.events,{type:'die_rolled',actorId:'p1',details:{value:landed}}]};
  if(legacy){const {terraceRulesVersion,...rest}=state;state=rest;}
  return state;
}
function upgrade(state,id=state.players[0].position){return applyAction(state,{type:'upgrade_property',actorId:'p1',tileId:id});}

test('新青柠对局一次到访建设连续三块空地，扣总额并逐户留事件',()=>{
  const state=fixture(),result=upgrade(state);
  assert.equal(result.ok,true);
  assert.deepEqual(result.state.tiles.slice(1,4).map(t=>t.level),[1,1,1]);
  assert.equal(result.state.players[0].cash,2820);
  assert.deepEqual(result.events.map(e=>e.details.tileId),[1,2,3]);
  assert.equal(result.events.reduce((sum,e)=>sum+e.details.amount,0),180);
  assert.equal(upgrade(result.state).ok,false);
  assert.deepEqual(state.tiles.slice(1,4).map(t=>t.level),[0,0,0]);
});

test('满级房落点仍能补建最低邻居，保留先建房投资且不越级',()=>{
  let state=fixture([2,0,0]);
  let result=upgrade(state);
  assert.equal(result.ok,true);
  assert.deepEqual(result.state.tiles.slice(1,4).map(t=>t.level),[2,1,1]);
  assert.equal(result.state.players[0].cash,2880);
  state={...result.state,events:[...result.state.events,{type:'die_rolled',actorId:'p1',details:{value:1}}]};
  result=upgrade(state,3);
  assert.equal(result.ok,true);
  assert.deepEqual(result.state.tiles.slice(1,4).map(t=>t.level),[2,2,2]);
  assert.equal(result.state.players[0].cash,2688);
  assert.equal(upgrade({...result.state,events:[...result.state.events,{type:'die_rolled',actorId:'p1'}]}).ok,false);
});

test('钱只够一户不够整排时拒绝，所有产权与现金原样返回',()=>{
  const state=fixture([0,0,0],2,100),result=upgrade(state);
  assert.equal(result.ok,false);
  assert.equal(result.reason,'INSUFFICIENT_FUNDS');
  assert.strictEqual(result.state,state);
});

test('空置、对手与抵押中间地截断；出售和解除抵押实时改变分段',()=>{
  for(const middle of [{ownerId:null,level:0},{ownerId:'p2',level:0},{mortgaged:true}]){
    const base=fixture(),state={...base,tiles:base.tiles.map(t=>t.id===2?{...t,...middle}:t)};
    const result=upgrade(state);
    assert.equal(result.ok,true);
    assert.deepEqual(result.state.tiles.slice(1,4).map(t=>t.level),[1,0,0]);
  }
  const state=fixture([1,1,1]);
  const sold=applyAction(state,{type:'sell_property',actorId:'p1',tileId:2}).state;
  assert.deepEqual(upgrade(sold).state.tiles.slice(1,4).map(t=>t.level),[2,0,1]);
});

test('踩整排任一格一次收合计租金，混级也按实际等级计费，免租覆盖全部',()=>{
  for(const landed of [1,2,3])for(const waived of [false,true]){
    const base=fixture([2,0,1]);
    const state={...base,currentPlayerIndex:1,phase:'await_roll',pendingDie:landed,pendingRentWaiver:waived};
    const result=applyAction(state,{type:'roll',actorId:'p2'});
    assert.equal(result.ok,true);
    const rents=result.events.filter(e=>e.type==='rent_paid');
    assert.equal(rents.length,1);
    assert.equal(rents[0].details.due,waived?0:168);
    assert.equal(result.state.players[1].cash,waived?3000:2832);
    assert.equal(result.state.players[0].cash,waived?3000:3168);
    if(waived)assert.equal(result.events.find(e=>e.type==='rent_waived').details.amount,168);
  }
});

test('旧青柠存档仍逐格升级收费，新规则往返存档且拒绝跨地图或未知版本',()=>{
  const old=fixture([0,0,0],2,3000,true);
  const restored=deserializeGame(serializeGame(old)).game;
  assert.equal(restored.terraceRulesVersion,undefined);
  assert.deepEqual(upgrade(restored).state.tiles.slice(1,4).map(t=>t.level),[0,1,0]);
  const modern=fixture();
  assert.equal(modern.terraceRulesVersion,1);
  assert.deepEqual(deserializeGame(serializeGame(upgrade(modern).state)).game,upgrade(modern).state);
  assert.throws(()=>validateGameState({...modern,terraceRulesVersion:2}));
  assert.throws(()=>validateGameState({...createGame(1),terraceRulesVersion:1}));
});

test('基础、三种策略电脑使用整排总费用；满级落点能建邻居且不死循环',()=>{
  for(const cash of [100,1000])for(const style of [null,'conservative','balanced','aggressive']){
    const base=fixture([2,0,0],1,cash);
    const state={...base,players:base.players.map(p=>p.id==='p1'?{...p,kind:'computer'}:p)};
    const action=style?chooseStyledAction(state,style):choosePhaseAction(state,0);
    assert.ok(action);
    const result=applyAction(state,action);
    assert.equal(result.ok,true,JSON.stringify({cash,style,action}));
    if(cash===1000)assert.equal(action.type,'upgrade_property');
    else assert.notEqual(action.type,'upgrade_property');
  }
});

test('抵押中间地不收费并截断；解除抵押后恢复整排报价',()=>{
  const state=fixture([1,1,1]);
  const mortgage=applyAction(state,{type:'mortgage_property',actorId:'p1',tileId:2});
  assert.equal(mortgage.ok,true);
  assert.equal(propertyRent(mortgage.state,2),0);
  assert.equal(propertyRent(mortgage.state,1),48);
  assert.deepEqual(propertyRun(mortgage.state,1).map(t=>t.id),[1]);
  const release=applyAction(mortgage.state,{type:'release_mortgage',actorId:'p1',tileId:2});
  assert.equal(release.ok,true);
  assert.equal(propertyRent(release.state,1),144);
  assert.equal(quotePropertyUpgrade(release.state,1).cost,288);
  validateGameState(release.state);
});

test('购入中间空地接上两栋满级房，购买当次不得再建；下一次可从两端补建',()=>{
  const base=fixture([2,0,2],2);
  const state={...base,phase:'await_decision',tiles:base.tiles.map(t=>t.id===2?{...t,ownerId:null}:t)};
  const bought=applyAction(state,{type:'buy_property',actorId:'p1'});
  assert.equal(bought.ok,true);
  assert.equal(quotePropertyUpgrade(bought.state,1).cost,60);
  assert.equal(upgrade(bought.state).ok,false);
  const revisited={...bought.state,players:bought.state.players.map(p=>p.id==='p1'?{...p,position:3}:p),events:[...bought.state.events,{type:'die_rolled',actorId:'p1',details:{value:1}}]};
  const built=upgrade(revisited,1);
  assert.equal(built.ok,true);
  assert.deepEqual(built.state.tiles.slice(1,4).map(t=>t.level),[2,1,2]);
});

test('混级只提升最低层，未落在该经营单元不得远程建设',()=>{
  const state=fixture([0,1,2],3);
  assert.deepEqual(upgrade(state).state.tiles.slice(1,4).map(t=>t.level),[1,1,2]);
  const away={...state,players:state.players.map(p=>p.id==='p1'?{...p,position:5}:p)};
  assert.equal(upgrade(away,1).ok,false);
  const withOther={...state,tiles:state.tiles.map(t=>[5,6,7].includes(t.id)?{...t,ownerId:'p1'}:t)};
  assert.equal(upgrade(withOther,5).ok,false);
});

test('整排收费先用存款补款再清算，破产仅转移实付并释放全部产权',()=>{
  let state=fixture([2,2,2]);
  state={...state,currentPlayerIndex:1,phase:'await_roll',pendingDie:1,automaticLiquidation:true,
    players:state.players.map(p=>p.id==='p2'?{...p,cash:10,bankBalance:200}:p),
    tiles:state.tiles.map(t=>t.id===5?{...t,ownerId:'p2'}:t)};
  const rescued=applyAction(state,{type:'roll',actorId:'p2'});
  assert.equal(rescued.ok,true);
  assert.equal(rescued.state.status,'playing');
  assert.equal(rescued.state.players[1].cash,30);
  assert.equal(rescued.state.players[1].bankBalance,0);
  assert.equal(rescued.state.players[0].cash,3288);
  assert.equal(rescued.events.find(e=>e.type==='property_liquidated').details.amount,108);
  validateGameState(rescued.state);
  const poor={...state,automaticLiquidation:undefined,players:state.players.map(p=>p.id==='p2'?{...p,cash:10,bankBalance:0}:p)};
  const bankrupt=applyAction(poor,{type:'roll',actorId:'p2'});
  assert.equal(bankrupt.state.status,'finished');
  assert.equal(bankrupt.events.find(e=>e.type==='rent_paid').details.due,288);
  assert.equal(bankrupt.events.find(e=>e.type==='rent_paid').details.amount,10);
  assert.equal(bankrupt.state.players[0].cash,3010);
  assert.ok(!bankrupt.state.tiles.some(t=>t.ownerId==='p2'));
  validateGameState(bankrupt.state);
});

test('联排版本自身约束到访与每次一次，不依赖调用方额外开启旧到访开关',()=>{
  const base=fixture(),{propertyVisitOnly,...state}=base;
  assert.equal(upgrade(state).ok,true);
  assert.equal(upgrade(upgrade(state).state).ok,false);
  const away={...state,players:state.players.map(p=>({...p,position:5}))};
  assert.equal(upgrade(away,1).ok,false);
  const computer={...away,players:away.players.map(p=>({...p,kind:'computer'}))};
  const action=chooseStyledAction(computer,'balanced');
  assert.ok(action);
  assert.notEqual(action.type,'upgrade_property');
  assert.equal(applyAction(computer,action).ok,true);
});
