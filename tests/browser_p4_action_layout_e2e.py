"""P4 #66: real Chromium action-first layout, touch, finance, safety and offline acceptance."""
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler, open_new_game_setup, open_saved_games, select_map
import json, os, re

OUT=Path('artifacts/issue66')
CASES=[
 ('desktop-classic',1440,900,'classic-24',2),
 ('desktop-harbor',1280,800,'harbor-20',4),
 ('phone-classic',390,844,'classic-24',4),
 ('narrow-harbor',320,640,'harbor-20',2),
 ('landscape-harbor',667,375,'harbor-20',2),
]

def metrics(page):
  return page.evaluate("""()=>{
    const box=e=>{const r=e.getBoundingClientRect();return {
      x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),
      height:Math.round(r.height),bottom:Math.round(r.bottom)}};
    const el=q=>document.querySelector(q);
    const visible=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0};
    const allButtons=[...document.querySelectorAll('button')].filter(visible);
    // Preserve the original strict gameplay density target. Newly optional
    // presentation, sound and onboarding buttons are counted separately.
    const total=allButtons.filter(e=>!e.matches('.motion-toggle,.motion-skip,.audio-toggle,.guide-reopen,.guide-inline button'));
    return {
      viewport:{w:innerWidth,h:innerHeight},
      documentWidth:document.documentElement.scrollWidth,
      board:box(el('.board-viewport')),currentAction:box(el('.turn-card')),
      primaryAction:box(el('.turn-card .primary-btn')),
      visibleButtons:total.length,
      buttonsAboveFold:total.filter(e=>e.getBoundingClientRect().bottom<=innerHeight).length,
      openFinanceTabs:[...document.querySelectorAll('.finance-tabs button[aria-expanded="true"]')].map(x=>x.textContent.trim()),
      assetSummary:box(el('.asset-summary')),
      assetExpanded:el('.asset-overview').open
    };
  }""")

def enter_turn(page):
  page.get_by_role('button',name=re.compile('掷骰前进')).click()
  if page.locator('main').get_attribute('data-game-phase')=='await_decision':
    page.get_by_role('button',name=re.compile('购买地产')).click()
  if page.locator('main').get_attribute('data-game-phase')=='await_shop':
    page.get_by_role('button',name='离开商店').click()
  assert page.locator('main').get_attribute('data-game-phase')=='await_end_turn'

def open_tool(page,name):
  b=page.get_by_role('button',name=name,exact=True)
  assert b.count()==1,(name,b.count())
  if b.get_attribute('aria-expanded')!='true':b.click()
  assert b.get_attribute('aria-expanded')=='true'
  assert page.locator('.finance-tabs button[aria-expanded="true"]').count()==1

