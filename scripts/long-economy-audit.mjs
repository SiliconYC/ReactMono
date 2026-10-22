import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {existsSync,mkdirSync,writeFileSync} from 'node:fs';
import {createGame,applyAction,netWorth} from '../.test-dist/core/game.js';
import {levelConfig} from '../.test-dist/core/level-data.js';
import {chooseDebugSimulationAction} from '../.test-dist/core/debug-tools.js';
import {serializeGame,deserializeGame} from '../.test-dist/core/save.js';

const label=process.argv[2]??'current';
assert.match(label,/^[a-z0-9-]+$/);
const path=`artifacts/long-economy/${label}.json`;
assert.equal(existsSync(path),false,'证据文件已存在，请使用新标签');
const seeds=[20261015,...Array.from({length:32},(_,i)=>createHash('sha256').update(`ReactMono-long-economy-v1:${i}`).digest().readUInt32LE(0)||1)];
const liquid=state=>state.players.reduce((sum,p)=>sum+p.cash+(p.bankBalance??0),0);

function eventCashFlow(before,events) {
  let flow=0;
  for(const event of events){
    const d=event.details??{};
    if(['bank_interest','event_bonus','card_used','property_sold','property_liquidated','stock_sold','stock_liquidated','loan_borrowed'].includes(event.type))flow+=d.amount??0;
    if(['property_bought','property_upgraded','shop_purchased','facility_entered','event_fee','stock_bought','loan_repaid'].includes(event.type))flow-=d.amount??0;
    if(event.type==='loan_interest')flow-=d.paid;
    if(event.type==='loan_default'){
      const rules=before.resaleRules??{landPercent:0.75,upgradePercent:0.5};
      const collateral=before.tiles.filter(t=>t.ownerId===event.actorId&&t.mortgaged).reduce((sum,t)=>{
        const construction=(t.upgradeCosts??[]).slice(0,t.level??0).reduce((a,b)=>a+b,0);
        return sum+Math.floor(t.price*rules.landPercent)+Math.floor(construction*rules.upgradePercent);
      },0);
      flow+=Math.max(0,collateral-d.debt);
    }
    if(event.type==='rent_paid'){
      assert.ok(Number.isSafeInteger(d.amount)&&d.amount>=0&&d.amount<=d.due);
      assert.equal(d.fromId,event.actorId);
      assert.notEqual(d.toId,d.fromId);
    }
  }
  return flow;
}

const rows=[];
let auditedActions=0;
for(const map of ['classic-24','lime-garden-30'])for(const cash of [levelConfig(map).initialCash,1_000_000])for(const seats of [2,4])for(const seed of seeds){
  const config={...levelConfig(map),initialCash:cash,endCondition:'bankruptcy',
    players:Array.from({length:seats},(_,i)=>({id:`p${i+1}`,name:`玩家${i+1}`,kind:i===0?'human':'computer',...(i===0?{}:{computerStyle:'balanced'})})),
    propertyVisitOnly:true,automaticLiquidation:true,bankEnabled:true,loanEnabled:true,marketEnabled:true,stockAccount:'bank',strategyEnabled:true,specialEnabled:false};
  let state=applyAction(createGame(seed,config),{type:'start_game',actorId:'p1'}).state;
  const initialLiquid=liquid(state),trace=createHash('sha256');
  let actions=0,flow=0;
  while(state.status==='playing'&&state.round<201){
    assert.ok(actions<100_000);
    const action=chooseDebugSimulationAction(state);
    assert.ok(action);
    const result=applyAction(state,action);
    assert.equal(result.ok,true,JSON.stringify({map,cash,seats,seed,action}));
    const change=eventCashFlow(state,result.events);
    assert.equal(liquid(result.state)-liquid(state),change,JSON.stringify({map,cash,seats,seed,action,events:result.events}));
    flow+=change;
    trace.update(JSON.stringify(action)+'\n');
    state=result.state;
    actions++;
  }
  assert.equal(liquid(state),initialLiquid+flow);
  assert.deepEqual(deserializeGame(serializeGame(state)).game,state);
  if(state.status==='finished')assert.equal(state.events.at(-1).details.reason,'bankruptcy');
  if(cash===1_000_000){assert.equal(state.round,201);assert.equal(state.status,'playing');}
  const reason=state.status==='finished'?'bankruptcy':'requested_rounds';
  rows.push({map,cash,seats,seed,round:state.round,status:state.status,reason,winnerId:state.winnerId,actions,
    traceSha256:trace.digest('hex'),initialLiquid,finalLiquid:liquid(state),externalCashFlow:flow,
    properties:state.tiles.filter(t=>t.ownerId).length,levels:[0,1,2].map(level=>state.tiles.filter(t=>t.ownerId&&t.level===level).length),
    purchases:state.events.filter(e=>e.type==='property_bought').length,upgrades:state.events.filter(e=>e.type==='property_upgraded').length,
    rentPayments:state.events.filter(e=>e.type==='rent_paid').length,bankruptcies:state.players.filter(p=>p.bankrupt).length,
    players:state.players.map(p=>({id:p.id,cash:p.cash,bankBalance:p.bankBalance,loanBalance:p.loanBalance,netWorth:netWorth(state,p.id),bankrupt:p.bankrupt}))});
  auditedActions+=actions;
}
mkdirSync('artifacts/long-economy',{recursive:true});
const summary={label,requestedRounds:200,seeds,games:rows.length,auditedActions,allCashFlowsExact:true,
  finished:rows.filter(r=>r.status==='finished').length,stillPlaying:rows.filter(r=>r.status==='playing').length,
  limitations:['固定种子且所有代玩采用平衡风格；不等于真人选择或所有经济参数平衡。','达到指定轮数仍存活时保留进行中状态，不伪造胜者。']};
writeFileSync(path,JSON.stringify({...summary,rows},null,2)+'\n');
console.log(JSON.stringify(summary));
