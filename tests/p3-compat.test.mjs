import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import ts from 'typescript';
import { createGame, applyAction, DEFAULT_CONFIG } from '../dist/core/game.js';
import { choosePhaseAction } from '../dist/core/agent.js';

// Immutable pre-P3 engine: compare actual events, PRNG consumption, funds and state
// at EVERY accepted action. Do not update the reference to make a failing test pass.
const source = readFileSync(new URL('./fixtures/p2-engine-reference.ts', import.meta.url), 'utf8');
const code = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 }
}).outputText;
const p2 = await import('data:text/javascript;base64,' + Buffer.from(code).toString('base64'));
const normalize = value => JSON.parse(JSON.stringify(value));

test('P3-01: P2 compatibility reference: 100 seeds, all intermediate states and events', () => {
  for (let seed=0; seed<100; seed++) {
    const config = { ...DEFAULT_CONFIG, maxRounds: 20 + seed % 7 };
    let now=createGame(seed,config), before=p2.createGame(seed,config);
    assert.deepEqual(normalize(now),normalize(before),'seed='+seed+' initial');
    let complete=false;
    for (let index=0; index<2000; index++) {
      if (now.status==='finished') { complete=true; break; }
      const action=choosePhaseAction(now, seed % 2 ? 200 : 50);
      assert.ok(action,'seed='+seed+' step='+index);
      const current=applyAction(now,action);
      const previous=p2.applyAction(before,action);
      assert.deepEqual(normalize(current),normalize(previous),
        'seed='+seed+' step='+index+' action='+action.type);
      assert.equal(current.ok,true);
      now=current.state;before=previous.state;
    }
    assert.ok(complete,'seed='+seed+' did not finish');
  }
});

test('P3-01: reject semantics and random generator remain identical', () => {
  for (const seed of [0,1,7,42,0xffffffff]) {
    let current=createGame(seed), reference=p2.createGame(seed);
    for (const action of [
      { type:'roll',actorId:'p1' },
      { type:'start_game',actorId:'p2' },
      { type:'start_game',actorId:'p1' },
      { type:'start_game',actorId:'p1' },
      { type:'use_card',actorId:'p1',cardType:'reward' },
      { type:'upgrade_property',actorId:'p1',tileId:0 }
    ]) {
      const a=applyAction(current,action), b=p2.applyAction(reference,action);
      assert.deepEqual(normalize(a),normalize(b),'seed='+seed+' action='+action.type);
      current=a.state;reference=b.state;
    }
  }
});
