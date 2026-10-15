import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, applyAction, nextDie, DEFAULT_CONFIG, netWorth } from '../dist/core/game.js';

const act = (s, type, actorId = s.players[s.currentPlayerIndex].id) => applyAction(s, { type, actorId });
function ok(s, type) { const r = act(s,type); assert.equal(r.ok,true,type+': '+r.reason); return r.state; }
function start(seed=1,config=DEFAULT_CONFIG) { return ok(createGame(seed, config),'start_game'); }
function atTile(state, tileId, actorIndex=state.currentPlayerIndex) {
  const roll=nextDie(state.randomState).value;
  return { ...state, players:state.players.map((p,i)=>i===actorIndex?{...p,position:(tileId-roll+state.tiles.length)%state.tiles.length}:p) };
}
function afterLanding(state,tileId) { return ok(atTile(state,tileId),'roll'); }

test('购买未归属地产：扣买方现金、赋权且生成准确交易事件，原始状态不变', () => {
  const s=afterLanding(start(),1), before=JSON.stringify(s), tile=s.tiles[1];
  assert.equal(s.phase,'await_decision');
  const result=act(s,'buy_property');
  assert.equal(result.ok,true);
  assert.equal(result.state.players[0].cash,1500-tile.price);
  assert.equal(result.state.tiles[1].ownerId,'p1');
  assert.equal(result.state.phase,'await_end_turn');
  assert.deepEqual(result.events.map(e=>e.type),['property_bought']);
  assert.equal(result.events[0].details.amount,tile.price);
  assert.equal(result.events[0].details.tileId,1);
  assert.equal(JSON.stringify(s),before);
});

test('放弃购买不扣钱；余额不足拒绝且允许随后放弃', () => {
  const config={...DEFAULT_CONFIG,initialCash:15};
  const s=afterLanding(start(1,config),1);
  const frozen=JSON.stringify(s);
  const fail=act(s,'buy_property');
  assert.equal(fail.ok,false);
  assert.equal(fail.reason,'INSUFFICIENT_FUNDS');
  assert.strictEqual(fail.state,s);
  assert.deepEqual(fail.events,[]);
  assert.equal(JSON.stringify(s),frozen);
  const declined=act(s,'decline_property');
  assert.equal(declined.ok,true);
  assert.equal(declined.state.players[0].cash,15);
  assert.equal(declined.state.tiles[1].ownerId,null);
  assert.equal(declined.state.phase,'await_end_turn');
});

test('到达自己拥有的地产不会重复付款或再次触发购买', () => {
  const b=start();
  const s=atTile(b,1);
  const owned={...s,tiles:s.tiles.map(t=>t.id===1?{...t,ownerId:'p1'}:t)};
  const rolled=act(owned,'roll');
  assert.equal(rolled.ok,true);
  assert.equal(rolled.state.phase,'await_end_turn');
  assert.equal(rolled.state.players[0].cash,1500);
  assert.equal(rolled.events.some(e=>e.type==='rent_paid'),false);
  assert.equal(act(rolled.state,'buy_property').reason,'INVALID_PHASE');
});

test('到达对手地产自动结算租金且仅执行一次：买方扣款、产权方收款', () => {
  const b=start();
  const s=atTile(b,1);
  const owned={...s,tiles:s.tiles.map(t=>t.id===1?{...t,ownerId:'p2'}:t)};
  const rolled=act(owned,'roll');
  const rent=owned.tiles[1].rent;
  assert.equal(rolled.ok,true);
  assert.equal(rolled.state.phase,'await_end_turn');
  assert.equal(rolled.state.players[0].cash,1500-rent);
  assert.equal(rolled.state.players[1].cash,1500+rent);
  assert.equal(rolled.state.players.reduce((sum,p)=>sum+p.cash,0),3000);
  const rentEvent=rolled.events.find(e=>e.type==='rent_paid');
  assert.equal(rentEvent.details.amount,rent);
  assert.equal(rentEvent.details.fromId,'p1');
  assert.equal(rentEvent.details.toId,'p2');
  assert.equal(act(rolled.state,'roll').reason,'INVALID_PHASE');
  assert.equal(act(rolled.state,'buy_property').reason,'INVALID_PHASE');
  const ended=ok(rolled.state,'end_turn');
  assert.equal(ended.players[0].cash,1500-rent);
  assert.equal(ended.players[1].cash,1500+rent);
});

