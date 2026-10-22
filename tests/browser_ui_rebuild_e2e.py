"""Independent UI acceptance: visible choices, real transactions, modal isolation."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import os, re

URL=os.environ.get('GAME_URL','http://127.0.0.1:4174/')
OUT=Path(os.environ.get('UI_SCREENSHOTS','artifacts/ui-rebuild/viewports'));OUT.mkdir(parents=True,exist_ok=True)
def visible_in_view(page,locator):
    box=locator.bounding_box();assert box, 'missing element'
    assert box['x']>=0 and box['y']>=0 and box['x']+box['width']<=page.viewport_size['width']+1 and box['y']+box['height']<=page.viewport_size['height']+1, box
    assert locator.evaluate('(e)=>e.getBoundingClientRect().height>=40'), 'touch target too small'

def main():
 with sync_playwright() as p:
  b=p.chromium.launch(channel='chrome',headless=True)
  for w,h in [(1440,900),(1280,720),(1920,1080),(2560,1440),(390,844),(360,640),(844,390)]:
   c=b.new_context(viewport={'width':w,'height':h},reduced_motion='no-preference');page=c.new_page();errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept())
   page.goto(URL);page.get_by_role('heading',name='大富翁 2026',exact=True).wait_for()
   visible_in_view(page,page.get_by_role('button',name='开始游戏'))
   page.screenshot(path=str(OUT/f'title-{w}.png'))
   page.get_by_role('button',name='开始游戏').click()
   assert page.get_by_label('第 1 位玩家姓名').is_visible(), 'seat setup must not be hidden in advanced settings'
   page.get_by_label('玩家人数').select_option('4')
   assert page.get_by_label('第 4 位玩家姓名').is_visible()
   page.get_by_label('玩家人数').select_option('2')
   page.screenshot(path=str(OUT/f'setup-{w}.png'))
   page.get_by_role('button',name='开始游戏',exact=True).click()
   page.locator('.canvas-shell[data-ready=true]').wait_for(timeout=20000)
   page.wait_for_timeout(600)
   visible_in_view(page,page.get_by_role('button',name='掷骰前进'))
   assert page.locator('.turn-card').evaluate('(e)=>e.scrollHeight<=e.clientHeight+2'), 'action bar must not scroll'
   page.screenshot(path=str(OUT/f'turn-{w}.png'))
   page.get_by_role('button',name='银行',exact=True).click()
   dialog=page.get_by_role('dialog');assert dialog.is_visible()
   assert page.evaluate('document.activeElement.closest("dialog")!==null'), 'focus inside modal'
   assert dialog.evaluate('(e)=>e.matches(":modal")'), 'dialog must make background inert'
   try:
    page.get_by_role('button',name='掷骰前进',exact=False).click(timeout=250)
    raise AssertionError('background turn action accepted through modal')
   except Exception as error:
    assert 'Timeout' in type(error).__name__, error
   page.get_by_label('银行交易金额',exact=True).fill('100')
   page.get_by_role('button',name='存入银行',exact=True).click()
   assert '1,400' in dialog.inner_text()
   page.screenshot(path=str(OUT/f'bank-{w}.png'))
   page.keyboard.press('Escape');assert page.get_by_role('dialog').count()==0
   assert page.evaluate('document.activeElement.textContent')=='银行'
   page.get_by_role('button',name='掷骰前进').dblclick()
   assert page.get_by_role('button',name=re.compile('购买地产')).count()==0
   page.get_by_role('button',name=re.compile('购买地产')).wait_for(timeout=8000)
   for name in ['购买地产','暂不购买']:
    visible_in_view(page,page.get_by_role('button',name=re.compile(name)))
   assert '1,290' in page.locator('.turn-card').inner_text(), 'purchase balance preview'
   assert page.locator('.turn-card').evaluate('(e)=>e.scrollHeight<=e.clientHeight+2')
   page.screenshot(path=str(OUT/f'arrival-{w}.png'))
   page.get_by_role('button',name=re.compile('购买地产')).click()
   page.get_by_role('button',name=re.compile('^菜单')).click()
   page.get_by_role('dialog').get_by_role('button',name=re.compile('^设置')).click()
   assert page.evaluate('document.activeElement.closest("dialog")!==null'), 'focus lost after modal content switch'
   page.keyboard.press('Escape')
   assert not errors,errors
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   print(f'PASS visible title/setup/arrival, purchase + deposit, modal focus at {w}×{h}')
   c.close()
  from browser_main_game_acceptance import fixture,load_fixture
  raw=fixture("game=act(createGame(17,{...cfg,players:Array.from({length:4},(_,i)=>({id:'p'+(i+1),name:'这是一位姓名很长的小镇投资人'+i,kind:'human'}))}),'start_game');game={...game,players:game.players.map(p=>({...p,cash:999999999999}))};")
  for name,w,h,scale in [('four-long-names',360,640,1),('zoom-200',720,450,2)]:
   c=b.new_context(viewport={'width':w,'height':h},device_scale_factor=scale);page=c.new_page();load_fixture(page,URL,raw,name)
   assert page.locator('.player-card').evaluate_all('(es)=>es.every(e=>e.scrollWidth<=e.clientWidth+1)'), 'large balance overflow'
   visible_in_view(page,page.get_by_role('button',name='掷骰前进'))
   page.locator('.player-card').first.click()
   assert '999,999,999,999' in page.get_by_role('dialog').inner_text()
   page.keyboard.press('Escape');page.screenshot(path=str(OUT/f'{name}.png'));c.close()
  print('PASS four long names / large balances and 200% equivalent viewport')
  b.close()
if __name__=='__main__':
 if os.environ.get('GAME_URL'):main()
 else:
  from http.server import ThreadingHTTPServer
  from threading import Thread
  from browser_live_e2e import Handler
  server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
  URL=f'http://127.0.0.1:{server.server_port}/ReactMono/'
  try:main()
  finally:server.shutdown();thread.join()
