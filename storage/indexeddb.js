/** 全部保存在玩家自己的浏览器 IndexedDB；无网络传输。 */
import { deserializeGame, serializeGame } from '../core/save.js';
const DB_NAME = 'reactmono-local-saves';
const TABLE = 'slots';
const req = (request) => new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error('本地存储请求失败'));
});
async function database() {
    if (typeof indexedDB === 'undefined')
        throw new Error('此浏览器未提供 IndexedDB，无法使用本地存档');
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, 1);
        request.onupgradeneeded = () => { if (!request.result.objectStoreNames.contains(TABLE))
            request.result.createObjectStore(TABLE, { keyPath: 'id' }); };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error ?? new Error('本地存储无法打开'));
        request.onblocked = () => reject(new Error('其他页面正在占用旧版本存档，请关闭重复页面'));
    });
}
async function useDb(fn) {
    const db = await database();
    try {
        return await fn(db);
    }
    finally {
        db.close();
    }
}
function finished(tx) {
    return new Promise((resolve, reject) => {
        tx.oncomplete = () => resolve();
        tx.onabort = () => reject(tx.error ?? new Error('写入中止，原存档未改动'));
        tx.onerror = () => reject(tx.error ?? new Error('本地存储事务失败'));
    });
}
export async function listSlots() {
    return useDb(async (db) => {
        const rows = await req(db.transaction(TABLE, 'readonly').objectStore(TABLE).getAll());
        return rows.map(({ id, name, kind, updatedAt }) => ({ id, name, kind, updatedAt }))
            .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
    });
}
export async function readSlot(id) {
    return useDb(async (db) => {
        const row = await req(db.transaction(TABLE, 'readonly').objectStore(TABLE).get(id));
        if (!row || typeof row.contents !== 'string')
            throw new Error('没有找到此存档，可能已经被清理');
        return deserializeGame(row.contents);
    });
}
/** readwrite 事务中原子读取旧日期并覆盖；写失败不会半写入。 */
export async function writeSlot(id, name, kind, game) {
    if (!id || id.length > 100 || !name.trim() || name.length > 60 || !['auto', 'manual'].includes(kind))
        throw new Error('存档名称或标识不合法');
    await useDb(async (db) => {
        const tx = db.transaction(TABLE, 'readwrite');
        const done = finished(tx);
        const object = tx.objectStore(TABLE);
        try {
            const previous = await req(object.get(id));
            const now = new Date().toISOString();
            const createdAt = previous ? deserializeGame(previous.contents).createdAt : now;
            const contents = serializeGame(game, { createdAt, now });
            object.put({ id, name, kind, contents, updatedAt: now });
            await done;
        }
        catch (error) {
            try {
                tx.abort();
            }
            catch { /* 已提交或已中止 */ }
            await done.catch(() => undefined);
            throw error;
        }
    });
}
export async function deleteSlot(id) {
    await useDb(async (db) => {
        const tx = db.transaction(TABLE, 'readwrite');
        const done = finished(tx);
        tx.objectStore(TABLE).delete(id);
        await done;
    });
}
