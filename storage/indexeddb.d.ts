/** 全部保存在玩家自己的浏览器 IndexedDB；无网络传输。 */
import { type SaveEnvelope } from '../core/save.js';
import type { GameState } from '../core/game.js';
export type SlotKind = 'auto' | 'manual';
export interface SlotSummary {
    readonly id: string;
    readonly name: string;
    readonly kind: SlotKind;
    readonly updatedAt: string;
}
export declare function listSlots(): Promise<readonly SlotSummary[]>;
export declare function readSlot(id: string): Promise<SaveEnvelope>;
/** readwrite 事务中原子读取旧日期并覆盖；写失败不会半写入。 */
export declare function writeSlot(id: string, name: string, kind: SlotKind, game: GameState): Promise<void>;
export declare function deleteSlot(id: string): Promise<void>;
