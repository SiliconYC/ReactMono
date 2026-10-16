/** Pure, versioned map topology and screen coordinates. Every node has one cyclic successor. */
import type { GameMap, MapCell } from './types.js';

const cellsOfRing=(columns:number,rows:number): MapCell[]=>{
  const cells: MapCell[]=[];
  for(let c=1;c<=columns;c++)cells.push({column:c,row:1});
  for(let r=2;r<rows;r++)cells.push({column:columns,row:r});
  for(let c=columns;c>=1;c--)cells.push({column:c,row:rows});
  for(let r=rows-1;r>=2;r--)cells.push({column:1,row:r});
  return cells;
};
/** A map declaration may be shared but its game-state copy is isolated. */
export function makeRingMap(id:string,version:number,columns:number,rows:number):GameMap {
  if(!Number.isInteger(columns)||!Number.isInteger(rows)||columns<3||rows<3)
    throw new Error('地图环形尺寸非法');
  const cells=cellsOfRing(columns,rows);
  return {id,version,columns,rows,cells,route:cells.map((_,i)=>i)};
}
export const DEFAULT_MAP:GameMap=makeRingMap('classic-24',1,8,6);
export const INTERNAL_TEST_MAP:GameMap=makeRingMap('internal-square-16',1,5,5);

/** Supports tiny custom boards in legacy rules tests and old saved 2-tile fixtures. */
export function inferMap(count:number):GameMap {
  if(count===24)return cloneMap(DEFAULT_MAP);
  if(!Number.isInteger(count)||count<2||count>512)throw new Error('地图格数量非法');
  const columns=Math.min(count,8),rows=Math.ceil(count/columns);
  return {id:'custom-'+count,version:1,columns,rows,
    cells:Array.from({length:count},(_,i)=>({column:i%columns+1,row:Math.floor(i/columns)+1})),
    route:Array.from({length:count},(_,i)=>i)};
}
export function cloneMap(map:GameMap):GameMap {
  return {...map,cells:map.cells.map(p=>({...p})),route:[...map.route]};
}
export function advancePosition(map:GameMap,from:number,steps:number):number {
  if(!Number.isSafeInteger(steps)||steps<0)throw new Error('移动步数非法');
  const index=map.route.indexOf(from);
  if(index<0)throw new Error('棋盘不存在当前位置');
  return map.route[(index+(steps%map.route.length))%map.route.length];
}
const record=(x:unknown):x is Record<string,unknown>=>x!==null&&typeof x==='object'&&!Array.isArray(x);
function registered(id:string,length:number):GameMap|null {
  if(id===DEFAULT_MAP.id)return DEFAULT_MAP;
  if(id===INTERNAL_TEST_MAP.id)return INTERNAL_TEST_MAP;
  if(id==='custom-'+length)return inferMap(length);
  return null;
}
/** Reject forged paths, unknown IDs/versions, duplicate/out-of-grid cells and stale geometry. */
export function validateMap(map:unknown,tileCount:number):void {
  const error=()=>new Error('地图标识、版本或路径配置无效');
  // Separate guards allow strict TypeScript to narrow unknown inputs safely.
  if(!record(map))throw error();
  if(Object.keys(map).sort().join(',')!=='cells,columns,id,route,rows,version')throw error();
  if(typeof map.id!=='string'||!Array.isArray(map.cells)||!Array.isArray(map.route)||
    !Number.isInteger(map.version)||!Number.isInteger(map.columns)||!Number.isInteger(map.rows)||
    map.cells.length!==tileCount||map.route.length!==tileCount)throw error();
  const expected=registered(map.id,tileCount);
  if(expected===null)throw error();
  if(map.version!==expected.version||map.columns!==expected.columns||map.rows!==expected.rows||
    tileCount!==expected.cells.length||map.route[0]!==0||
    new Set(map.route).size!==tileCount||
    !map.route.every((id:unknown,i:number)=>Number.isInteger(id)&&id===expected.route[i]))throw error();
  const cells:unknown[]=map.cells;
  if(cells.some((c,i)=>!record(c)||Object.keys(c).sort().join(',')!=='column,row'||
    !Number.isInteger(c.column)||!Number.isInteger(c.row)||
    c.column!==expected.cells[i].column||c.row!==expected.cells[i].row))throw error();
}
