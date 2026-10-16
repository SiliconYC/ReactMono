import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, applyAction, DEFAULT_CONFIG, nextDie } from '../dist/core/game.js';
import { DEFAULT_MAP, INTERNAL_TEST_MAP, advancePosition, inferMap, validateMap } from '../dist/core/maps.js';
import { serializeGame, deserializeGame } from '../dist/core/save.js';
const tiles=length=>Array.from({length},(_,i)=>i===0?{id:i,kind:'start',title:'起点'}
  :i%3===0?{id:i,kind:'neutral',title:'休息站'+i}
  :{id:i,kind:'property',title:'地产'+i,price:100+i*10,rent:20+i*2});
function checksum(data){let h=0x811c9dc5;for(let i=0;i<data.length;i++){h^=data.charCodeAt(i);h=Math.imul(h,0x01000193);}return(h>>>0).toString(16).padStart(8,'0')}

test('P3-04: 24-cell map exactly reproduces the P2 ring, 5x5 internal map differs',()=>{
  assert.equal(DEFAULT_MAP.id,'classic-24');
  assert.equal(DEFAULT_MAP.cells.length,24);
  assert.deepEqual(DEFAULT_MAP.cells[0],{column:1,row:1});
  assert.deepEqual(DEFAULT_MAP.cells[7],{column:8,row:1});
  assert.deepEqual(DEFAULT_MAP.cells[8],{column:8,row:2});
  assert.deepEqual(DEFAULT_MAP.cells[11],{column:8,row:5});
  assert.deepEqual(DEFAULT_MAP.cells[12],{column:8,row:6});
  assert.deepEqual(DEFAULT_MAP.cells[19],{column:1,row:6});
  assert.deepEqual(DEFAULT_MAP.cells[20],{column:1,row:5});
  assert.deepEqual(DEFAULT_MAP.cells[23],{column:1,row:2});
  assert.equal(INTERNAL_TEST_MAP.cells.length,16);
  assert.equal(INTERNAL_TEST_MAP.columns,5);
  assert.equal(INTERNAL_TEST_MAP.rows,5);
  assert.equal(validateMap(DEFAULT_MAP,24),undefined);
  assert.equal(validateMap(INTERNAL_TEST_MAP,16),undefined);
  for(let tile=0;tile<24;tile++)for(let steps=0;steps<50;steps++)
    assert.equal(advancePosition(DEFAULT_MAP,tile,steps),(tile+steps)%24);
});
test('P3-04: internal 16-cell path wraps start correctly and preserves deterministic RNG',()=>{
  const config={...DEFAULT_CONFIG,tiles:tiles(16),map:INTERNAL_TEST_MAP,maxRounds:10};
  let a=createGame(2,config),b=createGame(2,config);
  assert.equal(a.map.id,INTERNAL_TEST_MAP.id);
  assert.deepEqual(a,b);
  for(const step of [0,1,6,15,16,17,35,1024])assert.equal(advancePosition(INTERNAL_TEST_MAP,15,step),(15+step)%16);
  a=applyAction(a,{type:'start_game',actorId:'p1'}).state;
  b=applyAction(b,{type:'start_game',actorId:'p1'}).state;
  const die=nextDie(a.randomState);
  a=applyAction(a,{type:'roll',actorId:'p1'}).state;
  b=applyAction(b,{type:'roll',actorId:'p1'}).state;
  assert.equal(a.players[0].position,die.value);
  assert.deepEqual(a,b);
  assert.equal(deserializeGame(serializeGame(a)).game.map.id,INTERNAL_TEST_MAP.id);
});
test('P3-04: invalid layout, overlapping cells, disconnected path and unsupported map reject',()=>{
  const base={...DEFAULT_CONFIG,map:DEFAULT_MAP};
  const invalid=[
    {...DEFAULT_MAP,route:[...DEFAULT_MAP.route.slice(0,23),0]},
    {...DEFAULT_MAP,route:[...DEFAULT_MAP.route].reverse()},
    {...DEFAULT_MAP,cells:[...DEFAULT_MAP.cells.slice(0,23),DEFAULT_MAP.cells[0]]},
    {...DEFAULT_MAP,cells:[...DEFAULT_MAP.cells.slice(0,23),{column:100,row:1}]},
    {...DEFAULT_MAP,version:99},
    {...DEFAULT_MAP,id:'bad-external-map'}
  ];
  for(const map of invalid)assert.throws(()=>createGame(1,{...base,map}),/地图/);
  assert.throws(()=>createGame(1,{...DEFAULT_CONFIG,tiles:tiles(16),map:DEFAULT_MAP}),/地图/);
});
test('P3-04: old v3 save migrates map metadata, player state, RNG and action reproducibly',()=>{
  const state=applyAction(createGame(42),{type:'start_game',actorId:'p1'}).state;
  const old={...state,schemaVersion:3};delete old.map;
  const payload={format:'reactmono-save',formatVersion:1,rulesVersion:3,
    createdAt:'2026-10-15T00:00:00.000Z',updatedAt:'2026-10-15T00:00:00.000Z',game:old};
  const decoded=deserializeGame(JSON.stringify({...payload,checksum:checksum(JSON.stringify(payload))}));
  assert.equal(decoded.rulesVersion,4);
  assert.equal(decoded.game.map.id,DEFAULT_MAP.id);
  assert.deepEqual({...decoded.game,schemaVersion:3,map:undefined},
    {...old,map:undefined});
  assert.equal(decoded.game.randomState,state.randomState);
  assert.deepEqual(deserializeGame(serializeGame(decoded.game)).game,decoded.game);
});
