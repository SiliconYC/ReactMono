/** P3-16: independent engine acceptance; do NOT reuse the #42 runStyleBenchmark loop. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import {createGame,applyAction,DEFAULT_CONFIG,HARBOR_CONFIG,loanLimit} from '../dist/core/game.js';
import {chooseComputerAction} from '../dist/core/agent.js';
import {serializeGame,deserializeGame} from '../dist/core/save.js';

const NOW='2026-10-17T00:00:00.000Z';
const styles=['conservative','balanced','aggressive'];
const path='artifacts/issue45/p3-1000-raw.json';
const deterministicSave=state=>{
  const restored=deserializeGame(serializeGame(state,{now:NOW})).game;
  assert.deepEqual(restored,state,'asset/state must survive a full save round-trip');
};
function validateAssets(state,seed,step){
  assert.equal(state.bank?.lastInterestRound,state.round,'bank round mismatch seed='+seed);
  assert.equal(state.loan?.lastInterestRound,state.round,'loan round mismatch seed='+seed);
  assert.equal(state.market?.round,state.round,'market round mismatch seed='+seed);
  const ids=new Set(state.players.map(p=>p.id));
  for(const t of state.tiles){
    assert.ok(t.ownerId===null||ids.has(t.ownerId),'orphan property seed='+seed);
    assert.ok(!t.ownerId||!state.players.find(p=>p.id===t.ownerId)?.bankrupt,'bankrupt property owner seed='+seed);
  }
  for(const p of state.players){
    for(const n of [p.cash,p.bankBalance??0,p.loanBalance??0]){
      assert.ok(Number.isSafeInteger(n)&&n>=0,'negative/noninteger account seed='+seed+' step='+step);
    }
    if(p.bankrupt) {
      assert.equal(p.bankBalance??0,0,'bankrupt bank balance seed='+seed);
      assert.equal(p.loanBalance??0,0,'bankrupt debt seed='+seed);
      assert.equal(Object.values(p.holdings??{}).reduce((a,v)=>a+v.quantity,0),0,'bankrupt shares seed='+seed);
    }
    for(const lot of Object.values(p.holdings??{})){
      assert.ok(Number.isSafeInteger(lot.quantity)&&lot.quantity>0,'shares seed='+seed);
      assert.ok(Number.isSafeInteger(lot.costBasis)&&lot.costBasis>0,'cost basis seed='+seed);
    }
    if((p.loanBalance??0)>0)assert.ok(p.loanBalance<=loanLimit(state,p.id),'uncovered loan seed='+seed);
  }
}
test('P3 最终独立验收：1000 固定种子、2–4 人、双地图、三风格、资金与存档逐步校验',()=>{
  mkdirSync('artifacts/issue45',{recursive:true});
  const rows=[],summary={games:0,actions:0,rejections:0,detentions:0,bankruptcies:0,
    roundLimits:0,wins:0,totalRounds:0,totalTurns:0,byMap:{},byPlayers:{},byStyle:{}};
  const saveEvidence=()=>writeFileSync(path,JSON.stringify({suite:'P3-16',version:1,
    base:'dev post #44',summary,rows},null,2)+'\n');
  for(let i=0;i<1000;i++){
    const seed=450000+i*97;
    const base=i%2===0?DEFAULT_CONFIG:HARBOR_CONFIG;
    const count=2+(Math.floor(i/2)%3);
    const maxRounds=[12,24,36,60][Math.floor(i/6)%4];
    const initialCash=[450,800,1500,2500,3500][Math.floor(i/24)%5];
    const players=Array.from({length:count},(_,seat)=>({id:'p'+(seat+1),
      name:'电脑'+(seat+1),kind:'computer',computerStyle:styles[(seat+Math.floor(i/30))%3]}));
    const config={...base,players,maxRounds,initialCash,strategyEnabled:true,specialEnabled:true,
      bankEnabled:true,loanEnabled:true,marketEnabled:true,automaticLiquidation:true};
    const map=base.map?.id??'classic-24',trace=[];
    try{
      let state=createGame(seed,config);
      const started=applyAction(state,{type:'start_game',actorId:'p1'});
      assert.ok(started.ok,'start seed='+seed);
      state=started.state;
      deterministicSave(state);
      let actions=0,turns=0,detentions=0;
      const maxActions=maxRounds*count*30;
      while(state.status!=='finished'){
        assert.ok(actions<maxActions,'nontermination seed='+seed+' recent='+trace.slice(-8).join('|'));
        const actor=state.players[state.currentPlayerIndex];
        assert.equal(actor.kind,'computer');
        const choice=chooseComputerAction(state);
        assert.ok(choice,'dead phase seed='+seed+' phase='+state.phase);
        assert.equal(choice.actorId,actor.id);
        const previous=state;
        const result=applyAction(state,choice);
        assert.ok(result.ok,'illegal action seed='+seed+' action='+choice.type+
          ' reason='+(result.ok?'':result.reason));
        assert.equal(result.state.revision,previous.revision+1,'duplicate revision seed='+seed);
        assert.ok(result.state.events.length>previous.events.length,'missing events seed='+seed);
        state=result.state;actions++;
        if(choice.type==='roll'||choice.type==='skip_turn')turns++;
        if(choice.type==='skip_turn')detentions++;
        trace.push(actions+':'+actor.id+':'+choice.type+':'+state.phase);
        validateAssets(state,seed,actions);
        if(actions%45===0)deterministicSave(state);
      }
      deterministicSave(state);
      assert.equal(state.phase,'finished');
      assert.equal(state.events.filter(e=>e.type==='game_finished').length,1,'terminal event seed='+seed);
      assert.ok(turns<=maxRounds*count,'turn limit seed='+seed);
      const bankruptcies=state.players.filter(p=>p.bankrupt).length;
      const finish=state.events.findLast(e=>e.type==='game_finished');
      const reason=String(finish.details?.reason??'unknown');
      assert.ok(['round_limit','bankruptcy'].includes(reason),'reason seed='+seed);
      const record={seed,map,count,maxRounds,initialCash,styles:players.map(p=>p.computerStyle),
        actions,turns,detentions,rounds:state.round,reason,winnerId:state.winnerId,
        bankruptcies,balances:state.players.map(p=>({id:p.id,style:p.computerStyle,cash:p.cash,
          bankBalance:p.bankBalance??0,loanBalance:p.loanBalance??0,holdings:p.holdings??{},
          bankrupt:p.bankrupt})),trace};
      rows.push(record);summary.games++;summary.actions+=actions;summary.totalTurns+=turns;
      summary.totalRounds+=state.round;summary.detentions+=detentions;summary.bankruptcies+=bankruptcies;
      summary.roundLimits+=Number(reason==='round_limit');summary.wins+=Number(state.winnerId!==null);
      summary.byMap[map]=(summary.byMap[map]??0)+1;
      summary.byPlayers[count]=(summary.byPlayers[count]??0)+1;
      for(const p of state.players){
        const s=p.computerStyle;
        summary.byStyle[s]??={seats:0,wins:0,bankruptcies:0};
        summary.byStyle[s].seats++;
        summary.byStyle[s].wins+=Number(p.id===state.winnerId);
        summary.byStyle[s].bankruptcies+=Number(p.bankrupt);
      }
    }catch(error){
      rows.push({seed,map,count,maxRounds,initialCash,failed:String(error)});
      saveEvidence();
      throw new Error('P3-16 failed seed='+seed+': '+String(error),{cause:error});
    }
  }
  saveEvidence();
  assert.equal(summary.games,1000);
  assert.equal(summary.rejections,0);
  assert.ok(summary.detentions>0,'hospital/prison skips must be represented');
  assert.deepEqual(Object.keys(summary.byMap).sort(),['classic-24','harbor-20']);
  assert.deepEqual(Object.keys(summary.byPlayers).sort(),['2','3','4']);
  assert.deepEqual(Object.keys(summary.byStyle).sort(),[...styles].sort());
  console.log('P3-16 INDEPENDENT ACCEPTANCE '+JSON.stringify({
    ...summary,averageRounds:summary.totalRounds/summary.games,
    averageTurns:summary.totalTurns/summary.games,raw:path}));
});
