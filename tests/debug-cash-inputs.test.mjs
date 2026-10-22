import test from 'node:test';
import assert from 'node:assert/strict';
import { syncDebugCashInputs } from '../.test-dist/ui/debug-cash-inputs.js';

test('设置一位玩家现金后，其他玩家尚未提交的现金草稿保留', () => {
  const previous = [{ id: 'p1', cash: 1500 }, { id: 'p2', cash: 1500 }];
  const next = [{ id: 'p1', cash: 8000 }, { id: 'p2', cash: 1500 }];
  assert.deepEqual(syncDebugCashInputs({ p1: '8000', p2: '9999' }, previous, next), { p1: '8000', p2: '9999' });
});

test('模拟确实改变的现金用最新值更新，未变的玩家保留原输入', () => {
  const previous = [{ id: 'p1', cash: 1500 }, { id: 'p2', cash: 1500 }];
  const next = [{ id: 'p1', cash: 1250 }, { id: 'p2', cash: 1500 }];
  assert.deepEqual(syncDebugCashInputs({ p1: '8000', p2: '未输入完' }, previous, next), { p1: '1250', p2: '未输入完' });
});

test('首次打开和玩家名单改变时建立有效输入，不遗留已移除玩家', () => {
  assert.deepEqual(syncDebugCashInputs({}, null, [{ id: 'p1', cash: 0 }]), { p1: '0' });
  assert.deepEqual(syncDebugCashInputs({ p1: '300', p2: '400' }, [{ id: 'p1', cash: 100 }], [{ id: 'p3', cash: 500 }]), { p3: '500' });
});
