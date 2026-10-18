import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, applyAction, DEFAULT_CONFIG } from '../.test-dist/core/game.js';
import { choosePhaseAction } from '../.test-dist/core/agent.js';
import { runSimulation } from '../.test-dist/core/simulator.js';
import { deserializeGame, serializeGame, SaveError } from '../.test-dist/core/save.js';

const players = n => Array.from({length:n}, (_,i)=>({
  id:'p'+(i+1), name:'玩家'+(i+1), kind:i===0?'human':i%2?'computer':'human'
}));
const config = n => ({...DEFAULT_CONFIG,players:players(n),maxRounds:16});
const ok = (s,type,more={}) => {
  const r=applyAction(s,{type,actorId:s.players[s.currentPlayerIndex].id,...more});
  assert.equal(r.ok,true,'action '+type+': '+(r.reason??'')); return r.state;
};
function checksum(data) {let h=0x811c9dc5;for(let i=0;i<data.length;i++){h^=data.charCodeAt(i);h=Math.imul(h,0x01000193);}return(h>>>0).toString(16).padStart(8,'0')}

test('P3-02: 2 to 4 configurable player kinds and illegal configs', () => {
  for (const n of [2,3,4]) {
    const s=createGame(77,config(n));
    assert.equal(s.players.length,n);
    assert.deepEqual(s.players.map(p=>p.kind),players(n).map(p=>p.kind));
    assert.equal(s.schemaVersion,4);
  }
  for (const n of [1,5]) assert.throws(()=>createGame(1,config(n)),/玩家/);
  assert.throws(()=>createGame(1,{...config(3),players:[...players(2),{...players(2)[0]}]}),/玩家/);
  assert.throws(()=>createGame(1,{...config(3),players:[...players(2),{id:'z',name:'坏',kind:'alien'}]}),/玩家/);
});

test('P3-02: three-player bankruptcy removes one participant without ending the game', () => {
  const c={...config(3),initialCash:100,maxRounds:6,tiles:[
    {id:0,kind:'start',title:'起点'},
    {id:1,kind:'property',title:'高租地',price:20,rent:500}
  ]};
  let s=ok(createGame(2,c),'start_game');
  s=ok(s,'roll'); assert.equal(s.phase,'await_decision');
  s=ok(s,'buy_property');s=ok(s,'end_turn');
  assert.equal(s.currentPlayerIndex,1);
  s=ok(s,'roll');
  assert.equal(s.players[1].bankrupt,true);
  assert.equal(s.status,'playing');
  assert.equal(s.currentPlayerIndex,2);
  assert.equal(s.phase,'await_roll');
  assert.equal(s.players[0].cash,180);
  assert.equal(s.players[1].cash,0);
  assert.equal(s.players[1].position,1);
  assert.equal(s.events.filter(e=>e.type==='rent_paid').length,1);
  assert.equal(s.events.filter(e=>e.type==='player_bankrupt').length,1);
  assert.equal(s.events.filter(e=>e.type==='game_finished').length,0);
  for(let i=0;i<2000&&s.status!=='finished';i++){
    const a=choosePhaseAction(s,300);
    assert.ok(a);
    s=ok(s,a.type,Object.fromEntries(Object.entries(a).filter(([key])=>!['type','actorId'].includes(key))));
    if(s.status!=='finished')assert.equal(s.players[s.currentPlayerIndex].bankrupt,false);
  }
  assert.equal(s.status,'finished');
  assert.ok(s.events.some(e=>e.type==='game_finished'));
});

test('P3-02: 100 deterministic complete games for each of 2/3/4 players', () => {
  for(const n of [2,3,4]){
    const cfg=config(n);
    for(let seed=0;seed<100;seed++){
      const a=runSimulation(seed,{config:cfg,maxActions:3000});
      const b=runSimulation(seed,{config:cfg,maxActions:3000});
      assert.equal(a.finalState.status,'finished');
      assert.deepEqual(a.finalState,b.finalState,'n='+n+' seed='+seed);
      assert.equal(a.rejections,0);
      assert.ok(a.finalState.players.every(p=>p.cash>=0&&Number.isSafeInteger(p.cash)));
      assert.ok(a.finalState.tiles.every(t=>t.ownerId===null||a.finalState.players.some(p=>p.id===t.ownerId&&!p.bankrupt)));
    }
  }
});

test('P3-02: legacy v2 two-player save upgrades to v3 without lost property, events or PRNG state', () => {
  let current=ok(createGame(31),'start_game');
  current=ok(current,'roll');
  const old={...current,schemaVersion:2};delete old.map;
  const payload={format:'reactmono-save',formatVersion:1,rulesVersion:2,
    createdAt:'2026-10-15T00:00:00.000Z',updatedAt:'2026-10-15T00:00:00.000Z',game:old};
  const imported=deserializeGame(JSON.stringify({...payload,checksum:checksum(JSON.stringify(payload))}));
  assert.equal(imported.rulesVersion,4);
  assert.equal(imported.game.schemaVersion,4);
  const {map,...recovered}=imported.game;
  assert.deepEqual({...recovered,schemaVersion:2},old);
  assert.deepEqual(deserializeGame(serializeGame(imported.game)).game,imported.game);
});
