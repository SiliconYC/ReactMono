"""#41 real offline Chromium: special map setup, detention, shop buy, IndexedDB resume."""
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler
import re

def run():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
            context=browser.new_context(service_workers='allow',accept_downloads=True)
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('dialog',lambda d:d.accept('特殊设施离线' if d.type=='prompt' else None))
            url=f'http://127.0.0.1:{server.server_port}/ReactMono/'
            page.goto(url)
            page.wait_for_function('navigator.serviceWorker.controller!==null')
            context.set_offline(True)
            # Seed 98 produces first die=3 and lands human on hospital on the classic map.
            page.reload(wait_until='load')
            assert '已断网' in page.locator('.network-indicator').inner_text()
            page.get_by_label('对局种子').fill('98')
            page.get_by_label('启用医院、监狱与商店').check()
            page.get_by_label('快速模式').check()
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            assert page.locator('.tile').filter(has_text='医院').count()==1
            assert page.locator('.tile').filter(has_text='监狱').count()==1
            assert page.locator('.tile').filter(has_text='商店').count()==1
            page.get_by_role('button',name=re.compile('掷骰前进')).click()
            page.wait_for_function("document.querySelector('.players-card')?.textContent.includes('住院剩余 2 回合')")
            page.get_by_role('button',name='创建手动存档').click()
            slot=page.locator('.save-list li').filter(has_text='特殊设施离线')
            slot.wait_for()
            page.reload(wait_until='load')
            slot=page.locator('.save-list li').filter(has_text='特殊设施离线')
            slot.get_by_role('button',name='读取').click()
            page.wait_for_function("document.querySelector('.players-card')?.textContent.includes('住院剩余 2 回合')")
            page.get_by_role('button',name='结束当前回合').click()
            page.get_by_role('button',name='跳过当前停留回合').wait_for(timeout=25000)
            page.get_by_role('button',name='跳过当前停留回合').click()
            page.get_by_role('button',name='跳过当前停留回合').wait_for(timeout=25000)
            assert '住院剩余 1 回合' in page.locator('.players-card').inner_text()
            page.get_by_role('button',name='跳过当前停留回合').click()
            page.get_by_role('button',name=re.compile('掷骰前进')).wait_for(timeout=25000)
            assert '住院剩余' not in page.locator('.players-card').inner_text()
            # Seed 104: human rolls 5, computer rolls 1, human rolls 4 -> prison #9.
            page.reload(wait_until='load')
            page.get_by_label('对局种子').fill('104')
            page.get_by_label('启用医院、监狱与商店').check()
            page.get_by_label('快速模式').check()
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            page.get_by_role('button',name=re.compile('掷骰前进')).click()
            page.get_by_role('button',name='购买地产').click()
            page.get_by_role('button',name='结束当前回合').click()
            page.get_by_role('button',name=re.compile('掷骰前进')).wait_for(timeout=25000)
            page.get_by_role('button',name=re.compile('掷骰前进')).click()
            page.wait_for_function("document.querySelector('.players-card')?.textContent.includes('入狱剩余 3 回合')")
            page.get_by_role('button',name='结束当前回合').click()
            page.get_by_role('button',name='跳过当前停留回合').wait_for(timeout=25000)
            page.get_by_role('button',name='跳过当前停留回合').click()
            assert '入狱剩余 2 回合' in page.locator('.players-card').inner_text()
            # Visit the shop on each original map, while keeping the whole route real,
            # no mutable engine state injection, no fake React rendering.
            for board in ['classic-24','harbor-20']:
                page.reload(wait_until='load')
                page.get_by_label('游戏地图').select_option(board)
                page.get_by_label('对局种子').fill('5')
                page.get_by_label('最多轮数').fill('75')
                page.get_by_label('启用医院、监狱与商店').check()
                page.get_by_label('快速模式').check()
                page.get_by_role('button',name=re.compile('开始游戏')).click()
                result=page.evaluate("""async()=>{
                  const click=s=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes(s)&&!x.disabled);if(!b)return false;b.click();return true};
                  for(let i=0;i<7000;i++){
                    const main=document.querySelector('main');
                    if(main?.dataset.gamePhase==='await_shop'&&[...document.querySelectorAll('button')].some(b=>b.textContent.includes('离开商店')))return {shop:true,i};
                    if(main?.dataset.gameStatus==='finished')return {shop:false,finished:true,i};
                    if(click('使用奖励卡')||click('使用步数卡')||click('使用免租卡')||
                       click('放置路障')||click('使用遥控骰子')){}
                    else if(!click('掷骰前进')&&!click('跳过当前停留回合')&&!click('购买地产')&&!click('放弃购买')&&!click('结束当前回合')){}
                    await new Promise(r=>setTimeout(r,12));
                  }
                  return {shop:false,timeout:true};
                }""")
                assert result.get('shop'),(board,result)
                # Confirm actual legal buying deducts money & decrements stock.
                bought=False
                for btn in page.locator('.purchase-actions button').all():
                    if '购买' in btn.inner_text() and '卡' in btn.inner_text() and btn.is_enabled():
                        text=btn.inner_text()
                        btn.click()
                        assert '购买' in page.locator('.activity-card').inner_text()
                        bought=True
                        break
                assert bought,('No affordable shop goods',board)
                page.get_by_role('button',name='创建手动存档').click()
                page.locator('.save-list li').filter(has_text='特殊设施离线').wait_for()
                page.reload(wait_until='load')
                page.locator('.save-list li').filter(has_text='特殊设施离线').get_by_role('button',name='读取').click()
                page.wait_for_function("document.querySelector('main')?.dataset.gamePhase==='await_shop'")
                page.get_by_role('button',name='离开商店').click()
                assert page.locator('main').get_attribute('data-game-phase')=='await_end_turn'
            assert not errors,errors
            print('PASS: real Chrome offline hospital detention/resume, two map shops and purchases')
            browser.close()
    finally:
        server.shutdown();thread.join()

if __name__=='__main__':run()
