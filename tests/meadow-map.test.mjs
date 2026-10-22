import test from 'node:test';
import assert from 'node:assert/strict';
import { PLAYABLE_LEVELS, levelConfig } from '../.test-dist/core/level-data.js';
import { createGame } from '../.test-dist/core/game.js';
import { runSimulation } from '../.test-dist/core/simulator.js';
import { serializeGame, deserializeGame } from '../.test-dist/core/save.js';

test('青柠游园可开30格对局、完整结算并往返存档',()=>{
  assert.ok(PLAYABLE_LEVELS.some(l=>l.map.id==='lime-garden-30'));
  for(const seed of [17,31,88]){
    const config={...levelConfig('lime-garden-30'),maxRounds:12,players:[{id:'p1',name:'春风',kind:'computer'},{id:'p2',name:'青柠',kind:'computer'}],strategyEnabled:true,specialEnabled:true,bankEnabled:true,loanEnabled:true,marketEnabled:true,automaticLiquidation:true};
    assert.equal(createGame(seed,config).tiles.length,30);
    const report=runSimulation(seed,{config,maxActions:5000});
    assert.equal(report.finalState.status,'finished');
    assert.equal(report.rejections,0);
    assert.deepEqual(deserializeGame(serializeGame(report.finalState)).game,report.finalState);
  }
});
