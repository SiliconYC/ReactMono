import test from 'node:test';
import assert from 'node:assert/strict';
import {runSimulation} from '../dist/core/simulator.js';
import {netWorth} from '../dist/core/game.js';
import {serializeGame,deserializeGame} from '../dist/core/save.js';

test('P2 独立验收：100 固定种子经济、产权、卡牌与事件重放不变量',()=>{
  let cards=0,randomEvents=0,upgrades=0,rents=0;
  for(let seed=0;seed<100;seed++){
    const a=runSimulation(seed),b=runSimulation(seed);
    assert.deepEqual(a,b,'重复种子不一致 seed='+seed);
    const s=a.finalState;
    assert.equal(s.status,'finished');
    assert.ok(a.actions<=720,'动作上限 seed='+seed);
    for(const p of s.players){
      assert.ok(Number.isSafeInteger(p.cash)&&p.cash>=0,'现金非法 seed='+seed);
      assert.ok((p.cards?.reward??0)>=0&&(p.cards?.stride??0)>=0,'库存非法 seed='+seed);
      const worth=p.cash+s.tiles.reduce((sum,t)=>t.kind==='property'&&t.ownerId===p.id?
        sum+(t.price??0)+(t.upgradeCosts??[]).slice(0,t.level??0).reduce((v,c)=>v+c,0):sum,0);
      assert.equal(netWorth(s,p.id),worth);
    }
    for(const t of s.tiles){
      if(t.kind==='property'){
        assert.ok(Number.isInteger(t.level)&&t.level>=0&&t.level<=2);
        assert.ok(t.ownerId===null||s.players.some(p=>p.id===t.ownerId));
        if(t.ownerId===null)assert.equal(t.level,0,'无主地产不可保有升级');
      }
    }
    const hand=new Map(s.players.map(p=>[p.id,{reward:0,stride:0}]));
    let lastRoll=null;
    for(const e of s.events){
      if(e.type==='die_rolled')lastRoll=e;
      if(e.type==='card_received'){
        const inv=hand.get(e.actorId);
        assert.ok(inv);
        inv[e.details.cardType]++;cards++;
      }
      if(e.type==='card_used'){
        const inv=hand.get(e.actorId);
        assert.ok(inv);
        inv[e.details.cardType]--;
        assert.ok(inv[e.details.cardType]>=0,'无库存用卡 seed='+seed);
      }
      if(e.type==='event_fee'||e.type==='event_bonus'){
        assert.ok(Number.isSafeInteger(e.details.amount)&&e.details.amount>=0);randomEvents++;
      }
      if(e.type==='rent_paid'){
        assert.ok(lastRoll,'未掷骰就收租');
        assert.ok(e.details.amount>=0&&e.details.amount<=e.details.due);rents++;
      }
      if(e.type==='property_upgraded'){assert.ok(e.details.level>=1&&e.details.level<=2);upgrades++;}
    }
    for(const p of s.players){assert.deepEqual(p.cards??{reward:0,stride:0},hand.get(p.id),'最终库存与事件流水不符 seed='+seed);}
    assert.deepEqual(deserializeGame(serializeGame(s)).game,s,'终局保存恢复不一致 seed='+seed);
  }
  assert.ok(cards>0&&randomEvents>0&&upgrades>0&&rents>0,{cards,randomEvents,upgrades,rents});
});
