"""真实公网 GitHub Pages 子路径交互，不能以 Actions 发布成功代替访问。"""
import re
from playwright.sync_api import sync_playwright
URL='https://siliconyc.github.io/ReactMono/'
def main():
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox'])
        page=browser.new_page()
        errors=[]
        page.on('pageerror',lambda e: errors.append(str(e)))
        response=page.goto(URL,wait_until='load',timeout=25000)
        assert response is not None and response.status==200,(URL,None if response is None else response.status)
        assert page.locator('.tile').count()==24,page.locator('body').inner_text()[:500]
        assert page.locator('.tile').first.get_attribute('data-tile-id')=='0'
        assert page.evaluate("performance.getEntriesByType('resource').filter(r=>/unpkg|jsdelivr|esm.sh/.test(r.name)).length")==0
        page.get_by_label('对局种子').fill('17')
        page.get_by_label('快速模式').check()
        page.get_by_role('button',name=re.compile('开始游戏')).click()
        report=page.evaluate("""async()=>{
           const click=s=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes(s)&&!x.disabled);if(!b)return false;b.click();return true};
           const pause=()=>new Promise(r=>setTimeout(r,20));
           let rolls=0;
           for(let i=0;i<1500;i++){
             if(document.querySelector('main')?.dataset.gameStatus==='finished')return {finished:true,rolls};
             if(click('使用奖励卡')){}
             else if(click('使用步数卡')){}
             else if(click('升级 地产')){}
             else if(click('掷骰前进'))rolls++;
             else if(click('购买地产')){}
             else if(click('放弃购买')){}
             else click('结束当前回合');
             await pause();
           }
           return {finished:false,rolls};
        }""")
        assert report['finished'] and report['rolls']>0,report
        assert not errors,errors
        print('PASS: 公网 Pages 200 + 24 格 + 完整真人电脑游戏，无 CDN',report)
        browser.close()
if __name__=='__main__':main()
