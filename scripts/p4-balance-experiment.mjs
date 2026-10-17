/** P4 #71: PRE-REGISTERED 1000-pair trial. Experimental configuration only. */
import {mkdirSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {runSimulation} from '../dist/core/simulator.js';
import {DEFAULT_CONFIG,HARBOR_CONFIG,netWorth} from '../dist/core/game.js';
import {cpuDelay} from '../dist/ui/computer-pace.js';
const TOTAL=1000,STYLES=['conservative','balanced','aggressive'];
const OUTPUT='artifacts/issue71/p4-balance-paired-1000x2.json';
const baseStats=()=>({games:0,roundLimit:0,bankruptcyFinish:0,totalRounds:0,totalTurns:0,actions:0,illegal:0,
  bankruptPlayers:0,firstBankruptcyEvents:[],assetTopShares:[],assetGaps:[],stocks:0,bank:0,loans:0,cards:0,facilities:0,
  modeledNormalWaitMs:0,modeledFastWaitMs:0,byMap:{},byCount:{},
  byStyle:Object.fromEntries(STYLES.map(s=>[s,{seats:0,wins:0,bankruptcies:0}])),actionCounts:{},eventCounts:{}});
const A=baseStats(),B=baseStats(),rows=[],failureSeeds=[];
const aggregate=(stats,sim,meta,side)=>{
 const end=sim.finalState,players=end.players,events=end.events;
 const wealth=players.map(p=>netWorth(end,p.id)).sort((x,y)=>y-x);
 const positives=wealth.map(x=>Math.max(0,x));
 const share=positives[0]/Math.max(1,positives.reduce((a,b)=>a+b,0));
 const gap=(wealth[0]??0)-(wealth[1]??0);
 const actions={};
 for(const trace of sim.trace){
  const type=trace.split(':')[2];actions[type]=(actions[type]??0)+1;
  stats.actionCounts[type]=(stats.actionCounts[type]??0)+1;
  stats.modeledNormalWaitMs+=cpuDelay('normal',{type,actorId:'p1'});
  stats.modeledFastWaitMs+=cpuDelay('fast',{type,actorId:'p1'});
 }
 const eventCounts={};
 for(const ev of events){eventCounts[ev.type]=(eventCounts[ev.type]??0)+1;
  stats.eventCounts[ev.type]=(stats.eventCounts[ev.type]??0)+1;}
 stats.games++;stats.totalRounds+=end.round;stats.totalTurns+=sim.playerTurns;
 stats.actions+=sim.actions;stats.illegal+=sim.rejections;
 stats.roundLimit+=Number(sim.finishReason==='round_limit');
 stats.bankruptcyFinish+=Number(sim.finishReason==='bankruptcy');
 stats.bankruptPlayers+=players.filter(p=>p.bankrupt).length;
 stats.firstBankruptcyEvents.push(events.findIndex(e=>e.type==='player_bankrupt'));
 stats.assetTopShares.push(share);stats.assetGaps.push(gap);
 for(const [key,prefixes] of Object.entries({stocks:['stock_bought','stock_sold','stock_liquidated'],
  bank:['bank_deposited','bank_withdrawn','bank_interest'],loans:['loan_borrowed','loan_repaid','loan_interest','loan_default'],
  cards:['card_used','card_received','shop_purchased'],facilities:['facility_entered','detention_skipped']})){
  stats[key]+=prefixes.reduce((n,x)=>n+(eventCounts[x]??0),0);
 }
 stats.byMap[meta.map]=(stats.byMap[meta.map]??0)+1;
 stats.byCount[meta.count]=(stats.byCount[meta.count]??0)+1;
 for(const p of players){const score=stats.byStyle[p.computerStyle];score.seats++;
  score.wins+=Number(end.winnerId===p.id);score.bankruptcies+=Number(p.bankrupt);}
 return {side,seed:meta.seed,map:meta.map,count:meta.count,roundCap:meta.maxRounds,
  cash:meta.initialCash,styles:meta.players.map(p=>p.computerStyle),
  rounds:end.round,playerTurns:sim.playerTurns,actions:sim.actions,reason:sim.finishReason,winnerId:end.winnerId,
  bankruptcies:players.filter(p=>p.bankrupt).length,assetTopShare:share,assetGap:gap,
  firstBankruptcyEvent:events.findIndex(e=>e.type==='player_bankrupt'),
  finalAssets:players.map(p=>({id:p.id,style:p.computerStyle,netWorth:netWorth(end,p.id),
    cash:p.cash,deposit:p.bankBalance??0,debt:p.loanBalance??0,shares:p.holdings??{},cards:p.cards??{},
    detention:p.detention??null,bankrupt:p.bankrupt})),
  actionCounts:actions,eventCounts,trace:sim.trace};
};
const mean=arr=>arr.length?arr.reduce((a,b)=>a+b,0)/arr.length:0;
const summarize=s=>({
 games:s.games,roundLimitShare:s.roundLimit/s.games,bankruptcyFinish:s.bankruptcyFinish,
 averageRounds:s.totalRounds/s.games,averageTurns:s.totalTurns/s.games,averageActions:s.actions/s.games,
 illegalActions:s.illegal,bankruptPlayers:s.bankruptPlayers,averageAssetTopShare:mean(s.assetTopShares),
 averageAssetGap:mean(s.assetGaps),
 firstBankruptcyEventMean:mean(s.firstBankruptcyEvents.filter(x=>x>=0)),
 meanModeledNormalWaitMs:s.modeledNormalWaitMs/s.games,
 meanModeledFastWaitMs:s.modeledFastWaitMs/s.games,
 stocks:s.stocks,bank:s.bank,loans:s.loans,cards:s.cards,facilities:s.facilities,
 byMap:s.byMap,byCount:s.byCount,byStyle:s.byStyle,actionCounts:s.actionCounts,eventCounts:s.eventCounts
});
let changedWinners=0,failedPrefix=0;
const started=performance.now();
try{
 for(let i=0;i<TOTAL;i++){
  const seed=450000+i*97,base=i%2===0?DEFAULT_CONFIG:HARBOR_CONFIG;
  const count=2+(Math.floor(i/2)%3),maxRounds=[12,24,36,60][Math.floor(i/6)%4];
  const initialCash=[450,800,1500,2500,3500][Math.floor(i/24)%5];
  const players=Array.from({length:count},(_,seat)=>({id:'p'+(seat+1),name:'电脑'+(seat+1),
   kind:'computer',computerStyle:STYLES[(seat+Math.floor(i/30))%3]}));
  const meta={seed,map:base.map?.id??'classic-24',count,maxRounds,initialCash,players};
  const config={...base,players,maxRounds,initialCash,strategyEnabled:true,specialEnabled:true,
   bankEnabled:true,loanEnabled:true,marketEnabled:true,automaticLiquidation:true};
  // Only independent parameter is the shorter user-selectable horizon.
  const reducedRounds=Math.max(1,Math.floor(maxRounds*.75));
  const a=runSimulation(seed,{config,maxActions:maxRounds*count*30});
  const b=runSimulation(seed,{config:{...config,maxRounds:reducedRounds},
    maxActions:reducedRounds*count*30});
  assert.equal(a.rejections,0);assert.equal(b.rejections,0);
  assert.equal(a.finalState.status,'finished');assert.equal(b.finalState.status,'finished');
  const aSeq=a.trace.map(x=>x.split(':').slice(1,3).join(':'));
  const bSeq=b.trace.map(x=>x.split(':').slice(1,3).join(':'));
  if(!bSeq.every((x,n)=>aSeq[n]===x))failedPrefix++;
  changedWinners+=Number(a.finalState.winnerId!==b.finalState.winnerId);
  rows.push({seed,base:aggregate(A,a,meta,'A'),candidate:aggregate(B,b,{...meta,maxRounds:reducedRounds},'B')});
  if((i+1)%250===0)console.log('P4-71 completed paired games',i+1);
 }
}catch(e){failureSeeds.push(String(e));}
const baseline=summarize(A),candidate=summarize(B);
const paired={games:rows.length,changedWinners,changedWinnerShare:changedWinners/Math.max(1,rows.length),
  failedPrefix,meanActionReduction:(baseline.averageActions-candidate.averageActions)/Math.max(1,baseline.averageActions),
  bankruptcySignalReduction:(baseline.bankruptPlayers-candidate.bankruptPlayers)/Math.max(1,baseline.bankruptPlayers),
  nominalWaitReduction:(baseline.meanModeledNormalWaitMs-candidate.meanModeledNormalWaitMs)/Math.max(1,baseline.meanModeledNormalWaitMs)};
const thresholds={minActionReduction:.20,maxChangedWinners:.10,maxBankruptcySignalReduction:.20};
const violated=[
 ...(paired.failedPrefix?['pre-terminal action-sequence divergence']:[]),
 ...(paired.meanActionReduction<thresholds.minActionReduction?['less than 20% action savings']:[]),
 ...(paired.changedWinnerShare>thresholds.maxChangedWinners?['over 10% winner changes']:[]),
 ...(paired.bankruptcySignalReduction>thresholds.maxBankruptcySignalReduction?['over 20% lost bankruptcy signal']:[])
];
const decision={defaultChange:'REJECT',machineGate:violated.length?'REJECT':'PASS_PENDING_HUMAN_TRIAL',
  reasons:violated.length?violated:['No human experience feedback: do not change a default on simulator metrics alone'],
  realPlayerParticipants:0,rulesOrAgentCodeModified:false};
mkdirSync('artifacts/issue71',{recursive:true});
writeFileSync(OUTPUT,JSON.stringify({version:1,design:'pre-registered A/B maxRounds 100% vs floor(75%)',
  seedFormula:'450000+97*i',source:'same game engine and three original strategies',
  clock:'modeled #70 UI timer budget only, NOT measured browser wait',
  thresholds,baseline,candidate,paired,decision,rows,failureSeeds,
  metadata:{totalWallMs:Math.round(performance.now()-started),humanFeedback:false}},null,2)+'\n');
assert.equal(failureSeeds.length,0,JSON.stringify(failureSeeds));
assert.equal(rows.length,TOTAL);assert.equal(paired.failedPrefix,0);
assert.equal(A.illegal+B.illegal,0);
assert.deepEqual(A.byMap,{'classic-24':500,'harbor-20':500});
assert.deepEqual(B.byMap,{'classic-24':500,'harbor-20':500});
assert.deepEqual(Object.keys(A.byCount).sort(),['2','3','4']);
assert.ok(A.cards>0&&A.facilities>0&&A.stocks>0&&A.bank>0&&A.loans>0);
console.log('P4-71 SUMMARY '+JSON.stringify({baseline,candidate,paired,decision,artifact:OUTPUT}));