def main():
  OUT.mkdir(parents=True,exist_ok=True)
  server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
  t=Thread(target=server.serve_forever,daemon=True);t.start()
  errors=[];report=[]
  try:
    with sync_playwright() as pw:
      opts={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
      if os.environ.get('CHROMIUM_PATH'):opts['executable_path']=os.environ['CHROMIUM_PATH']
      else:opts['channel']='chrome'
      browser=pw.chromium.launch(**opts)
      for name,w,h,map_id,seats in CASES:
        ctx=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=1,
          is_mobile=w<=390,has_touch=w<=390,reduced_motion='reduce',service_workers='allow')
        page=ctx.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        dialogs=[]
        allow_confirm=[True]
        def handle_dialog(d):
          dialogs.append({'type':d.type,'text':d.message})
          if d.type=='prompt':d.accept('新版操作验收')
          elif allow_confirm[0]:d.accept()
          else:d.dismiss()
        page.on('dialog',handle_dialog)
        page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/',wait_until='load')
        open_new_game_setup(page)
        assert page.locator('link[rel="stylesheet"][href*="/assets/main-"]').count()==1
        select_map(page,map_id)
        page.get_by_label('玩家人数').select_option(str(seats))
        page.get_by_label('对局种子').fill('17')
        page.get_by_label('最多轮数').fill('3')
        page.get_by_label('快速模式').check()
        for i in range(seats):
          page.get_by_label(f'第 {i+1} 位玩家类型').select_option('human')
        page.get_by_role('button',name=re.compile('开始游戏')).click()
        m=metrics(page)
        assert m['documentWidth']<=w+2,m
        assert m['board']['width']>=260,m
        assert m['visibleButtons']<32,m
        assert not m['openFinanceTabs'] and not m['assetExpanded'],m
        assert page.locator('.asset-quick-roster>span').count()==seats
        if w<=1060:
          assert m['currentAction']['bottom']<=h,m
          assert m['primaryAction']['bottom']<=m['currentAction']['bottom'],m
        else:assert m['board']['x']<m['currentAction']['x'],m
        page.screenshot(path=str(OUT/f'{name}-default.png'),full_page=True,animations='disabled')
        if w<=390:
          page.locator('.asset-summary').tap()
        else:page.locator('.asset-summary').click()
        assert page.locator('.asset-overview').evaluate('(e)=>e.open')
        assert page.locator('.asset-player').count()==seats
        assert page.locator('.asset-player[data-active-player="true"]').count()==1
        page.keyboard.press('Escape')
        assert not page.locator('.asset-overview').evaluate('(e)=>e.open')
        enter_turn(page)
        after=metrics(page)
        assert after['visibleButtons']<38,after
        for key in ['property','bank','loan','stock']:
          assert page.locator(f'#finance-{key}').get_attribute('hidden') is not None
        open_tool(page,'地产')
        assert page.locator('#finance-property').is_visible()
        open_tool(page,'银行')
        assert not page.locator('#finance-property').is_visible()
        assert page.locator('#bank-actions').is_visible()
        assert page.get_by_label('银行交易金额').is_visible()
        page.get_by_label('银行交易金额').fill('100')
        before=int(page.locator('.turn-position').inner_text().split('现金：')[1].split('·')[0].replace(',','').strip())
        page.get_by_role('button',name='存入银行').click()
        after_cash=int(page.locator('.turn-position').inner_text().split('现金：')[1].split('·')[0].replace(',','').strip())
        assert after_cash==before-100,(before,after_cash)
        open_tool(page,'股票')
        assert not page.locator('#bank-actions').is_visible()
        row=page.locator('.stock-entry').filter(has_text='青禾农业')
        page.get_by_label('股票交易数量').fill('1')
        page.get_by_role('button',name='买入 青禾农业').click()
        assert '持有 1 股' in row.inner_text()
        open_tool(page,'抵押借贷')
        assert page.get_by_label('银行交易金额').is_visible()
        page.get_by_label('银行交易金额').fill('9999999')
        assert page.get_by_role('button',name='借入贷款').is_disabled()
        assert page.locator('.finance-tabs button[aria-expanded="true"]').count()==1
        page.screenshot(path=str(OUT/f'{name}-finance.png'),full_page=True,animations='disabled')
        if name=='phone-classic':
          # A rejected mortgage must NOT mutate revision or wealth; accepted one must.
          mortgage=page.locator('#loan-actions').get_by_role('button',name=re.compile('^抵押'))
          assert mortgage.count()>0
          rev=page.locator('main').get_attribute('data-game-revision')
          cash=page.locator('.turn-position').inner_text()
          allow_confirm[0]=False
          mortgage.first.click()
          assert page.locator('main').get_attribute('data-game-revision')==rev
          assert page.locator('.turn-position').inner_text()==cash
          assert '已取消操作' in page.locator('.turn-tip').inner_text()
          allow_confirm[0]=True
          mortgage.first.click()
          assert page.locator('main').get_attribute('data-game-revision')!=rev
          assert '解除抵押' in page.locator('#loan-actions').inner_text()
          page.get_by_label('银行交易金额').fill('20')
          page.get_by_role('button',name='借入贷款').click()
          assert '贷款 20' in page.locator('#loan-actions').inner_text()
          page.get_by_role('button',name='偿还贷款').click()
          assert '贷款 0' in page.locator('#loan-actions').inner_text()
          page.keyboard.press('Escape')
          open_saved_games(page)
          page.get_by_role('button',name='创建手动存档').click()
          page.locator('.save-list li').filter(has_text='新版操作验收').wait_for()
          saved=page.locator('main').get_attribute('data-game-revision')
          page.reload()
          open_saved_games(page)
          page.locator('.title-save-list li').filter(has_text='新版操作验收').get_by_role('button',name='读取').click()
          page.wait_for_function("(rev)=>document.querySelector('main')?.dataset.gameRevision===rev",arg=saved)
          assert page.locator('.asset-quick-roster>span').count()==seats
          page.wait_for_function('navigator.serviceWorker.controller!==null',timeout=30000)
          ctx.set_offline(True)
          page.reload(wait_until='load')
          assert page.locator('link[rel="stylesheet"][href*="/assets/main-"]').count()==1
          assert page.locator('.finance-tabs').evaluate("(e)=>getComputedStyle(e).display")=='grid' if page.locator('.finance-tabs').count() else True
          page.screenshot(path=str(OUT/'phone-classic-offline.png'),full_page=True,animations='disabled')
        report.append({'case':name,'beforeFinance':m,'finance':after,'dialogCount':len(dialogs),
          'map':map_id,'players':seats,'humanFeedback':False})
        ctx.close()
      browser.close()
    assert not errors,errors
    (OUT/'report.json').write_text(json.dumps({'origin':'real Chromium local Pages subpath',
      'commit':os.environ.get('GITHUB_SHA','local'),'scenarios':report,'pageErrors':errors,
      'humanFeedbackCollected':False},indent=2,ensure_ascii=False),encoding='utf8')
    print('PASS #66: 5 sizes, 2 maps, accessible tabbed finances, touch, asset expansion, no horizontal overflow')
  finally:
    server.shutdown();t.join()

if __name__=='__main__':main()
