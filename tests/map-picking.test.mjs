import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { tileIdForHit } from '../.test-dist/demo3d/world/map-picking.js';

test('右键命中详细屋顶时沿父组识别所属地产，不穿透选择后方道路',()=>{
  const house=new THREE.Group();house.userData.tileId=17;
  const roof=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshBasicMaterial());house.add(roof);
  assert.equal(tileIdForHit({object:roof}),17);
  roof.geometry.dispose();roof.material.dispose();
});
test('简化房屋实例使用显式地产编号，不把筛选后的实例下标当作格号',()=>{
  const group=new THREE.Object3D();group.userData.tileIds=[8,29,106];
  assert.equal(tileIdForHit({object:group,instanceId:1}),29);
  group.userData.mapTiles=true;
  assert.equal(tileIdForHit({object:group,instanceId:1}),29);
  delete group.userData.tileIds;
  assert.equal(tileIdForHit({object:group,instanceId:1}),1);
  assert.equal(tileIdForHit({object:new THREE.Object3D()}),null);
});
