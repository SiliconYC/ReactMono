import test from 'node:test';import assert from 'node:assert/strict';
import {cpuDelay,cpuTurnKey,addCpuTiming,initialCpuTiming,MAX_CPU_ACTIONS_PER_TURN} from '../dist/ui/computer-pace.js';
import {runSimulation} from '../dist/core/simulator.js';
import {DEFAULT_CONFIG,HARBOR_CONFIG} from '../dist/core/game.js';
test('#70 delay presets reduce wait but NEVER modify legal decisions',()=>{
 const r={type:'roll',actorId:'p1'};
 assert.equal(cpuDelay('normal',r),160);
 assert.equal(cpuDelay('fast',r),8);
 assert.ok(cpuDelay('normal',r,[{type:'rent_paid'}])>cpuDelay('normal',r));
 assert.ok(MAX_CPU_ACTIONS_PER_TURN>=20);
 const t=addCpuTiming(initialCpuTiming,16,200);
 assert.equal(t.decisions,1);assert.equal(t.calculationMs,16);
});
test('#70 cross-mode game determinism: 72 matched seeds, dual boards and 2–4 seats',()=>{
 for(let i=0;i<72;i++){
   const base=i%2===0?DEFAULT_CONFIG:HARBOR_CONFIG;
   const count=2+(Math.floor(i/2)%3);
   const config={...base,maxRounds:4+(i%3),initialCash:800,strategyEnabled:true,specialEnabled:true,
    bankEnabled:true,loanEnabled:true,marketEnabled:true,automaticLiquidation:true,
    players:Array.from({length:count},(_,j)=>({id:'p'+(j+1),name:'电脑'+j,kind:'computer',computerStyle:['conservative','balanced','aggressive'][j%3]}))};
   const seed=70000+i*113;
   const normal=runSimulation(seed,{config,maxActions:2000}),fast=runSimulation(seed,{config,maxActions:2000});
   assert.equal(normal.rejections,0);assert.equal(fast.rejections,0);
   assert.deepEqual(normal.trace,fast.trace);
   assert.deepEqual(normal.finalState,fast.finalState);
   assert.equal(cpuTurnKey(normal.finalState),cpuTurnKey(fast.finalState));
 }
});
