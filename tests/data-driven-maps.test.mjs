import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { createGame, applyAction } from '../.test-dist/core/game.js';
import { advancePosition, validateMap } from '../.test-dist/core/maps.js';
import { serializeGame, deserializeGame } from '../.test-dist/core/save.js';
import { runSimulation } from '../.test-dist/core/simulator.js';

const sizes=[['bend-60',60],['bays-120',120],['ridges-360',360]];
async function data(){
  assert.ok(existsSync('src/data/levels.json'),'缺少可交换 JSON 关卡目录');
  return import('../.test-dist/core/level-data.js');
}
test('JSON 压力地图精确格数、凹形无重叠闭环，任意起格跨圈不截断',async()=>{
  const {LEVELS}=await data();
  for(const [id,count] of sizes){
    const level=LEVELS.find(l=>l.map.id===id);
    assert.ok(level,id);
    const {map,tiles}=level;
    assert.equal(tiles.length,count);
    assert.equal(map.cells.length,count);
    assert.equal(new Set(map.cells.map(c=>`${c.column},${c.row}`)).size,count);
    assert.ok(map.cells.some(c=>c.column>1&&c.column<map.columns&&c.row>1&&c.row<map.rows),'必须离开矩形边界');
    for(let i=0;i<count;i++){
      const a=map.cells[map.route[i]],b=map.cells[map.route[(i+1)%count]];
      assert.equal(Math.abs(a.column-b.column)+Math.abs(a.row-b.row),1,`${id} edge ${i}`);
      assert.equal(advancePosition(map,map.route[i],count*3+7),map.route[(i+7)%count]);
    }
  }
});
test('通用 JSON 加载接受额外关卡，无需修改 TS 注册名单；内置数据冻结',async()=>{
  const {loadLevelCatalog,LEVELS}=await data();
  const catalog=JSON.parse(readFileSync('src/data/levels.json','utf8'));
  const added=structuredClone(catalog.levels[0]);
  added.map.id='new-data-only-map';added.name='新关卡';
  catalog.levels.push(added);
  const loaded=loadLevelCatalog(catalog);
  assert.equal(loaded.at(-1).map.id,'new-data-only-map');
  assert.ok(Object.isFrozen(LEVELS[0].map.cells[0]));
  assert.throws(()=>{LEVELS[0].map.route[0]=7},TypeError);
});
test('目录拒绝重复标识、断路、重复格、越界、非有限值、错误站点及未知字段',async()=>{
  const {loadLevelCatalog}=await data();
  const source=JSON.parse(readFileSync('src/data/levels.json','utf8'));
  const mutations=[
    c=>c.levels.push(structuredClone(c.levels[0])),
    c=>c.levels[0].map.cells[1]={...c.levels[0].map.cells[0]},
    c=>c.levels[0].map.cells[1].column=999,
    c=>c.levels[0].map.route.splice(1,2,2,1),
    c=>c.levels[0].map.columns=Infinity,
    c=>c.levels[0].map.version=0,
    c=>c.levels[0].tiles[1].price=-1,
    c=>c.levels[0].tiles[1].kind='unknown',
    c=>c.levels[0].eventRules.tileIds=[1],
    c=>c.levels[0].cardRules.tileIds=[900],
    c=>c.levels[0].map.script='anything',
    c=>c.levels[0].hiddenCode='anything',
    c=>c.schemaVersion=99,
    c=>c.levels[0].tiles[1].title='甲'.repeat(101),
    c=>c.levels[0].cardRules.rewardCash=100001,
    c=>c.levels[0].cardRules.maxHand=1001,
  ];
  for(const mutate of mutations){const c=structuredClone(source);mutate(c);assert.throws(()=>loadLevelCatalog(c),/关卡|地图/);}
});
test('三张大图真实规则开局、完整圈移动、存读档隔离与篡改拒绝',async()=>{
  const {levelConfig}=await data();
  for(const [id,count] of sizes){
    const config=levelConfig(id);
    let state=createGame(94,config);
    state=applyAction(state,{type:'start_game',actorId:'p1'}).state;
    state=applyAction(state,{type:'roll',actorId:'p1'}).state;
    assert.ok(state.players[0].position>0);
    const restored=deserializeGame(serializeGame(state)).game;
    assert.deepEqual(restored,state);
    restored.map.cells[0].column=999;
    assert.equal(createGame(94,config).map.cells[0].column,1);
    assert.throws(()=>validateMap(restored.map,count),/地图/);
    assert.throws(()=>levelConfig('missing'),/关卡/);
  }
});
test('60/120/360 格各 30 种子、2/3/4 人真实完整模拟，无非法动作且存档不丢格',async()=>{
  const {levelConfig}=await data();
  for(const [id,count] of sizes)for(let seed=0;seed<30;seed++){
    const config={...levelConfig(id),maxRounds:12,propertyVisitOnly:true,stockAccount:'bank',
      strategyEnabled:true,specialEnabled:true,bankEnabled:true,loanEnabled:true,marketEnabled:true,
      automaticLiquidation:true,players:Array.from({length:2+seed%3},(_,i)=>({id:'p'+(i+1),name:'测试'+i,kind:'computer'}))};
    const report=runSimulation(seed,{config,maxActions:5000});
    assert.equal(report.finalState.status,'finished',`${id} seed=${seed}`);
    assert.equal(report.rejections,0);
    assert.equal(report.finalState.tiles.length,count);
    assert.ok(report.finalState.players.every(p=>p.position>=0&&p.position<count&&p.cash>=0));
    assert.deepEqual(deserializeGame(serializeGame(report.finalState)).game,report.finalState);
  }
});

