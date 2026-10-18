"""P3-05：真实 Chromium 两图多人整局、选图、存读档及手机布局。"""
from http.server import ThreadingHTTPServer
from threading import Thread
from browser_local_multiplayer_e2e import Handler
from browser_live_e2e import open_new_game_setup, open_saved_games, select_map
from playwright.sync_api import sync_playwright
import re

def exercise(browser,url,map_id,size,players):
    page=browser.new_page(viewport={'width':390 if players==4 else 1440,'height':900})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(url,wait_until='load')
    open_new_game_setup(page)
    select_map(page,map_id)
    assert page.locator('.setup-map-choice button').count()==2
    selected=page.locator('.setup-map-choice button[aria-pressed="true"]')
    assert selected.count()==1
    assert ('海港' in selected.inner_text())==(map_id=='harbor-20')
    page.get_by_label('玩家人数').select_option(str(players))
    for i in range(players):
        page.get_by_label(f'第 {i+1} 位玩家类型').select_option('human' if i==0 else 'computer')
    page.get_by_label('对局种子').fill('17')
    page.get_by_label('最多轮数').fill('3')
    page.get_by_label('快速模式').check()
    page.get_by_role('button',name=re.compile('开始游戏')).click()
    assert page.locator('main').get_attribute('data-map-id')==map_id
    name=f'地图验收-{map_id}-{players}'
    page.on('dialog',lambda dialog:dialog.accept(name if dialog.type=='prompt' else None))
    open_saved_games(page)
    page.get_by_role('button',name='创建手动存档').click()
    page.locator('.save-list li').filter(has_text=name).wait_for()
    page.reload()
    open_saved_games(page)
    page.locator('.title-save-list li').filter(has_text=name).get_by_role('button',name='读取').click()
    page.wait_for_function("document.querySelector('main')?.dataset.gameStatus==='playing'")
    assert page.locator('main').get_attribute('data-map-id')==map_id
    assert page.locator('.tile').count()==size
    assert page.locator('.player-line').count()==players
    report=page.evaluate("""async()=>{
      const wait=()=>new Promise(r=>setTimeout(r,15));
      const click=s=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes(s)&&!x.disabled);if(!b)return false;b.click();return true};
      let rolls=0,buys=0;
      for(let i=0;i<2200;i++){
        if(document.querySelector('main')?.dataset.gameStatus==='finished')
          return {finished:true,rolls,buys};
        if(click('我已就位')){}
        else if(click('使用奖励卡')){}
        else if(click('使用步数卡')){}
        else if(click('掷骰前进'))rolls++;
        else if(click('购买地产'))buys++;
        else if(click('放弃购买')){}
        else click('结束当前回合');
        await wait();
      }
      return {finished:false,rolls,buys};
    }""")
    assert report['finished'] and report['rolls']>0,report
    assert not errors,errors
    print('PASS: two maps, saved board and real game',map_id,players,report)
    page.close()

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
            url=f'http://127.0.0.1:{server.server_port}/ReactMono/'
            for map_id,size in [('classic-24',24),('harbor-20',20)]:
                for players in (2,4):exercise(browser,url,map_id,size,players)
            browser.close()
    finally:
        server.shutdown();thread.join()

if __name__=='__main__':main()
