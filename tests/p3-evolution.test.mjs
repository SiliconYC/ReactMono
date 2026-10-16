import test from 'node:test';
import assert from 'node:assert/strict';
import {DEFAULT_CONFIG,HARBOR_CONFIG} from '../dist/core/game.js';
import {runSimulation} from '../dist/core/simulator.js';

// #44: independent, reproducible evidence. The P3 evaluator previously counted
// only dice rolls, omitting turns spent detained in hospital/prison.
test('P3 自主改进：被拘留跳过的回合也计入真实回合数', () => {
  let skipped = 0;
  for (let seed = 1; seed <= 60; seed++) {
    const base = seed % 2 ? DEFAULT_CONFIG : HARBOR_CONFIG;
    const config = {...base, maxRounds: 12, strategyEnabled: true, specialEnabled: true,
      players: [
        {id:'p1',name:'保守',kind:'computer',computerStyle:'conservative'},
        {id:'p2',name:'平衡',kind:'computer',computerStyle:'balanced'},
        {id:'p3',name:'进取',kind:'computer',computerStyle:'aggressive'}
      ]};
    const report = runSimulation(seed, {config, maxActions: 900});
    const types = report.trace.map(line => line.split(':')[2]);
    const rolled = types.filter(type => type === 'roll').length;
    const skippedHere = types.filter(type => type === 'skip_turn').length;
    skipped += skippedHere;
    assert.equal(report.playerTurns, rolled + skippedHere,
      'seed=' + seed + ' should count each detained turn, not just rolled dice');
    assert.equal(report.finalState.status, 'finished');
    assert.equal(report.rejections, 0);
  }
  assert.ok(skipped > 0, 'fixtures must cover actual hospital/prison detention');
});