test('JSON 轮廓通过通用生成命令形成完整容器；拒绝斜边和自交重叠',async()=>{
  await data();
  const {mkdtempSync,writeFileSync,rmSync}=await import('node:fs');
  const {tmpdir}=await import('node:os');
  const {join}=await import('node:path');
  const {spawnSync}=await import('node:child_process');
  const dir=mkdtempSync(join(tmpdir(),'reactmono-map-'));
  try{
    const input=join(dir,'outline.json'),output=join(dir,'level.json');
    const recipe={id:'generated-test',name:'凹形试验',description:'数据轮廓测试',outline:[[0,0],[8,0],[8,3],[4,3],[4,6],[0,6]]};
    writeFileSync(input,JSON.stringify(recipe));
    const run=()=>{if(existsSync(output))rmSync(output);return spawnSync(process.execPath,['scripts/generate-map.mjs',input,output],{encoding:'utf8'});};
    assert.equal(run().status,0,'通用生成命令必须成功');
    const result=JSON.parse(readFileSync(output,'utf8')).levels[0];
    assert.equal(result.tiles.length,28);
    assert.equal(result.map.id,'generated-test');
    const checked=spawnSync(process.execPath,['scripts/validate-maps.mjs',output],{encoding:'utf8'});
    assert.equal(checked.status,0,checked.stderr);
    assert.deepEqual(result.map.cells[8],{column:9,row:1});
    assert.deepEqual(result.map.cells[11],{column:9,row:4});
    recipe.outline=[[0,0],[8,3],[0,6]];
    writeFileSync(input,JSON.stringify(recipe));
    assert.notEqual(run().status,0,'斜边必须拒绝');
    recipe.outline=[[0,0],[8,0],[8,3],[0,3],[0,0],[4,0],[4,6],[0,6]];
    writeFileSync(input,JSON.stringify(recipe));
    assert.notEqual(run().status,0,'重复路径必须拒绝');
  }finally{rmSync(dir,{recursive:true,force:true});}
});

// A map with relocated facilities must remain entirely expressible as data.
test('JSON 设施地点可迁移，非法设施引用和参数提前拒绝',async()=>{
  const {loadLevelCatalog,levelConfig}=await data();
  const source=JSON.parse(readFileSync('src/data/levels.json','utf8'));
  const level=source.levels.find(l=>l.map.id==='bend-60');
  assert.ok(level.facilityConfig,'关卡容器必须声明设施');
  level.facilityConfig.hospitalTiles=[15];
  level.facilityConfig.prisonTiles=[21];
  level.facilityConfig.shopTiles=[24];
  const loaded=loadLevelCatalog(source).find(l=>l.map.id==='bend-60');
  const cfg={...levelConfig('bend-60'),facilityConfig:loaded.facilityConfig,strategyEnabled:true,specialEnabled:true};
  const state=createGame(94,cfg);
  assert.equal(state.tiles[15].facility,'hospital');
  assert.equal(state.tiles[21].facility,'prison');
  assert.equal(state.tiles[24].facility,'shop');
  assert.equal(state.tiles[3].facility,undefined);
  assert.deepEqual(deserializeGame(serializeGame(state)).game,state);
  for(const mutate of [f=>f.hospitalTiles=[1],f=>f.shopTiles=[21],f=>f.prices.remote=-1,f=>f.stock.reward=101]){
    const c=structuredClone(source);mutate(c.levels.find(l=>l.map.id==='bend-60').facilityConfig);
    assert.throws(()=>loadLevelCatalog(c),/关卡/);
  }
});
