import test from 'node:test';
import assert from 'node:assert/strict';
import { applyAction, createGame } from '../dist/core/game.js';
import { chooseComputerAction } from '../dist/core/agent.js';
function computerTurn(seed=17) {
  const s=applyAction(createGame(seed),{type:'start_game',actorId:'p1'}).state;
  return {...s,currentPlayerIndex:1};
}
test('仅轮到电脑时会执行合法指令，人类仍由用户操作',()=>{
  const human=applyAction(createGame(3),{type:'start_game',actorId:'p1'}).state;
  assert.equal(chooseComputerAction(human),null);
  const state=computerTurn();
  assert.deepEqual(chooseComputerAction(state),{type:'roll',actorId:'p2'});
  const arrived=applyAction(state,{type:'roll',actorId:'p2'}).state;
  const act=chooseComputerAction(arrived);
  assert.equal(act.actorId,'p2');
  assert.notEqual(act.type,'roll');
  assert.equal(chooseComputerAction({...arrived,status:'finished',phase:'finished'}),null);
});
test('预留现金200的决策边界，可配置阈值，不改动余额或棋盘',()=>{
  const s=computerTurn();
  const s2={...s,phase:'await_decision',
    players:s.players.map((p,i)=>i===1?{...p,position:1,cash:450}:p),
    tiles:s.tiles.map((t,i)=>i===1?{...t,price:250,ownerId:null}:t)};
  const before=JSON.stringify(s2);
  assert.equal(chooseComputerAction(s2).type,'buy_property');
  const low={...s2,players:s2.players.map((p,i)=>i===1?{...p,cash:449}:p)};
  assert.equal(chooseComputerAction(low).type,'decline_property');
  assert.equal(chooseComputerAction(low,{reserveCash:199}).type,'buy_property');
  assert.equal(chooseComputerAction({...s2,phase:'await_end_turn'}).type,'end_turn');
  assert.throws(()=>chooseComputerAction(s2,{reserveCash:-1}),/保留资金/);
  assert.equal(JSON.stringify(s2),before);
});
