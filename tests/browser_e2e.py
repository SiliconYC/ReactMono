"""P1 浏览器端到端：通过真实 DOM 按钮完成整局，不修改游戏内部状态。
无网络沙盒可用本地 UMD React 替代 CDN 脚本（默认是环境预装 React 16）。
注意：此测试不等于在公网 GitHub Pages 上加载 React 18 的验证。
"""
from pathlib import Path
import os
import re
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REACT = Path(os.environ.get('REACT_UMD_PATH',
    '/opt/pyvenv/lib/python3.13/site-packages/nbclassic/static/components/react/react.production.min.js'))
REACT_DOM = Path(os.environ.get('REACT_DOM_UMD_PATH',
    '/opt/pyvenv/lib/python3.13/site-packages/nbclassic/static/components/react/react-dom.production.min.js'))

def main():
    if not REACT.is_file() or not REACT_DOM.is_file():
        raise RuntimeError('请用 REACT_UMD_PATH、REACT_DOM_UMD_PATH 指定本地 React UMD 文件')
    html = (ROOT/'dist/index.html').read_text(encoding='utf-8')
    html = re.sub(r'<script\b[^>]*>.*?</script>', '', html, flags=re.S|re.I)
    files = [(ROOT/f'dist/{path}').read_text(encoding='utf-8')
             for path in ('core/game.js','core/agent.js','ui/app.js')]
    compiled = '\n'.join(
        re.sub(r'^import .+?;\s*$', '',
            re.sub(r'\bexport\s+(?=(?:const|function|class)\b)', '', code), flags=re.M)
        for code in files)
    seed = os.environ.get('REACTMONO_E2E_SEED', '17')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),
                                    args=['--no-sandbox','--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width':1440,'height':900})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.set_content(html)
        page.add_style_tag(content=(ROOT/'dist/style.css').read_text(encoding='utf-8'))
        page.add_script_tag(path=str(REACT))
        page.add_script_tag(path=str(REACT_DOM))
        page.add_script_tag(content=compiled)
        assert page.locator('.tile').count() == 24
        assert page.get_by_role('button', name=re.compile('开始游戏')).count() == 1
        page.get_by_label('对局种子').fill('abc')
        page.get_by_role('button', name=re.compile('开始游戏')).click()
        assert page.locator('main[data-game-status=setup]').count() == 1
        assert '请输入' in page.locator('.turn-tip').inner_text()
        page.get_by_label('对局种子').fill(seed)
        page.get_by_label('快速模式').check()
        page.get_by_role('button', name=re.compile('开始游戏')).click()
        assert page.locator('main[data-game-status=playing]').count() == 1
        report = page.evaluate("""async () => {
          const click = label => {
            const b = [...document.querySelectorAll('button')].find(
              el => el.textContent.includes(label) && !el.disabled);
            if (!b) return false;
            b.click();
            return true;
          };
          const pause = () => new Promise(r => setTimeout(r, 20));
          let rolls=0,buys=0,declines=0,computerTurns=0,rentSeen=false;
          for (let i=0;i<1200;i++) {
            const main=document.querySelector('main[data-game-status]');
            if(main.dataset.gameStatus==='finished')
              return {rolls,buys,declines,computerTurns,rentSeen,finished:true};
            if(click('掷骰前进')) rolls++;
            else if(click('购买地产')) buys++;
            else if(click('放弃购买')) declines++;
            else if(click('结束当前回合')) computerTurns++;
            if(document.querySelector('.activity-card')?.textContent.includes('支付租金'))
              rentSeen=true;
            await pause();
          }
          return {rolls,buys,declines,computerTurns,rentSeen,finished:false};
        }""")
        assert report['finished'] and report['rolls']>0 and report['buys']>0 and report['computerTurns']>0, report
        assert page.locator('main[data-game-status=finished]').count() == 1
        result = page.locator('.result-box').inner_text()
        assert '本局种子：'+seed in result
        assert ('获胜' in result or '平局' in result)
        assert report['rentSeen'] and report['declines']>0, report
        assert not errors, errors
        page.get_by_role('button',name=re.compile('再来一局')).click()
        assert page.locator('main[data-game-status=setup]').count() == 1
        print('PASS: 浏览器从新游戏操作至结束，种子=',seed,'证据=',report)
        browser.close()

if __name__ == '__main__': main()
