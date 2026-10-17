"""P3-16 independent real PUBLIC Pages Chromium: finance, file recovery, full game, phone offline.
Never substitute local HTTP results for this public-URL check.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json,re

URL='https://siliconyc.github.io/ReactMono/'
OUT=Path('artifacts/issue45')

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

def run_game(page,max_steps):
    result=page.evaluate("""async maxSteps=>{
       const click=s=>{const b=[...document.querySelectorAll('button')]
         .find(x=>x.textContent.includes(s)&&!x.disabled);if(!b)return false;b.click();return true;};
       let rolls=0,handoffs=0;
       for(let i=0;i<maxSteps;i++){
         if(document.querySelector('main')?.dataset.gameStatus==='finished')return {finished:true,rolls,handoffs};
         if(click('我已就位'))handoffs++;
         else if(click('跳过当前停留回合')){}
         else if(click('离开商店')){}
         else if(click('掷骰前进'))rolls++;
         else if(click('购买地产')){}
         else if(click('放弃购买')){}
         else click('结束当前回合');
         await new Promise(r=>setTimeout(r,20));
       }
       return {finished:false,rolls,handoffs};
    }""",max_steps)
    assert result['finished'],result
    return result

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        errors=[]
        desktop=browser.new_context(viewport={'width':1440,'height':900},accept_downloads=True,service_workers='allow')
        page=desktop.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('dialog',lambda d:d.accept('P3公网资产存档' if d.type=='prompt' else None))
        response=page.goto(URL,wait_until='load',timeout=30000)
        assert response and response.status==200,response
        assert page.locator('.tile').count()==24
        page.get_by_label('对局种子').fill('17')
        page.get_by_label('最多轮数').fill('3')
        page.get_by_label('启用医院、监狱与商店').check()
        page.get_by_label('快速模式').check()
        page.get_by_role('button',name=re.compile('开始游戏')).click()
        assert page.locator('.asset-player').count()==2
        page.get_by_role('button',name=re.compile('掷骰前进')).click()
        if page.locator('main').get_attribute('data-game-phase')=='await_decision':
            page.get_by_role('button',name=re.compile('购买地产')).click()
        assert page.locator('main').get_attribute('data-game-phase')=='await_end_turn'
        cash=wallet(page)[0]
        open_tool(page,'银行')
        page.get_by_label('银行交易金额').fill('100')
        page.get_by_role('button',name='存入银行').click()
        assert wallet(page)[0]==cash-100 and wallet(page)[1]==100
        open_tool(page,'股票')
        page.get_by_label('股票交易数量').fill('1')
        page.get_by_role('button',name='买入 青禾农业').click()
        assert wallet(page)[3]==1,'stock holding was not exposed in player assets'
        open_tool(page,'抵押借贷')
        mortgage=page.locator('#loan-actions').get_by_role('button',name=re.compile('^抵押'))
        if mortgage.count():
            mortgage.first.click()
            page.get_by_label('银行交易金额').fill('20')
            page.get_by_role('button',name='借入贷款').click()
            assert wallet(page)[4]==20,'mortgage/loan should survive on same game'
        before=wallet(page)
        page.screenshot(path=str(OUT/'public-desktop-finance.png'),full_page=True)
        page.get_by_role('button',name='创建手动存档').click()
        row=page.locator('.save-list li').filter(has_text='P3公网资产存档')
        row.wait_for()
        with page.expect_download() as task:row.get_by_role('button',name='导出').click()
        download=task.value
        raw=Path(download.path()).read_bytes()
        assert json.loads(raw)['game']['players'][0]['bankBalance']==100
        row.get_by_role('button',name='删除').click()
        page.wait_for_function("!document.querySelector('.save-list')?.textContent.includes('P3公网资产存档')")
        page.get_by_label('导入 JSON 存档文件').set_input_files({
            'name':download.suggested_filename,'mimeType':'application/json','buffer':raw})
        page.get_by_role('region',name='存档导入预览').wait_for()
        page.get_by_role('button',name='确认导入存档').click()
        row=page.locator('.save-list li').filter(has_text='P3公网资产存档')
        row.wait_for()
        row.get_by_role('button',name='读取').click()
        page.wait_for_function("document.querySelector('.save-message')?.textContent.includes('已读取「P3公网资产存档」')",timeout=10000)
        assert wallet(page)==before,'SILENT ASSET LOSS after JSON export/delete/import/read'
        assert page.locator('main').get_attribute('data-game-phase')=='await_end_turn'
        desktop_result=run_game(page,2400)
        page.screenshot(path=str(OUT/'public-desktop-finished.png'),full_page=True)
        desktop.close()

        mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,
            device_scale_factor=1,service_workers='allow')
        phone=mobile.new_page()
        phone.on('pageerror',lambda e:errors.append(str(e)))
        response=phone.goto(URL,wait_until='load',timeout=30000)
        assert response and response.status==200
        phone.wait_for_function("navigator.serviceWorker.controller!==null",timeout=30000)
        mobile.set_offline(True)
        phone.reload(wait_until='load')
        phone.get_by_label('游戏地图').select_option('harbor-20')
        phone.get_by_label('玩家人数').select_option('4')
        phone.get_by_label('最多轮数').fill('2')
        phone.get_by_label('快速模式').check()
        for i in range(4):phone.get_by_label(f'第 {i+1} 位玩家类型').select_option('human')
        assert phone.locator('main').get_attribute('data-map-id')=='harbor-20'
        assert phone.locator('.tile').count()==20
        assert '已断网' in phone.locator('.network-indicator').inner_text()
        assert phone.evaluate('document.documentElement.scrollWidth<=window.innerWidth+2')
        phone.get_by_role('button',name=re.compile('开始游戏')).click()
        assert phone.locator('.asset-player').count()==4
        assert phone.locator('.asset-player[data-active-player="true"]').count()==1
        phone.screenshot(path=str(OUT/'public-mobile-offline.png'),full_page=True)
        mobile_result=run_game(phone,1200)
        assert mobile_result['handoffs']>=3 and mobile_result['rolls']>=4,mobile_result
        phone.screenshot(path=str(OUT/'public-mobile-finished.png'),full_page=True)
        assert not errors,errors
        print('PASS P3-16 PUBLIC Chromium: desktop cash/bank/stock/loan/save-restore/full game',desktop_result,
              'and offline touchscreen 4-player harbor full game',mobile_result,'screenshots=4')
        browser.close()

if __name__=='__main__':main()
