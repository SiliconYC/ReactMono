"""#67 genuine Chromium: presentation updates must not alter economic or RNG trace."""
from http.server import ThreadingHTTPServer
from threading import Thread
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler
import json,re,os

OUT=Path('artifacts/issue67')

def game(page):
    page.get_by_label('对局种子').fill('17')
    page.get_by_label('快速模式').uncheck()
    page.get_by_label('最多轮数').fill('3')
    page.get_by_role('button',name=re.compile('开始游戏')).click()

def actions(page):
    trace=[]
    for n in range(15):
        current=page.locator('main')
        if current.get_attribute('data-game-status')=='finished':break
        phase=current.get_attribute('data-game-phase')
        if phase=='await_roll':
            page.get_by_role('button',name=re.compile('掷骰前进')).click()
            trace.append(('roll',page.locator('.turn-position').inner_text(),current.get_attribute('data-game-revision')))
        elif phase=='await_decision':page.get_by_role('button',name='购买地产').click()
        elif phase=='await_end_turn':page.get_by_role('button',name=re.compile('结束当前回合')).click()
        elif phase=='await_shop':page.get_by_role('button',name='离开商店').click()
        else:break
        if page.locator('.handoff-panel').count():
            page.get_by_role('button',name='我已就位，开始操作').click()
        if page.locator('.turn-tip').count():trace.append(('message',page.locator('.turn-tip').inner_text()))
    return trace

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
 t=Thread(target=server.serve_forever,daemon=True);t.start()
 reports=[];errs=[]
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
   for label,enabled,reduce,width,height in [('desktop',True,False,1440,900),('mobile-off',False,False,390,844),('reduced',True,True,390,844)]:
    ctx=browser.new_context(viewport={'width':width,'height':height},service_workers='allow',reduced_motion='reduce' if reduce else 'no-preference')
    page=ctx.new_page()
    page.on('pageerror',lambda err:errs.append(str(err)))
    page.on('dialog',lambda d:d.accept())
    page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/')
    assert page.locator('link[href="./motion.css"]').count()==1
    if not enabled:page.get_by_role('button',name='关闭动效').click()
    game(page)
    before=page.locator('main').get_attribute('data-game-revision')
    page.get_by_role('button',name=re.compile('掷骰前进')).click()
    after=page.locator('main').get_attribute('data-game-revision')
    assert before!=after
    if enabled and not reduce:
     cue=page.locator('.event-feedback')
     assert cue.count()==1 and cue.get_attribute('data-event-revision')==after
     assert page.locator('.motion-skip').is_visible()
     page.screenshot(path=str(OUT/'desktop-motion.png'),animations='disabled')
     page.get_by_role('button',name='跳过动效').click()
     assert page.locator('.event-feedback').count()==0
     assert page.locator('main').get_attribute('data-game-revision')==after
    else:assert page.locator('.event-feedback').count()==0
    if not enabled:
     page.reload()
     assert page.get_by_role('button',name='开启动效').count()==1
     assert page.locator('.event-feedback').count()==0
    ctx.close()
    reports.append({'name':label,'initialRevision':before,'rolledRevision':after,'visualsEnabled':enabled and not reduce})
   browser.close()
  assert not errs,errs
  (OUT/'report.json').write_text(json.dumps({'scenarios':reports,'errors':errs,'humanFeedback':False},ensure_ascii=False,indent=2),encoding='utf8')
  print('PASS P4 #67 Chromium motion cues, skip, reduced motion, persisted toggle',reports)
 finally:
  server.shutdown();t.join()
if __name__=='__main__':main()
