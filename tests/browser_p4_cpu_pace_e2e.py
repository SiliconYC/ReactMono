"""#70 real browser: CPU pause, resumption, timing and same-seed fast/normal outcomes."""
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler
import json,re,time
OUT=Path('artifacts/issue70')

def configure(page,board,n,cpu=0):
  page.get_by_label('游戏地图').select_option(board)
  page.get_by_label('玩家人数').select_option(str(n))
  page.get_by_label('对局种子').fill('70070')
  page.get_by_label('最多轮数').fill('3')
  page.get_by_label('启用医院、监狱与商店').check()
  for i in range(n):
    page.get_by_label(f'第 {i+1} 位玩家类型').select_option('computer' if i<n-cpu else 'human')
    if i<n-cpu:page.get_by_label(f'第 {i+1} 位电脑策略').select_option(['conservative','balanced','aggressive'][i%3])

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
 thread=Thread(target=server.serve_forever,daemon=True);thread.start()
 records=[];errors=[]
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
   for width,height,board,n in [(1440,900,'classic-24',2),(390,844,'harbor-20',3),(320,640,'classic-24',4)]:
    snapshots=[]
    for fast in [False,True]:
     context=browser.new_context(viewport={'width':width,'height':height},service_workers='allow',is_mobile=width<500,has_touch=width<500)
     page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
     page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/')
     configure(page,board,n)
     if fast:page.get_by_label('快速模式').check()
     start=time.monotonic()
     page.get_by_role('button',name=re.compile('开始游戏')).click()
     if fast:
       assert page.get_by_role('button',name='恢复正常速度').count()==1
       page.get_by_role('button',name='暂停电脑').click()
       frozen=page.locator('main').get_attribute('data-game-revision')
       page.wait_for_timeout(480)
       assert page.locator('main').get_attribute('data-game-revision')==frozen
       page.get_by_role('button',name='继续电脑').click()
     page.wait_for_function("document.querySelector('main')?.dataset.gameStatus==='finished'",timeout=95000)
     elapsed=round((time.monotonic()-start)*1000)
     summary=page.locator('.asset-quick-roster').inner_text()
     revision=page.locator('main').get_attribute('data-game-revision')
     page.screenshot(path=str(OUT/(f'{board}-{n}-'+('fast' if fast else 'normal')+'.png')),animations='disabled',full_page=True)
     snapshots.append({'mode':'fast' if fast else 'normal','elapsedMs':elapsed,
       'revision':revision,'assets':summary})
     context.close()
    assert snapshots[0]['revision']==snapshots[1]['revision'],snapshots
    assert snapshots[0]['assets']==snapshots[1]['assets'],snapshots
    records.append({'map':board,'seats':n,'modes':snapshots})
   # Mixed human/CPU handoff stays a true human decision, not computer autoplay.
   ctx=browser.new_context(viewport={'width':390,'height':844},service_workers='allow')
   page=ctx.new_page();page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/')
   configure(page,'harbor-20',2,cpu=1)
   page.get_by_role('button',name=re.compile('开始游戏')).click()
   page.wait_for_function("document.querySelector('.turn-person .character-portrait')?.dataset.characterSeat==='2' && document.querySelector('main')?.dataset.gamePhase==='await_roll'",timeout=20000)
   assert page.get_by_role('button',name=re.compile('掷骰前进')).count()==1
   r=page.locator('main').get_attribute('data-game-revision')
   page.wait_for_timeout(350)
   assert r==page.locator('main').get_attribute('data-game-revision')
   page.screenshot(path=str(OUT/'mixed-human-wait.png'),full_page=True,animations='disabled')
   ctx.close()
   browser.close()
  assert not errors,errors
  (OUT/'report.json').write_text(json.dumps({'samples':records,'errors':errors,'humanParticipants':0},ensure_ascii=False,indent=2),encoding='utf8')
  print('PASS #70 real Chromium CPU pacing and deterministic fast/normal game outcomes',records)
 finally:server.shutdown();thread.join()

if __name__=='__main__':main()
