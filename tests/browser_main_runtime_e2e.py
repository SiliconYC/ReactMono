"""Main-game keyboard, WebAudio/GPU, save rejection and SW upgrade acceptance."""
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright, expect
from browser_live_e2e import open_new_game_setup
from browser_main_game_acceptance import fixture, load_fixture, export_current, open_panel, click_confirm
from browser_sw_upgrade_e2e import UpdateHandler
import json, re, time

OUT=Path('artifacts/ui-rebuild');OUT.mkdir(parents=True,exist_ok=True)
METRICS='''(()=>{
 window.__metrics={draws:0,audioStarts:0,audioEnds:0,notes:[],puts:0,longTasks:[],frames:[]};
 for(const name of ['drawElements','drawArrays']){
  const old=WebGL2RenderingContext.prototype[name];WebGL2RenderingContext.prototype[name]=function(...args){window.__metrics.draws++;return old.apply(this,args)};
 }
 const start=OscillatorNode.prototype.start;OscillatorNode.prototype.start=function(...args){window.__metrics.audioStarts++;this.addEventListener('ended',()=>window.__metrics.audioEnds++,{once:true});return start.apply(this,args)};
 const set=AudioParam.prototype.setValueAtTime;AudioParam.prototype.setValueAtTime=function(value,...args){if(this.defaultValue===440)window.__metrics.notes.push(value);return set.call(this,value,...args)};
 const put=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(...args){if(this.name==='slots')window.__metrics.puts++;return put.apply(this,args)};
 try{new PerformanceObserver(list=>window.__metrics.longTasks.push(...list.getEntries().map(x=>x.duration))).observe({type:'longtask',buffered:true})}catch{}
 let last=null;const frame=t=>{if(last!==null)window.__metrics.frames.push(t-last);last=t;requestAnimationFrame(frame)};requestAnimationFrame(frame);
})()'''

