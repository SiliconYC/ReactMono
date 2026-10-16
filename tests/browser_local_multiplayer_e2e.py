"""P3-03: real Chromium interactions for local 2–4 player setup and pass-the-device."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import os
import re
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        route=path.split('?',1)[0]
        if not route.startswith('/ReactMono/'):return str(ROOT/'dist'/'not-found')
        return str(ROOT/'dist'/route.removeprefix('/ReactMono/'))
    def log_message(self,*args):pass

def scenario(browser,url,n,computer_positions):
    page=browser.new_page(viewport={'width':390,'height':844})
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(url,wait_until='load')
    page.get_by_label('玩家人数').select_option(str(n))
    for i in range(n):
        page.get_by_label(f'第 {i+1} 位玩家姓名').fill(f'测试者{i+1}')
        page.get_by_label(f'第 {i+1} 位玩家类型').select_option('computer' if i in computer_positions else 'human')
    page.get_by_label('最多轮数').fill('2')
    page.get_by_label('快速模式').check()
    page.get_by_label('对局种子').fill('17')
    page.get_by_role('button',name=re.compile('开始游戏')).click()
    assert page.locator('.player-line').count()==n, page.locator('body').inner_text()
    report=page.evaluate("""async()=>{
      const pause=()=>new Promise(r=>setTimeout(r,15));
      const click=s=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes(s)&&!x.disabled);if(!b)return false;b.click();return true};
      let handoffs=0,rolls=0;
      for(let i=0;i<2000;i++){
        if(document.querySelector('main[data-game-status]')?.dataset.gameStatus==='finished')
          return {finished:true,handoffs,rolls};
        if(click('我已就位，开始操作'))handoffs++;
        else if(click('使用奖励卡')){}
        else if(click('使用步数卡')){}
        else if(click('掷骰前进'))rolls++;
        else if(click('购买地产')){}
        else if(click('放弃购买')){}
        else click('结束当前回合');
        await pause();
      }
      return {finished:false,handoffs,rolls};
    }""")
    assert report['finished'] and report['rolls']>0,report
    if len(computer_positions)==0:assert report['handoffs']>0,report
    assert not errors,errors
    print('PASS: local multiplayer UI',{'players':n,'computers':list(computer_positions),**report})
    page.close()

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p:
            args={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
            if os.environ.get('CHROMIUM_PATH'):args['executable_path']=os.environ['CHROMIUM_PATH']
            else:args['channel']='chrome'
            browser=p.chromium.launch(**args)
            url=f'http://127.0.0.1:{server.server_port}/ReactMono/'
            scenario(browser,url,2,set())
            scenario(browser,url,4,{1,2,3})
            scenario(browser,url,4,set())
            browser.close()
    finally:
        server.shutdown();thread.join()

if __name__=='__main__':main()
