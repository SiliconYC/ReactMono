import test from 'node:test';
import assert from 'node:assert/strict';
import {createGame,applyAction,DEFAULT_CONFIG,HARBOR_CONFIG} from '../dist/core/game.js';
import {chooseComputerAction} from '../dist/core/agent.js';
import {COMPUTER_STYLES} from '../dist/core/strategic-agent.js';
import {runStyleBenchmark} from '../dist/core/benchmark.js';
import {runSimulation} from '../dist/core/simulator.js';
import {deserializeGame,serializeGame} from '../dist/core/save.js';

const config=(style)=>({...DEFAULT_CONFIG,strategyEnabled:true,specialEnabled:true,bankEnabled:true,
  marketEnabled:true,loanEnabled:true,automaticLiquidation:true,maxRounds:20,
  players:[{id:'p1',name:'甲',kind:'computer',computerStyle:style},
           {id:'p2',name:'乙',kind:'computer',computerStyle:'balanced'}]});
test('风格字段严格校验；旧电脑存档不受影响',()=>{
  for(const style of COMPUTER_STYLES){
    const s=createGame(123,config(style));
    assert.equal(s.players[0].computerStyle,style);
    assert.deepEqual(deserializeGame(serializeGame(s)).game,s);
    const started=applyAction(s,{type:'start_game',actorId:'p1'}).state;
    const before=JSON.stringify(started);
    const choice=chooseComputerAction(started);
    assert.equal(choice.actorId,'p1');
    assert.equal(JSON.stringify(started),before);
  }
  assert.throws(()=>createGame(1,config('hacked')),/玩家配置/);
  const wrong=config('balanced');
  assert.throws(()=>createGame(1,{...wrong,players:[{...wrong.players[0],kind:'human'},wrong.players[1]]}),/玩家配置/);
  const legacy=createGame(123);
  assert.equal(legacy.players[1].computerStyle,undefined);
  assert.deepEqual(deserializeGame(serializeGame(legacy)).game,legacy);
});
test('不同策略在相同棋盘产生不同买地产决策',()=>{
  const examples=COMPUTER_STYLES.map(style=>{
    const initial=createGame(35,config(style));
    const state=applyAction(initial,{type:'start_game',actorId:'p1'}).state;
    const candidate={...state,phase:'await_decision',
      players:state.players.map((p,i)=>i===0?{...p,cash:450,position:1}:p)};
    return chooseComputerAction(candidate).type;
  });
  assert.equal(examples[0],'decline_property');
  assert.equal(examples[2],'buy_property');
});
test('相同输入、相同种子跨地图可以复现，且始终经引擎合法命令',()=>{
  for(const base of [DEFAULT_CONFIG,HARBOR_CONFIG])for(const style of COMPUTER_STYLES){
    const options={config:{...config(style),map:base.map,tiles:base.tiles,maxRounds:8},maxActions:500};
    const first=runSimulation(20261016,options),second=runSimulation(20261016,options);
    assert.equal(first.rejections,0);
    assert.deepEqual(first.trace,second.trace);
    assert.equal(first.finalState.status,'finished');
  }
});
test('1000 局真实无界面对战：多人数、多地图、多风格、零拒绝、决策分布可追溯',()=>{
  const result=runStyleBenchmark(1000);
  console.log('P3-13 TOURNAMENT RESULTS '+JSON.stringify(result));
  assert.equal(result.games,1000);
  assert.equal(result.illegalActions,0);
  assert.ok(result.totalActions>1000);
  assert.deepEqual(Object.keys(result.byPlayerCount).sort(),['2','3','4']);
  assert.equal(Object.keys(result.byMap).length,2);
  for(const style of COMPUTER_STYLES){
    const score=result.byStyle[style];
    assert.ok(score.games>500);
    assert.ok(score.winRate>=0&&score.winRate<=1);
    assert.ok(score.bankruptcyRate>=0&&score.bankruptcyRate<=1);
    assert.ok(score.actionSelection.end_turn>0);
  }
  assert.notDeepEqual(result.byStyle.conservative.actionSelection,result.byStyle.aggressive.actionSelection);
});