def main():
 UpdateHandler.version=0
 server=ThreadingHTTPServer(('127.0.0.1',0),UpdateHandler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
 url=f'http://127.0.0.1:{server.server_port}/ReactMono/'
 errors=[];results=[];samples=[]
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
   ctx=browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce',accept_downloads=True,service_workers='allow');ctx.add_init_script(METRICS)
   page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept('当前验收' if d.type=='prompt' else None))
   # Real WebAudio invocation, persistence and reduced-motion demand rendering.
   load_fixture(page,url,fixture(''),'运行时')
   open_panel(page,'设置');page.get_by_label('开启音效',exact=True).check();page.get_by_label('音效音量').fill('65');page.keyboard.press('Escape')
   page.get_by_role('button',name='掷骰前进').click();assert page.locator('main').get_attribute('data-presenting')=='false'
   page.wait_for_function('window.__metrics.audioStarts>0')
   page.wait_for_timeout(650)
   assert page.evaluate('window.__metrics.audioStarts===window.__metrics.audioEnds')
   state,backup=export_current(page)
   open_panel(page,'银行');page.wait_for_timeout(200);draws=page.evaluate('window.__metrics.draws');page.wait_for_timeout(250);assert page.evaluate('window.__metrics.draws')==draws
   page.keyboard.press('Escape');page.wait_for_timeout(250);draws=page.evaluate('window.__metrics.draws');page.wait_for_timeout(250);assert page.evaluate('window.__metrics.draws')==draws
   open_panel(page,'设置');page.get_by_label('开启音效',exact=True).uncheck();assert page.evaluate("localStorage.getItem('reactmono-audio-volume')")=='0.65';page.keyboard.press('Escape')
   samples.append({'stage':'audio-and-reduced-idle','revision':page.locator('main').get_attribute('data-game-revision'),'metrics':page.evaluate('window.__metrics')})
   results.append('WebAudio确实启动/节点回收，音效音量持久化，减少动态闲置与模态GPU停止绘制')
   normal=browser.new_context(viewport={'width':1280,'height':720},reduced_motion='no-preference',service_workers='allow');normal.add_init_script(METRICS)
   np=normal.new_page();np.on('pageerror',lambda e:errors.append(str(e)))
   raw=fixture("game={...game,tiles:game.tiles.map(t=>t.id===1?{...t,ownerId:'p2',level:2}:t),players:game.players.map((p,i)=>i===0?{...p,cash:1}:p)};")
   load_fixture(np,url,raw,'声音因果');open_panel(np,'设置');np.get_by_label('开启音效',exact=True).check();np.keyboard.press('Escape')
   np.get_by_role('button',name='掷骰前进').click();np.wait_for_timeout(250)
   assert np.evaluate('window.__metrics.notes.slice(0,3)')==[350,465,510], ('finish/rent sound must not precede the dice',np.evaluate('window.__metrics.notes'))
   np.locator('.result-box').wait_for(timeout=12000)
   samples.append({'stage':'dice-rent-outcome-audio','metrics':np.evaluate('window.__metrics')})
   normal.close();results.append('掷骰/走路/租金/结局音效与演出因果顺序一致')
   # Mutating a backup without checksum must not affect the current session or slots.
   open_panel(page,'存档');count=page.locator('.save-list li').count();revision=page.locator('main').get_attribute('data-game-revision')
   modified=json.loads(backup);modified['game']['randomState']+=1
   page.get_by_label('导入 JSON 存档文件').set_input_files({'name':'损坏.json','mimeType':'application/json','buffer':json.dumps(modified).encode()})
   expect(page.locator('.save-message')).to_contain_text('导入失败')
   assert page.locator('.save-list li').count()==count
   assert page.locator('main').get_attribute('data-game-revision')==revision
   page.get_by_label('导入 JSON 存档文件').set_input_files({'name':'副本.json','mimeType':'application/json','buffer':backup})
   page.get_by_label('导入存档名称').fill('当前验收');page.get_by_role('button',name='另存为副本').click()
   page.locator('.save-list li').filter(has=page.get_by_text('当前验收（副本）',exact=True)).wait_for()
   results.append('损坏校验拒绝且对局/档位未变，同名存档另存副本')
   # Cover and delete one manual slot without changing its sibling.
   page.keyboard.press('Escape');page.get_by_role('button',name=re.compile('购买地产')).click()
   open_panel(page,'存档');row=page.locator('.save-list li').filter(has=page.get_by_text('当前验收',exact=True)).first
   row.get_by_role('button',name='覆盖',exact=True).click();page.get_by_role('button',name='确认操作',exact=True).click()
   expect(page.locator('.save-message')).to_contain_text('已覆盖')
   with page.expect_download() as d:row.get_by_role('button',name='导出',exact=True).click()
   covered=json.loads(Path(d.value.path()).read_bytes())['game'];assert covered['tiles'][1]['ownerId']=='p1'
   row.get_by_role('button',name='删除',exact=True).click();page.get_by_role('button',name='取消',exact=True).click();assert row.count()==1
   row.get_by_role('button',name='删除',exact=True).click();page.get_by_role('button',name='确认操作',exact=True).click();expect(row).to_have_count(0)
   assert page.locator('.save-list li').filter(has=page.get_by_text('当前验收（副本）',exact=True)).count()==1
   results.append('手动覆盖保存真实新状态，取消删除/确认删除，另一存档保留')
   # Collect a full CPU game before navigation resets the runtime counters.
   raw=fixture("game=act(createGame(70070,{...cfg,maxRounds:3,players:[{id:'p1',name:'谨慎电脑',kind:'computer',computerStyle:'conservative'},{id:'p2',name:'进取电脑',kind:'computer',computerStyle:'aggressive'}]}),'start_game');")
   load_fixture(page,url,raw,'完整局性能');start=time.monotonic();page.locator('.result-box').wait_for(timeout=60000)
   revision=int(page.locator('main').get_attribute('data-game-revision'));metrics=page.evaluate('window.__metrics')
   assert metrics['draws']>0 and metrics['puts']<=revision+3
   samples.append({'stage':'complete-cpu-game','revision':revision,'elapsedMs':round((time.monotonic()-start)*1000),'metrics':metrics})
   final,_=export_current(page);assert final['status']=='finished'
   results.append('完整电脑对局长任务/帧间隔/绘制/IndexedDB写入原始指标')
   # Two human seats separated by a CPU still require handing the device over.
   raw=fixture("game=act(createGame(17,{...cfg,players:[{id:'p1',name:'甲',kind:'human'},{id:'p2',name:'电脑',kind:'computer'},{id:'p3',name:'乙',kind:'human'}]}),'start_game');game={...game,currentPlayerIndex:1,phase:'await_end_turn'};")
   load_fixture(page,url,raw,'人机人交接')
   page.get_by_role('button',name='我已就位，开始操作').wait_for(timeout=15000)
   assert not page.get_by_role('button',name='掷骰前进').count()
   page.get_by_role('button',name='我已就位，开始操作').click();page.get_by_role('button',name='掷骰前进').wait_for()
   results.append('人→电脑→人交接，确认前不能投骰')
   # Pointer-down belongs to its original action, even when the presentation is skipped.
   load_fixture(page,url,fixture(''),'双击')
   page.get_by_role('button',name='掷骰前进').dblclick()
   assert page.locator('main').get_attribute('data-die-nonce')=='1'
   assert page.locator('main').get_attribute('data-game-phase')=='await_decision'
   assert page.get_by_role('button',name=re.compile('购买地产')).count()==1
   results.append('减少动态下双击投骰不会误触下一阶段购买')
   # An actual SW installs a second version and waits for explicit player action.
   saved,backup=export_current(page)
   page.wait_for_function('navigator.serviceWorker.controller!==null')
   old_keys=page.evaluate("caches.keys()")
   UpdateHandler.version=1
   page.evaluate('async()=>{const r=await navigator.serviceWorker.ready;await r.update()}')
   page.wait_for_function('async()=>Boolean((await navigator.serviceWorker.ready).waiting)',timeout=20000)
   assert page.evaluate('caches.keys()')!=old_keys
   assert page.locator('main').get_attribute('data-game-revision')==str(saved['revision'])
   open_panel(page,'设置');page.get_by_text('版本与离线状态',exact=True).click()
   with page.expect_navigation(wait_until='load',timeout=20000):page.get_by_role('button',name='保存并更新版本',exact=True).click()
   page.wait_for_function("async()=>{const keys=await caches.keys();return keys.includes('reactmono-0123456789abcdef')&&keys.filter(k=>k.startsWith('reactmono-')).length===1}")
   ctx.set_offline(True);page.reload(wait_until='load');page.get_by_role('button',name='继续游戏').click();page.locator('main.app-shell').wait_for()
   restored,_=export_current(page);assert restored==saved
   open_panel(page,'玩法说明');assert '经营地产' in page.locator('dialog').inner_text()
   results.append('双Service Worker等待显式更新、旧缓存清理、断网重载读档/帮助')
   # Collect actual browser timings/counters, never claim a physical-phone measurement.
   metrics=page.evaluate('window.__metrics');metrics['resources']=page.evaluate('performance.getEntriesByType("resource").map(e=>({name:e.name.split("/").pop(),bytes:e.decodedBodySize}))')
   assert not errors,errors
   (OUT/'runtime.json').write_text(json.dumps({'passed':results,'samples':samples,'browserMetrics':metrics,'errors':errors,'physicalPhone':False},ensure_ascii=False,indent=2))
   print('PASS '+json.dumps(results,ensure_ascii=False),flush=True)
   ctx.close();browser.close()
 finally:server.shutdown();thread.join()
if __name__=='__main__':main()
