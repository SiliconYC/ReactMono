import type { InspectionRequest, InspectionTarget } from './map-picking.js';
export const INSPECTION_DELAY=400;
export class InspectionHold {
  private press:({pointerId:number;started:number}&InspectionRequest)|null=null;
  begin(pointerId:number,x:number,y:number,target:InspectionTarget,now:number):void {
    this.press={...target,x,y,pointerId,started:now};
  }
  move(pointerId:number,x:number,y:number):void {
    const p=this.press;
    if(p&&p.pointerId===pointerId&&Math.hypot(x-p.x,y-p.y)>7)this.press=null;
  }
  read(now:number):InspectionRequest|null {
    const p=this.press;if(!p||now-p.started<INSPECTION_DELAY)return null;
    const {pointerId:_pointer,started:_start,...request}=p;return request;
  }
  end():void {this.press=null;}
}