test('租金不足时即时破产：有限额转移余额、不记负债、不出现负钱、直接判另一方获胜',()=>{
  const base=start();
  const at=atTile(base,1);
  const owned={...at,
    players:at.players.map((p,i)=>i===0?{...p,cash:5}:p),
    tiles:at.tiles.map(t=>t.id===1?{...t,ownerId:'p2',rent:100}:t)};
  const rolled=act(owned,'roll');
  assert.equal(rolled.ok,true);
  assert.equal(rolled.state.status,'finished');
  assert.equal(rolled.state.phase,'finished');
  assert.equal(rolled.state.winnerId,'p2');
  assert.equal(rolled.state.players[0].cash,0);
  assert.equal(rolled.state.players[0].bankrupt,true);
  assert.equal(rolled.state.players[1].cash,1505);
  assert.equal(rolled.events.find(e=>e.type==='rent_paid').details.amount,5);
  assert.equal(rolled.events.find(e=>e.type==='rent_paid').details.due,100);
  assert.ok(rolled.events.some(e=>e.type==='player_bankrupt'));
  assert.ok(rolled.events.some(e=>e.type==='game_finished'));
  assert.equal(act(rolled.state,'end_turn').reason,'INVALID_PHASE');
});

test('第 60 轮结束按净资产（现金+地价）判赢家；双方同分判平局',()=>{
  const b=start(), owned=[...b.tiles];
  owned[1]={...owned[1],ownerId:'p2',price:300};
  const at={...b,phase:'await_end_turn',round:60,currentPlayerIndex:1,tiles:owned};
  assert.equal(netWorth(at,'p1'),1500);
  assert.equal(netWorth(at,'p2'),1800);
  const finish=act(at,'end_turn');
  assert.equal(finish.ok,true);
  assert.equal(finish.state.status,'finished');
  assert.equal(finish.state.winnerId,'p2');
  assert.equal(finish.events.at(-1).type,'game_finished');
  const tied={...at,tiles:b.tiles};
  const draw=act(tied,'end_turn');
  assert.equal(draw.ok,true);
  assert.equal(draw.state.winnerId,null);
  assert.equal(draw.events.at(-1).details.reason,'round_limit');
  assert.equal(draw.events.at(-1).details.draw,1);
  assert.equal(act(draw.state,'end_turn').reason,'INVALID_PHASE');
});

test('资产计算使用可配置价格，且不替其他人的资产计价',()=>{
  let s=createGame(3);
  assert.equal(netWorth(s,'p1'),1500);
  s={...s,tiles:s.tiles.map(t=>t.id===1?{...t,ownerId:'p1',price:678}:t)};
  assert.equal(netWorth(s,'p1'),2178);
  assert.equal(netWorth(s,'p2'),1500);
});

test('100 种固定种子自动对局均能结束，动作合法、余额与产权有效，重复运行完全一致',()=>{
  function simulate(seed){
    let s=start(seed); let actions=0;
    while(s.status!=='finished'&&actions<400){
      if(s.phase==='await_roll')s=ok(s,'roll');
      else if(s.phase==='await_decision'){
        const buyer=s.players[s.currentPlayerIndex],land=s.tiles[buyer.position];
        s=ok(s,buyer.cash>=land.price+100?'buy_property':'decline_property');
      }else if(s.phase==='await_end_turn')s=ok(s,'end_turn');
      else assert.fail('状态机卡在 '+s.phase);
      assert.ok(s.players.every(p=>p.cash>=0),'不得出现负余额');
      assert.ok(s.tiles.every(t=>t.ownerId===null||s.players.some(p=>p.id===t.ownerId)),'不得有未知产权');
      actions++;
    }
    assert.equal(s.status,'finished');
    assert.ok(actions<=400);
    return s;
  }
  for(const seed of Array.from({length:100},(_,i)=>i)){
    assert.deepEqual(simulate(seed),simulate(seed),'随机种子 '+seed+' 不可重复');
  }
});
