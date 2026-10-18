"""Current 3D main-game acceptance against the actual production PWA.

Replaces historical 2D DOM assumptions with real rule-generated save fixtures,
physical UI input, canvas frames, IndexedDB/file round trips and offline play.
No game state is changed through React internals or a test-only app API.
"""
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright, expect
from browser_live_e2e import Handler, open_new_game_setup, select_map
import json, re, subprocess, time, os

OUT=Path('artifacts/ui-rebuild');OUT.mkdir(parents=True,exist_ok=True)

def fixture(script):
 code="""import {createGame,applyAction,DEFAULT_CONFIG,HARBOR_CONFIG} from './.test-dist/core/game.js';
 import {serializeGame} from './.test-dist/core/save.js';
 const cfg={...DEFAULT_CONFIG,players:[{id:'p1',name:'玩家',kind:'human'},{id:'p2',name:'对手',kind:'human'}],maxRounds:4,propertyVisitOnly:true,stockAccount:'bank',bankEnabled:true,loanEnabled:true,marketEnabled:true,strategyEnabled:true,specialEnabled:true};
 const act=(s,type,extra={})=>{const r=applyAction(s,{type,actorId:s.players[s.currentPlayerIndex].id,...extra});if(!r.ok)throw new Error(type+': '+r.reason);return r.state};
 let game=act(createGame(17,cfg),'start_game');
 """+script+"\nconsole.log(serializeGame(game));"
 return subprocess.check_output(['node','--input-type=module','-e',code],text=True).strip().encode()

def open_panel(page,name):
 if page.locator('dialog').count():page.keyboard.press('Escape')
 if name=='存档' and page.locator('.result-box').count():
  page.get_by_role('button',name='保存或导出',exact=True).click()
 elif name in ['银行','股票','地产','手牌']:
  page.locator('.hud-tools').get_by_role('button',name=re.compile('^'+name)).click()
 else:
  page.get_by_role('button',name=re.compile('^菜单')).click()
  page.get_by_role('dialog').get_by_role('button',name=re.compile('^'+name)).click()

def click_confirm(page,name):
 page.get_by_role('button',name=name,exact=True).click()
 if page.get_by_role('heading',name='确认操作',exact=True).count():page.get_by_role('button',name='确认操作',exact=True).click()

def load_fixture(page,url,raw,name='验收样本'):
 page.goto(url)
 if page.locator('.title-shell').count():page.get_by_role('button',name='读取存档').click()
 else:open_panel(page,'存档')
 page.get_by_label('导入 JSON 存档文件').set_input_files({'name':name+'.json','mimeType':'application/json','buffer':raw})
 page.get_by_label('导入存档名称').fill(name)
 if page.get_by_role('button',name='另存为副本').count():page.get_by_role('button',name='另存为副本').click();name+='（副本）'
 else:page.get_by_role('button',name='确认导入存档').click()
 page.locator('.save-list li').filter(has=page.get_by_text(name,exact=True)).get_by_role('button',name='读取',exact=True).click()
 page.locator('main.app-shell').wait_for()
 page.locator('.canvas-shell[data-ready=true]').wait_for(timeout=20000)


def export_current(page):
 open_panel(page,'存档')
 rows=page.locator('.save-list li').filter(has=page.get_by_text('当前验收',exact=True));count=rows.count()
 page.get_by_role('button',name='创建手动存档').click()
 expect(rows).to_have_count(count+1)
 row=rows.first
 with page.expect_download() as d:row.get_by_role('button',name='导出',exact=True).click()
 raw=Path(d.value.path()).read_bytes()
 page.keyboard.press('Escape')
 return json.loads(raw)['game'],raw


def finish_human_turn(page):
 for _ in range(15):
  if page.get_by_role('button',name=re.compile('购买地产')).count():
   b=page.get_by_role('button',name=re.compile('购买地产'))
   if b.is_enabled():b.click()
   else:page.get_by_role('button',name='暂不购买').click()
  elif page.get_by_role('button',name='结束当前回合').count():page.get_by_role('button',name='结束当前回合').click();return
  elif page.get_by_role('button',name='暂不建设').count():page.get_by_role('button',name='暂不建设').click();return
  elif page.get_by_role('button',name='离开商店').count():page.get_by_role('button',name='离开商店').click()
  else:page.wait_for_timeout(150)
  page.wait_for_timeout(360)
 raise AssertionError('could not finish human turn')


