import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
test('#66 action-first UI remains self-contained with PWA offline CSS',async()=>{
  const [html,css,sw,app]=await Promise.all([
    'dist/index.html','dist/action-layout.css','dist/sw.js','dist/ui/app.js'
  ].map(x=>readFile(x,'utf8')));
  assert.ok(html.includes('href="./action-layout.css"'));
  assert.ok(sw.includes('./action-layout.css'));
  assert.doesNotMatch(sw,/__CACHE_VERSION__|__RUNTIME_ASSETS__/);
  assert.match(css,/finance-pane\[hidden\]\{display:none!important\}/);
  assert.match(css,/finance-tabs button\[aria-expanded=true\]/);
  assert.match(css,/asset-quick-roster/);
  assert.match(css,/max-width:1060px/);
  assert.match(app,/financePanel/);
  assert.match(app,/lastCommittedAction/);
  assert.match(app,/确认抵押地产/);
  assert.match(app,/characterMarker/);
  assert.doesNotMatch(css,/https?:\/\//);
});
