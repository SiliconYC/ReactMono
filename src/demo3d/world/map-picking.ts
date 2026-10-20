import type { Intersection } from 'three';
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