def main():
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
 url=f'http://127.0.0.1:{server.server_port}/ReactMono/'
 report=[];errors=[]
 try:
  with sync_playwright() as p:
   launch={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
   if os.environ.get('CHROMIUM_PATH'):launch['executable_path']=os.environ['CHROMIUM_PATH']
   else:launch['channel']='chrome'
   browser=p.chromium.launch(**launch)
   ctx=browser.new_context(viewport={'width':1280,'height':720},accept_downloads=True,service_workers='allow')
   page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('dialog',lambda d:d.accept('当前验收' if d.type=='prompt' else None))
   # 1–6: actual intermediate actor callbacks, arrival barrier, skip/normal equality.
   seeds=json.loads(subprocess.check_output(['node','--input-type=module','-e',"import {createGame,applyAction} from './.test-dist/core/game.js';let found={};for(let n=1;Object.keys(found).length<6;n++){let g=createGame(n);g=applyAction(g,{type:'start_game',actorId:'p1'}).state;let r=applyAction(g,{type:'roll',actorId:'p1'});let v=r.events.find(e=>e.type==='die_rolled').details.value;found[v]??=n}console.log(JSON.stringify(found))"],text=True))
   for die,seed in seeds.items():
    raw=fixture(f"game=act(createGame({seed},cfg),'start_game');")
    load_fixture(page,url,raw,'骰点'+die)
    page.get_by_role('button',name='掷骰前进').click()
    page.wait_for_timeout(180)
    assert page.locator('main').get_attribute('data-presenting')=='true'
    assert not page.locator('.action-buttons .primary-btn').count()
    before_frame=page.locator('canvas').screenshot()
    steps=[];start=time.monotonic()
    while page.locator('main').get_attribute('data-presenting')=='true' and time.monotonic()-start<9:
     steps.append(int(page.locator('main').get_attribute('data-scene-step')));page.wait_for_timeout(60)
    assert not page.locator('main[data-presenting=true]').count()
    assert max(steps,default=0)>0,(die,steps)
    assert before_frame!=page.locator('canvas').screenshot(), '3D must actually render different frames'
    if int(die)>=3:assert any(0<s<int(die) for s in steps),(die,steps)
    normal,_=export_current(page)
    assert [e for e in normal['events'] if e['type']=='die_rolled'][-1]['details']['value']==int(die)
    load_fixture(page,url,raw,'跳过'+die)
    page.get_by_role('button',name='掷骰前进').click();page.get_by_role('button',name='跳过演出').click()
    skipped,_=export_current(page)
    assert normal==skipped,'skipping presentation must preserve exact rule state'
   report.append('1–6 点实际中间帧/输入屏障/正常与跳过存档等价')
   print('PASS stage: '+report[-1],flush=True)
   # Cash, deposits, stocks, mortgages and loans use the real production commands.
   raw=fixture("game=act(game,'roll');game=act(game,'buy_property');")
   load_fixture(page,url,raw,'交易样本')
   assert page.get_by_role('button',name=re.compile('建造住宅')).count()==0,'same visit cannot build immediately after buying'
   nonce=page.locator('main').get_attribute('data-die-nonce')
   open_panel(page,'银行');page.get_by_label('银行交易金额').fill('200');click_confirm(page,'存入银行')
   assert '1,190' in page.locator('.account-summary').inner_text()
   page.get_by_label('银行交易金额').fill('75');click_confirm(page,'从银行取款')
   page.locator('.finance-tabs').get_by_role('button',name='股票',exact=True).click()
   page.get_by_label('股票交易数量').fill('1');page.get_by_role('button',name=re.compile('^买入 ')).first.click()
   assert '持有 1 股' in page.locator('.stock-entry').first.inner_text()
   page.get_by_role('button',name=re.compile('^卖出 ')).first.click()
   assert '持有 0 股' in page.locator('.stock-entry').first.inner_text()
   page.locator('.finance-tabs').get_by_role('button',name='抵押借贷',exact=True).click()
   click_confirm(page,'抵押地产');page.get_by_label('银行交易金额').fill('20');click_confirm(page,'借入贷款')
   assert page.locator('.account-summary b').nth(2).inner_text()=='20'
   click_confirm(page,'偿还贷款');click_confirm(page,'解除抵押')
   assert page.locator('.account-summary b').nth(2).inner_text()=='0'
   assert page.locator('main').get_attribute('data-die-nonce')==nonce
   page.keyboard.press('Escape');state,backup=export_current(page)
   assert state['players'][0]['loanBalance']==0
   assert state['players'][0]['bankBalance']==123
   load_fixture(page,url,backup,'交易往返')
   restored,_=export_current(page);assert state==restored
   report.append('现金/存款/股票买卖手续费/抵押借还/解除抵押/文件往返/不重掷')
   print('PASS stage: '+report[-1],flush=True)
   # Legacy stock accounts continue to use cash, preserving bank deposits.
   raw=fixture("delete game.stockAccount;game=act(game,'roll');game=act(game,'decline_property');game={...game,players:game.players.map((p,i)=>i===0?{...p,bankBalance:100}:p)};")
   load_fixture(page,url,raw,'旧现金股票');open_panel(page,'股票')
   page.get_by_role('button',name=re.compile('^买入 ')).first.click()
   old_stock,_=export_current(page);assert old_stock['players'][0]['cash']<1500 and old_stock['players'][0]['bankBalance']==100
   open_panel(page,'股票');page.get_by_role('button',name=re.compile('^卖出 ')).first.click()
   old_sold,_=export_current(page);assert old_sold['players'][0]['cash']>old_stock['players'][0]['cash'] and old_sold['players'][0]['bankBalance']==100
   report.append('旧档现金股票账户买卖，银行存款不变')
   print('PASS stage: '+report[-1],flush=True)
   # Direct visit building and legacy unrestricted property management.
   for level in [0,1]:
    raw=fixture(f"game={{...game,tiles:game.tiles.map(t=>t.id===1?{{...t,ownerId:'p1',level:{level}}}:t)}};game=act(game,'roll');")
    load_fixture(page,url,raw,'到访建设'+str(level))
    page.get_by_role('button',name=re.compile('^(建造住宅|升级房屋)')).click()
    page.wait_for_timeout(370)
    assert page.get_by_role('button',name=re.compile('^(建造住宅|升级房屋)')).count()==0
    built,_=export_current(page);assert built['tiles'][1]['level']==level+1
   raw=fixture("delete game.propertyVisitOnly;game={...game,tiles:game.tiles.map(t=>t.id===2?{...t,ownerId:'p1',level:0}:t)};game=act(game,'roll');game=act(game,'decline_property');")
   load_fixture(page,url,raw,'旧规则建设');open_panel(page,'地产')
   page.get_by_role('button',name=re.compile('^建造住宅')).click()
   legacy,_=export_current(page);assert legacy['tiles'][2]['level']==1 and 'propertyVisitOnly' not in legacy
   open_panel(page,'地产')
   page.get_by_role('button',name=re.compile('^出售 ·')).click();page.get_by_role('button',name='确认操作',exact=True).click()
   sold,_=export_current(page);assert sold['tiles'][2]['ownerId'] is None and sold['players'][0]['cash']>legacy['players'][0]['cash']
   report.append('直接建设/升级/同到访一次/旧规则异地升级兼容')
   print('PASS stage: '+report[-1],flush=True)
   # All five existing card types, with independently validated save inputs.
   for kind,label in [('reward','使用奖励卡'),('stride','使用步数卡'),('remote','使用遥控骰子'),('roadblock','放置路障'),('rent_free','使用免租卡')]:
    raw=fixture(f"game={{...game,players:game.players.map((p,i)=>i===0?{{...p,cards:{{reward:0,stride:0,remote:0,roadblock:0,rent_free:0,{kind}:1}}}}:p)}};")
    load_fixture(page,url,raw,'卡片'+kind);open_panel(page,'手牌')
    if kind=='remote':page.get_by_label('遥控骰点').select_option('4')
    page.get_by_role('button',name=label,exact=True).click()
    used,_=export_current(page);assert used['players'][0]['cards'][kind]==0
    assert used['events'][-1]['type']=='card_used'
    if kind=='remote':assert used['pendingDie']==4
    if kind=='roadblock':assert len(used['roadblocks'])==1
    if kind=='rent_free':assert used['pendingRentWaiver'] is True
   report.append('五种手牌真实使用、目标选择与持久化')
   print('PASS stage: '+report[-1],flush=True)
   # Hospitals/prisons/shop: use actual landing rules, then physically click legal actions.
   facilities=json.loads(fixture(''))['game']['tiles']
   for facility in ['hospital','prison','shop']:
    tile=next(t['id'] for t in facilities if t.get('facility')==facility)
    raw=fixture(f"game={{...game,players:game.players.map((p,i)=>i===0?{{...p,position:{tile-1}}}:p)}};game=act(game,'roll');")
    load_fixture(page,url,raw,'设施'+facility)
    if facility=='shop':
     page.locator('.shop-offers button:not([disabled])').first.click();page.get_by_role('button',name='离开商店').click()
     bought,_=export_current(page);assert any(e['type']=='shop_purchased' for e in bought['events'])
    else:
     finish_human_turn(page);page.get_by_role('button',name='我已就位，开始操作').click()
     page.get_by_role('button',name='掷骰前进').click();page.get_by_role('button',name='跳过演出').click();finish_human_turn(page)
     page.get_by_role('button',name='我已就位，开始操作').click()
     page.get_by_role('button',name='跳过当前停留回合').click()
     detention,_=export_current(page);assert any(e['type']=='detention_skipped' for e in detention['events'])
   report.append('真实商店购买、医院/监狱停留、跳过和真人交接')
   print('PASS stage: '+report[-1],flush=True)
   # Rent → bankruptcy → victory stay ordered, with no actionable turn underneath.
   raw=fixture("game={...game,tiles:game.tiles.map(t=>t.id===1?{...t,ownerId:'p2',level:2}:t),players:game.players.map((p,i)=>i===0?{...p,cash:1}:p)};")
   load_fixture(page,url,raw,'破产演出');page.get_by_role('button',name='掷骰前进').click()
   assert not page.locator('.result-box').count()
   page.locator('.result-box').wait_for(timeout=12000)
   assert '对手获胜' in page.locator('.result-box').inner_text()
   assert not page.locator('.action-buttons .primary-btn').count()
   report.append('租金→破产→胜利与结果输入隔离')
   print('PASS stage: '+report[-1],flush=True)
   # A modal cancels a pending CPU timer, closing it resumes the same state.
   raw=fixture("game={...game,players:game.players.map(p=>({...p,kind:'computer',computerStyle:'balanced'}))};")
   load_fixture(page,url,raw,'电脑暂停');page.get_by_role('button',name=re.compile('^菜单')).click()
   revision=page.locator('main').get_attribute('data-game-revision');page.wait_for_timeout(1100)
   assert page.locator('main').get_attribute('data-game-revision')==revision
   page.keyboard.press('Escape');page.wait_for_function('(old)=>document.querySelector("main").dataset.gameRevision!==old',arg=revision,timeout=6000)
   report.append('待执行电脑计时器在菜单期间暂停，关闭后恢复')
   print('PASS stage: '+report[-1],flush=True)
   # Full real games on both maps, four seats, fixed seeds, fast/normal end states equal.
   for board in ['classic-24','harbor-20']:
    outcomes=[]
    for fast in [False,True]:
     c=browser.new_context(viewport={'width':390,'height':844},accept_downloads=True,service_workers='allow');pg=c.new_page();pg.on('dialog',lambda d:d.accept('当前验收' if d.type=='prompt' else None));pg.on('pageerror',lambda e:errors.append(str(e)))
     pg.goto(url);open_new_game_setup(pg);select_map(pg,board);pg.get_by_label('玩家人数').select_option('4');pg.get_by_label('最多轮数').fill('2');pg.get_by_label('对局种子').fill('70070');pg.get_by_label('启用医院、监狱与商店').check()
     for i in range(4):
      pg.get_by_label(f'第 {i+1} 位玩家类型').select_option('computer')
      pg.get_by_label(f'第 {i+1} 位电脑策略').select_option(['conservative','balanced','aggressive','balanced'][i])
     pg.get_by_label('快速模式').set_checked(fast);pg.get_by_role('button',name='开始游戏',exact=True).click()
     pg.locator('.result-box').wait_for(timeout=95000)
     final,raw_final=export_current(pg);outcomes.append(final)
     assert [p['computerStyle'] for p in final['players']]==['conservative','balanced','aggressive','balanced']
     load_fixture(pg,url,raw_final,'策略回读');restored,_=export_current(pg);assert restored==final
     pg.screenshot(path=str(OUT/f'{board}-4-{fast}.png'));c.close()
    assert outcomes[0]==outcomes[1],board
   report.append('两图四人完整局，正常/快速最终规则状态完全等价')
   print('PASS stage: '+report[-1],flush=True)
   # Production SW starts and resumes the same local match without network.
   page.goto(url);page.wait_for_function('navigator.serviceWorker.controller!==null',timeout=15000)
   open_new_game_setup(page);page.get_by_role('button',name='开始游戏',exact=True).click()
   page.get_by_role('button',name='掷骰前进').click();page.get_by_role('button',name='跳过演出').click()
   before,raw=export_current(page);ctx.set_offline(True);page.reload(wait_until='load')
   page.get_by_role('button',name='继续游戏').click();page.locator('main.app-shell').wait_for()
   after,_=export_current(page);assert before==after
   open_panel(page,'设置');page.get_by_text('版本与离线状态',exact=True).click();assert '当前离线' in page.locator('dialog').inner_text()
   report.append('生产 PWA 断网重载/自动存档续局/文件导出等价')
   print('PASS stage: '+report[-1],flush=True)
   assert not errors,errors
   (OUT/'acceptance.json').write_text(json.dumps({'passed':report,'pageErrors':errors,'humanParticipants':0,'physicalPhones':0},ensure_ascii=False,indent=2))
   print('PASS '+json.dumps(report,ensure_ascii=False),flush=True)
   ctx.close();browser.close()
 finally:server.shutdown();thread.join()
if __name__=='__main__':main()
