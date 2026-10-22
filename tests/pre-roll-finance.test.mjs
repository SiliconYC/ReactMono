import test from 'node:test';
import assert from 'node:assert/strict';
import {createGame,applyAction} from '../.test-dist/core/game.js';
import {levelConfig} from '../.test-dist/core/level-data.js';
import {serializeGame,deserializeGame} from '../.test-dist/core/save.js';
test('掷骰前可以完成存取款、股票、抵押借还与出售，决策中仍禁止交易',()=>{
 let game=applyAction(createGame(2,{...levelConfig('lime-garden-30'),bankEnabled:true,loanEnabled:true,marketEnabled:true,stockAccount:'bank'}),{type:'start_game',actorId:'p1'}).state;
 game={...game,tiles:game.tiles.map(t=>[1,2].includes(t.id)?{...t,ownerId:'p1',level:1}:t)};
 const act=(type,extra={})=>{const r=applyAction(game,{type,actorId:'p1',...extra});assert.equal(r.ok,true,type+': '+r.reason);game=r.state;assert.equal(game.phase,'await_roll');};
 act('deposit_bank',{amount:200});act('withdraw_bank',{amount:50});
 act('buy_stock',{stockId:'SEA',quantity:1});act('sell_stock',{stockId:'SEA',quantity:1});
 act('mortgage_property',{tileId:1});act('borrow_loan',{amount:10});act('repay_loan',{amount:10});act('release_mortgage',{tileId:1});act('sell_property',{tileId:2});
 for(const phase of ['await_decision','await_shop'])for(const action of [{type:'deposit_bank',amount:1},{type:'borrow_loan',amount:1},{type:'buy_stock',stockId:'SEA',quantity:1},{type:'sell_property',tileId:1}])assert.equal(applyAction({...game,phase},{...action,actorId:'p1'}).ok,false);
 assert.equal(game.events.some(e=>e.type==='die_rolled'),false);
 assert.deepEqual(deserializeGame(serializeGame(game)).game,game);
});
