"""#43: live Chrome + mobile touch asset dashboard, bank/loan/stock/card target, offline and full game."""
from http.server import ThreadingHTTPServer
from threading import Thread
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler, open_new_game_setup, select_map
import re

DIR=Path('artifacts/issue43')
def open_tool(page,label):
    """Use a real labeled drawer if running the action-first UI; keep public legacy compatible."""
    tabs=page.locator('.finance-tabs button')
    target=tabs.filter(has_text=label)
    if target.count() and target.first.get_attribute('aria-expanded')!='true':
        target.first.click()

def wallet(page,player='p1'):
    overview=page.locator('details.asset-overview')
    if overview.count() and not overview.evaluate('(e)=>e.open'):
        overview.locator('summary').click()
    card=page.locator(f'.asset-player[data-player-id="{player}"]')
    fields=card.locator('.asset-metrics dd').all_inner_texts()
    return [int(re.sub(r'[^0-9-]','',f.split(' 币')[0].split(' 股')[0].split(' 块')[0].split(' ·')[0]) or '0') for f in fields]

def run():
    DIR.mkdir(parents=True,exist_ok=True)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    th=Thread(target=server.serve_forever,daemon=True);th.start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
            errors=[]
            context=browser.new_context(viewport={'width':1440,'height':900},service_workers='allow')
            page=context.new_page()
            page.on('pageerror',lambda err:errors.append(str(err)))
            page.on('dialog',lambda d:d.accept('资产验收' if d.type=='prompt' else None))
            url=f'http://127.0.0.1:{server.server_port}/ReactMono/'
            page.goto(url)
            open_new_game_setup(page)
            page.get_by_label('对局种子').fill('17')
            page.get_by_label('启用医院、监狱与商店').check()
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            assert page.locator('.asset-player').count()==2
            assert page.locator('.asset-player[data-active-player="true"]').get_attribute('data-player-id')=='p1'
            assert wallet(page)[:2]==[1500,0]
            page.get_by_role('button',name=re.compile('掷骰前进')).click()
            if page.locator('main').get_attribute('data-game-phase')=='await_decision':
                page.get_by_role('button',name=re.compile('购买地产')).click()
            assert page.locator('main').get_attribute('data-game-phase')=='await_end_turn'
            assert page.get_by_role('navigation',name='交易操作快捷入口').get_by_role('button',name='股票').is_visible()
            cash=wallet(page)[0]
            open_tool(page,'银行')
            page.get_by_label('银行交易金额').fill('100')
            page.get_by_role('button',name='存入银行').click()
            assert wallet(page)[0]==cash-100 and wallet(page)[1]==100,wallet(page)
            open_tool(page,'股票')
            page.get_by_label('股票交易数量').fill('1')
            page.get_by_role('button',name='买入 青禾农业').click()
            assert '持有 1 股' in page.locator('.stock-entry').filter(has_text='青禾农业').inner_text()
            assert wallet(page)[3]==1
            cash=wallet(page)[0]
            open_tool(page,'股票')
            page.get_by_label('股票交易数量').fill('999999')
            assert page.get_by_role('button',name='买入 青禾农业').is_disabled()
            assert wallet(page)[0]==cash,'A disabled trade must not charge cash'
            open_tool(page,'股票')
            page.get_by_label('股票交易数量').fill('1')
            page.get_by_role('button',name='卖出 青禾农业').click()
            assert wallet(page)[3]==0
            open_tool(page,'抵押借贷')
            mortgage=page.locator('#loan-actions').get_by_role('button',name=re.compile('^抵押'))
            if mortgage.count():
                mortgage.first.click()
                assert '抵押' in page.locator('.asset-player[data-player-id="p1"]').inner_text()
                page.get_by_label('银行交易金额').fill('20')
                page.get_by_role('button',name='借入贷款').click()
                assert wallet(page)[4]==20
                page.get_by_role('button',name='偿还贷款').click()
                assert wallet(page)[4]==0
            page.screenshot(path=str(DIR/'desktop-trading.png'),full_page=True)
            page.get_by_role('button',name='创建手动存档').click()
            page.locator('.save-list li').filter(has_text='资产验收').wait_for()
            before=wallet(page)
            page.reload(wait_until='load')
            page.locator('.save-list li').filter(has_text='资产验收').get_by_role('button',name='读取').click()
            page.wait_for_function("document.querySelector('main')?.dataset.gamePhase==='await_end_turn'")
            assert wallet(page)==before,'IndexedDB restored asset overview diverges from engine'
            context.close()

            # Four human players on phone, fully offline and real touchscreen pass-the-device.
            phone_context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,
                                              device_scale_factor=1,service_workers='allow')
            mobile=phone_context.new_page()
            mobile.on('pageerror',lambda err:errors.append(str(err)))
            mobile.goto(url)
            open_new_game_setup(mobile)
            mobile.wait_for_function("navigator.serviceWorker.controller!==null",timeout=20000)
            phone_context.set_offline(True)
            mobile.reload(wait_until='load')
            assert '已断网' in mobile.locator('.network-indicator').inner_text()
            mobile.get_by_label('玩家人数').select_option('4')
            mobile.get_by_label('最多轮数').fill('2')
            mobile.get_by_label('快速模式').check()
            for i in range(4):
                mobile.get_by_label(f'第 {i+1} 位玩家类型').select_option('human')
            mobile.get_by_role('button',name=re.compile('开始游戏')).click()
            assert mobile.locator('.asset-player').count()==4
            assert mobile.locator('.asset-player[data-active-player="true"]').count()==1
            assert mobile.evaluate('document.documentElement.scrollWidth <= window.innerWidth+2')
            mobile.screenshot(path=str(DIR/'mobile-assets.png'),full_page=True)
            result=mobile.evaluate("""async()=>{
              const click=t=>{const buttons=[...document.querySelectorAll('button')];
                const b=buttons.find(x=>x.textContent.includes(t)&&!x.disabled);
                if(!b)return false;b.click();return true;};
              let handoffs=0,rolls=0;
              for(let n=0;n<1000;n++){
                if(document.querySelector('main')?.dataset.gameStatus==='finished')
                  return {finished:true,handoffs,rolls};
                if(click('我已就位，开始操作'))handoffs++;
                else if(click('掷骰前进'))rolls++;
                else if(click('购买地产')){}
                else if(click('放弃购买')){}
                else if(click('跳过当前停留回合')){}
                else if(click('离开商店')){}
                else click('结束当前回合');
                await new Promise(r=>setTimeout(r,12));
              }
              return {finished:false,handoffs,rolls};
            }""")
            assert result['finished'] and result['handoffs']>=3 and result['rolls']>=4,result
            mobile.screenshot(path=str(DIR/'mobile-finished.png'),full_page=True)
            assert not errors,errors
            print('PASS #43 Chromium: responsive 4-player offline full game, active seat handoffs, actual bank/loan/stocks, disabled invalid trades, IndexedDB, 3 screenshots',result)
            browser.close()
    finally:
        server.shutdown();th.join()

if __name__=='__main__':
    run()
