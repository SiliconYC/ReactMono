import test from 'node:test';
import assert from 'node:assert/strict';
import {createGame,applyAction,nextDie,netWorth,DEFAULT_CONFIG} from '../dist/core/game.js';
import {serializeGame,deserializeGame} from '../dist/core/save.js';
import {chooseComputerAction} from '../dist/core/agent.js';
const action=(s,type,tileId)=>applyAction(s,{type,actorId:s.players[s.currentPlayerIndex].id,...(tileId===undefined?{}:{tileId})});
const ok=r=>{assert.equal(r.ok,true,r.reason);return r.state};
const started=(seed=1,config=DEFAULT_CONFIG)=>ok(action(createGame(seed,config),'start_game'));
function buyFirst(){let s=started();let die=nextDie(s.randomState).value;s={...s,players:s.players.map((p,i)=>i===0?{...p,position:(1-die+s.tiles.length)%s.tiles.length}:p)};s=ok(action(s,'roll'));return ok(action(s,'buy_property'));}
test('地产升级逐级扣款、分级收租、净资产，并且输入保持不可变',()=>{
  let s=buyFirst();const cash=s.players[0].cash,base=netWorth(s,'p1'),costs=s.tiles[1].upgradeCosts;
  const snap=JSON.stringify(s);
  s=ok(action(s,'upgrade_property',1));
  assert.equal(s.tiles[1].level,1);assert.equal(s.players[0].cash,cash-costs[0]);assert.equal(netWorth(s,'p1'),base);
  assert.equal(JSON.stringify(buyFirst()),snap);
  s=ok(action(s,'upgrade_property',1));assert.equal(s.tiles[1].level,2);
  assert.equal(s.players[0].cash,cash-costs[0]-costs[1]);
  assert.equal(action(s,'upgrade_property',1).ok,false);
  const rent=s.tiles[1].levelRents[2];
  const die=nextDie(s.randomState).value;
  const opponent={...s,currentPlayerIndex:1,phase:'await_roll',players:s.players.map((p,i)=>i===1?{...p,position:(1-die+s.tiles.length)%s.tiles.length}:p)};
  const landing=action(opponent,'roll');assert.equal(landing.ok,true);
  assert.equal(landing.events.find(e=>e.type==='rent_paid').details.due,rent);
  assert.equal(action(landing.state,'roll').ok,false);
});
test('无主、对手、满级、错误阶段、缺钱一律拒绝且不可变',()=>{
  const purchased=buyFirst(), first=started(), other={...purchased,currentPlayerIndex:1};
  for(const [s,id] of [[first,1],[purchased,2],[other,1],[purchased,999]]) {
    const before=JSON.stringify(s);const r=action(s,'upgrade_property',id);
    assert.equal(r.ok,false);assert.strictEqual(r.state,s);assert.equal(JSON.stringify(s),before);
  }
  const low={...purchased,players:purchased.players.map((p,i)=>i===0?{...p,cash:0}:p)};
  assert.equal(action(low,'upgrade_property',1).reason,'INSUFFICIENT_FUNDS');
  assert.equal(action({...purchased,phase:'await_roll'},'upgrade_property',1).reason,'INVALID_PHASE');
});
test('电脑在现金保留阈值以内选择确定升级，存档往返保留所有级别和价格',()=>{
  let s=buyFirst();
  s={...s,currentPlayerIndex:1,players:s.players.map((p,i)=>i===1?{...p,cash:1000}:p),
    tiles:s.tiles.map((t,i)=>i===1?{...t,ownerId:'p2'}:t)};
  const ai=chooseComputerAction(s,{reserveCash:200});assert.equal(ai.type,'upgrade_property');
  assert.equal(ai.tileId,1);
  s=ok(applyAction(s,ai));
  const raw=serializeGame(s),saved=deserializeGame(raw);
  assert.deepEqual(saved.game,s);
  assert.equal(saved.game.tiles[1].level,1);
  assert.equal(saved.game.tiles[1].upgradeCosts[0],s.tiles[1].upgradeCosts[0]);
});
