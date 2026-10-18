"""#69: a genuinely new browser can complete onboarding, first economy, handoff, backup, offline."""
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler, open_new_game_setup, select_map
import json,re
OUT=Path('artifacts/issue69')

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
 worker=Thread(target=server.serve_forever,daemon=True);worker.start()
 errors=[];results=[]
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
   for name,width,height in [('desktop',1440,900),('phone',390,844),('narrow',320,640)]:
    ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<500,has_touch=width<500,
      service_workers='allow',device_scale_factor=1)
    page=ctx.new_page()
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('dialog',lambda d:d.accept('引导存档' if d.type=='prompt' else None))
    page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/',wait_until='load')
    open_new_game_setup(page)
    assert page.locator('link[href="./guide.css"]').count()==1
    guide=page.get_by_role('region',name='新手引导')
    assert guide.is_visible() and guide.get_attribute('data-guide-step')=='1'
    startRev=page.locator('main').get_attribute('data-game-revision')
    page.get_by_role('button',name='下一步').click()
    assert guide.get_attribute('data-guide-step')=='2'
    page.get_by_role('button',name='下一步').click()
    assert guide.get_attribute('data-guide-step')=='3'
    page.get_by_role('button',name='完成引导').click()
    assert guide.count()==0
    assert page.evaluate("localStorage.getItem('reactmono-guide-seen')")=='1'
    assert page.locator('main').get_attribute('data-game-revision')==startRev
    page.get_by_role('button',name='新手帮助').focus()
    page.keyboard.press('Enter')
    assert guide.count()==1
    page.get_by_role('button',name='跳过引导').click()
    assert guide.count()==0
    page.get_by_label('玩家人数').select_option('2')
    page.get_by_label('第 2 位玩家类型').select_option('human')
    page.get_by_label('对局种子').fill('17')
    page.get_by_label('快速模式').check()
    page.get_by_role('button',name=re.compile('开始游戏')).click()
    context=page.locator('details.context-help')
    assert context.count()==1
    context.locator('summary').click()
    assert '策略卡' in context.inner_text()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
    page.screenshot(path=str(OUT/f'{name}-novice.png'),full_page=True,animations='disabled')
    page.get_by_role('button',name=re.compile('掷骰前进')).click()
    if page.locator('main').get_attribute('data-game-phase')=='await_decision':
      assert '买地' in context.inner_text()
      page.get_by_role('button',name='购买地产').click()
    assert page.locator('main').get_attribute('data-game-phase')=='await_end_turn'
    page.get_by_role('button',name='银行',exact=True).click()
    page.get_by_label('银行交易金额').fill('50')
    page.get_by_role('button',name='存入银行').click()
    assert '银行存款：' in page.locator('.turn-position').inner_text()
    page.get_by_role('button',name='创建手动存档').click()
    page.locator('.save-list li').filter(has_text='引导存档').wait_for()
    page.get_by_role('button',name=re.compile('结束当前回合')).click()
    assert page.locator('.handoff-panel').is_visible()
    page.get_by_role('button',name='我已就位，开始操作').click()
    assert page.locator('.turn-person .character-portrait').get_attribute('data-character-id')=='bear'
    page.screenshot(path=str(OUT/f'{name}-handoff.png'),full_page=True,animations='disabled')
    page.reload(wait_until='load')
    assert page.get_by_role('region',name='新手引导').count()==0
    page.locator('.save-list li').filter(has_text='引导存档').get_by_role('button',name='读取').click()
    page.wait_for_function("document.querySelector('.save-message')?.textContent.includes('已读取')")
    assert page.locator('.turn-person .character-portrait').get_attribute('data-character-id')=='fox'
    page.wait_for_function('navigator.serviceWorker.controller!==null',timeout=30000)
    ctx.set_offline(True)
    page.reload(wait_until='load')
    assert page.get_by_role('button',name='新手帮助').is_visible()
    page.get_by_role('button',name='新手帮助').click()
    assert page.get_by_role('region',name='新手引导').count()==1
    page.screenshot(path=str(OUT/f'{name}-offline-guide.png'),full_page=True,animations='disabled')
    results.append({'case':name,'viewport':[width,height],'firstAndReturn':True,'economyAndHandoff':True,'offline':True})
    ctx.close()
   browser.close()
  assert not errors,errors
  (OUT/'report.json').write_text(json.dumps({'scenarios':results,'pageErrors':errors,'realUsers':False},ensure_ascii=False,indent=2),encoding='utf8')
  print('PASS #69 Chromium first-use, keyboard, contextual help, economy, handoff, save, offline',results)
 finally:server.shutdown();worker.join()

if __name__=='__main__':main()
