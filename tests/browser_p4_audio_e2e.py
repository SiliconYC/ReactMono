"""P4 #68 real Chromium: default mute, user-gesture synthesis, reload, offline and mobile."""
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler
import json,re
OUT=Path('artifacts/issue68')

def run():
 OUT.mkdir(parents=True,exist_ok=True)
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
 thread=Thread(target=server.serve_forever,daemon=True);thread.start()
 errors=[];reports=[]
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
   for name,w,h in [('desktop',1440,900),('phone',390,844)]:
    context=browser.new_context(viewport={'width':w,'height':h},service_workers='allow',has_touch=w<500)
    page=context.new_page()
    page.add_init_script("""{
      window.__starts=0;
      const original=OscillatorNode.prototype.start;
      OscillatorNode.prototype.start=function(...args){window.__starts++;return original.apply(this,args)};
    }""")
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/')
    assert page.locator('link[href="./audio.css"]').count()==1
    assert page.get_by_role('button',name='开启音效').get_attribute('aria-pressed')=='false'
    page.get_by_label('对局种子').fill('17')
    page.get_by_role('button',name='开启音效').click()
    assert page.get_by_role('button',name='关闭音效').get_attribute('aria-pressed')=='true'
    slider=page.get_by_label('音效音量')
    slider.focus();slider.press('End')
    for _ in range(7):slider.press('ArrowLeft')
    assert page.evaluate("localStorage.getItem('reactmono-audio-volume')")=='0.65'
    page.wait_for_timeout(140)
    page.get_by_role('button',name=re.compile('开始游戏')).click()
    page.get_by_role('button',name=re.compile('掷骰前进')).click()
    page.wait_for_function('window.__starts>=1',timeout=10000)
    played=page.evaluate('window.__starts')
    assert played>=1
    page.screenshot(path=str(OUT/f'{name}-audio-enabled.png'),full_page=True,animations='disabled')
    page.get_by_role('button',name='关闭音效').click()
    assert page.get_by_role('button',name='开启音效').count()==1
    silenced=page.evaluate('window.__starts')
    if page.locator('main').get_attribute('data-game-phase')=='await_decision':
      page.get_by_role('button',name='购买地产').click()
    assert page.evaluate('window.__starts')==silenced
    page.reload(wait_until='load')
    assert page.get_by_role('button',name='开启音效').count()==1
    page.get_by_role('button',name='开启音效').click()
    assert page.get_by_label('音效音量').input_value()=='65'
    page.wait_for_function('navigator.serviceWorker.controller!==null',timeout=30000)
    context.set_offline(True)
    page.reload(wait_until='load')
    assert page.locator('link[href="./audio.css"]').count()==1
    assert page.get_by_role('button',name='关闭音效').count()==1
    page.get_by_role('button',name='关闭音效').click()
    page.screenshot(path=str(OUT/f'{name}-offline-muted.png'),full_page=True,animations='disabled')
    reports.append({'viewport':name,'synthOscillators':played,'mutePersisted':True,'volumePersisted':True,'offline':True})
    context.close()
   browser.close()
  assert not errors,errors
  (OUT/'report.json').write_text(json.dumps({'results':reports,'pageErrors':errors,'humanFeedback':False},ensure_ascii=False,indent=2),encoding='utf8')
  print('PASS #68 procedural Web Audio controls',reports)
 finally:server.shutdown();thread.join()
if __name__=='__main__':run()
