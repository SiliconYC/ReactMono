import assert from 'node:assert/strict';
import { mkdirSync,writeFileSync,readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createGame,applyAction,netWorth } from '../.test-dist/core/game.js';
import { levelConfig } from '../.test-dist/core/level-data.js';
import { chooseDebugSimulationAction } from '../.test-dist/core/debug-tools.js';
import { serializeGame,deserializeGame } from '../.test-dist/core/save.js';
import { propertyRent,propertyRun } from '../.test-dist/core/property-groups.js';

const output='artifacts/lime-terraces';mkdirSync(output,{recursive:true});
const liquid=state=>state.players.reduce((sum,p)=>sum+p.cash+(p.bankBalance??0),0);
const rows=[];
let actions=0,groupBuilds=0,groupRents=0;
for(const seats of [2,4])for(const seed of Array.from({length:50},(_,i)=>20261022+i))for(const legacy of [false,true]){
  const config={...levelConfig('lime-garden-30'),endCondition:'bankruptcy',initialCash:2200,
    players:Array.from({length:seats},(_,i)=>({id:`p${i+1}`,name:`玩家${i+1}`,kind:'computer',computerStyle:['balanced','aggressive','conservative','balanced'][i]})),
    propertyVisitOnly:true,bankEnabled:true,loanEnabled:true,automaticLiquidation:true,strategyEnabled:true};
  if(legacy)delete config.terraceRulesVersion;
  let state=applyAction(createGame(seed,config),{type:'start_game',actorId:'p1'}).state,steps=0,builds=0,rents=0;
  while(state.status==='playing'&&state.round<151){
    const action=chooseDebugSimulationAction(state),before=state;
    assert.ok(action);
    const result=applyAction(state,action);
    assert.equal(result.ok,true,JSON.stringify({seats,seed,legacy,action}));
    let external=0;
    for(const e of result.events){
      const d=e.details??{};
      if(['bank_interest','event_bonus','card_used','property_sold','property_liquidated','loan_borrowed'].includes(e.type))external+=d.amount??0;
      if(['property_bought','property_upgraded','event_fee','facility_entered','shop_purchased','loan_repaid'].includes(e.type))external-=d.amount??0;
      if(e.type==='loan_interest')external-=d.paid;
      if(e.type==='loan_default'){
        const collateral=before.tiles.filter(t=>t.ownerId===e.actorId&&t.mortgaged).reduce((sum,t)=>sum+Math.floor(t.price*.75)+Math.floor((t.upgradeCosts??[]).slice(0,t.level??0).reduce((a,b)=>a+b,0)*.5),0);
        external+=Math.max(0,collateral-d.debt);
      }
      if(e.type==='rent_paid'){
        assert.equal(d.due,before.pendingRentWaiver?0:propertyRent(before,d.tileId));
        assert.ok(d.amount>=0&&d.amount<=d.due);
        if(propertyRun(before,d.tileId).length>1)rents++;
      }
    }
    assert.equal(liquid(result.state)-liquid(before),external,JSON.stringify({seats,seed,legacy,action,events:result.events}));
    const upgraded=result.events.filter(e=>e.type==='property_upgraded');
    if(upgraded.length>1)builds++;
    state=result.state;steps++;assert.ok(steps<20000);
  }
  assert.deepEqual(deserializeGame(serializeGame(state)).game,state);
  actions+=steps;groupBuilds+=builds;groupRents+=rents;
  rows.push({seats,seed,legacy,actions:steps,round:state.round,status:state.status,winnerId:state.winnerId,groupBuilds:builds,groupRents:rents,
    cash:state.players.map(p=>p.cash),netWorth:state.players.map(p=>netWorth(state,p.id))});
}
const current=JSON.parse(readFileSync('src/data/levels.json','utf8'));
const baseline=JSON.parse(execFileSync('git',['show','d38f371:src/data/levels.json'],{encoding:'utf8'}));
const unchanged=[];
for(const level of baseline.levels)if(level.map.id!=='lime-garden-30'){
  assert.deepEqual(current.levels.find(l=>l.map.id===level.map.id),level);unchanged.push(level.map.id);
}
const summary={games:rows.length,actions,groupBuilds,groupRents,finished:rows.filter(r=>r.status==='finished').length,
  capped:rows.filter(r=>r.status==='playing').length,allActionsLegal:true,allCashFlowsExact:true,saveRoundTrips:true,
  unchangedMaps:unchanged,limits:'固定50种子、2/4人、新旧规则各一组，150轮观察上限；不作为成熟经济平衡或真人趣味性结论。'};
writeFileSync(output+'/audit.json',JSON.stringify({summary,rows},null,2)+'\n');
console.log(JSON.stringify(summary));
