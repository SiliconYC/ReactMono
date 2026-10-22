import type { Intersection } from 'three';
export type InspectionTarget={kind:'tile';tileId:number}|{kind:'player';playerId:string};
export type InspectionRequest=InspectionTarget&{x:number;y:number};
export function inspectionForHit(hit:Pick<Intersection,'object'|'instanceId'>):InspectionTarget|null{
  let object:typeof hit.object|null=hit.object;
  while(object){if(typeof object.userData.playerId==='string')return {kind:'player',playerId:object.userData.playerId};object=object.parent;}
  const tileId=tileIdForHit(hit);
  return tileId===null?null:{kind:'tile',tileId};
}
export function tileIdForHit(hit:Pick<Intersection,'object'|'instanceId'>):number|null{
  const data=hit.object.userData;
  if(hit.instanceId!==undefined){
    const id=data.tileIds?.[hit.instanceId];
    if(Number.isInteger(id)&&id>=0)return id;
    if(data.mapTiles)return hit.instanceId;
  }
  // 房屋屋顶通常挡住自己的地基；必须保留归属，不能穿透到后方再猜地块。
  let object=hit.object as typeof hit.object|null;
  while(object){if(Number.isInteger(object.userData.tileId)&&object.userData.tileId>=0)return object.userData.tileId;object=object.parent;}
  return null;
}
