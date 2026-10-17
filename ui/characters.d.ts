/** P4 #65: 4 original paper-art characters. Identity is the persisted seat index, never AI/human status. */
export declare const CHARACTER_NAMES: readonly ["纸狐", "圆熊", "长耳兔", "帆鸟"];
export declare const CHARACTER_FILES: readonly ["fox", "bear", "rabbit", "bird"];
export type CharacterMode = 'human' | 'computer';
export type CharacterDisplay = 'pawn' | 'portrait' | 'badge' | 'setup' | 'winner';
/** Character assets have no network dependencies and are precached by the service worker. */
export declare function characterMarker(seat: number, kind: CharacterMode, display: CharacterDisplay, active?: boolean, moving?: boolean): unknown;
