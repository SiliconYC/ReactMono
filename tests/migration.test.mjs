import test from 'node:test';import assert from 'node:assert/strict';
import {createGame,applyAction,netWorth} from '../dist/core/game.js';
import {deserializeGame,serializeGame} from '../dist/core/save.js';
function checksum(data){let h=0x811c9dc5;for(let i=0;i<data.length;i++){h^=data.charCodeAt(i);h=Math.imul(h,0x01000193)}return(h>>>0).toString(16).padStart(8,'0')}
test('真实旧 v1 字段结构无损升级到 v2，净资产不变且导出后仍可再次读取',()=>{
  let state=applyAction(createGame(41),{type:'start_game',actorId:'p1'}).state;
  state=applyAction(state,{type:'roll',actorId:'p1'}).state;
  const old={...state,schemaVersion:1};delete old.upgradeRulesVersion;
  delete old.cardRules;delete old.pendingMoveBonus;
  old.players=state.players.map(p=>{const v={...p};delete v.cards;return v});
  old.tiles=state.tiles.map(t=>{const v={...t};delete v.level;delete v.upgradeCosts;delete v.levelRents;delete v.cardStation;delete v.eventBonus;delete v.eventFee;return v});
  const payload={format:'reactmono-save',formatVersion:1,rulesVersion:1,createdAt:'2026-10-15T00:00:00.000Z',updatedAt:'2026-10-15T00:00:00.000Z',game:old};
  const imported=deserializeGame(JSON.stringify({...payload,checksum:checksum(JSON.stringify(payload))}));
  assert.equal(imported.rulesVersion,2);assert.equal(imported.game.tiles[1].level,0);
  assert.equal(netWorth(imported.game,'p1'),netWorth(state,'p1'));
  assert.deepEqual(deserializeGame(JSON.stringify(imported)),imported);
  assert.deepEqual(deserializeGame(serializeGame(imported.game)).game,imported.game);
});
