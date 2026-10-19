import * as THREE from 'three';
import { useEffect, useMemo } from 'react';
export function BankBuilding(): React.JSX.Element {
  const sign = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 256; canvas.height = 80;
    const context = canvas.getContext('2d');
    if (context) {
      context.fillStyle = '#24594f'; context.fillRect(0, 0, 256, 80);
      context.fillStyle = '#ffe39b'; context.font = 'bold 45px "PingFang SC", "Microsoft YaHei", sans-serif';
      context.textAlign = 'center'; context.textBaseline = 'middle'; context.fillText('晴湾银行', 128, 42);
    }
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    return texture;
  }, []);
  useEffect(() => () => sign.dispose(), [sign]);
  return (
    <group name="晴湾银行">
      <mesh position={[0, 0.05, 0]}><cylinderGeometry args={[1.05, 1.12, 0.2, 8]} /><meshStandardMaterial color="#c1d3c4" /></mesh>
      <mesh position={[0, 0.65, -0.05]}><boxGeometry args={[1.24, 1.05, 0.96]} /><meshStandardMaterial color="#fff2ce" /></mesh>
      <mesh position={[0, 1.23, 0]}><boxGeometry args={[1.48, 0.18, 1.15]} /><meshStandardMaterial color="#427f73" /></mesh>
      <mesh position={[0, 0.54, 0.455]}><boxGeometry args={[0.3, 0.72, 0.035]} /><meshStandardMaterial color="#3a7165" /></mesh>
      {[-0.5, 0.5].map(x => <mesh key={x} position={[x, 0.68, 0.55]}><cylinderGeometry args={[0.075, 0.09, 0.92, 8]} /><meshStandardMaterial color="#fff9e9" /></mesh>)}
      <mesh position={[0, 1.12, 0.59]}><planeGeometry args={[1.14, 0.36]} /><meshBasicMaterial map={sign} /></mesh>
      <mesh position={[0, 1.58, 0]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.22, 0.22, 0.08, 16]} /><meshStandardMaterial color="#ffd461" metalness={0.4} roughness={0.3} /></mesh>
    </group>
  );
}

export function ClockTower(): React.JSX.Element {
  return (
    <group>
      <mesh position={[0, 0.14, 0]}>
        <cylinderGeometry args={[2.25, 2.4, 0.28, 12]} />
        <meshStandardMaterial color="#92c89e" roughness={0.9} />
      </mesh>
      <mesh position={[0, 1.18, 0]}>
        <boxGeometry args={[1.15, 2.05, 1.15]} />
        <meshStandardMaterial color="#f6d993" roughness={0.78} />
      </mesh>
      <mesh position={[0, 2.38, 0]} rotation={[0, Math.PI / 4, 0]}>
        <coneGeometry args={[1.02, 0.82, 4]} />
        <meshStandardMaterial color="#d15b4e" roughness={0.72} />
      </mesh>
      {[0, Math.PI / 2, Math.PI, -Math.PI / 2].map(angle => (
        <mesh key={angle} position={[Math.sin(angle) * 0.581, 1.42, Math.cos(angle) * 0.581]} rotation={[0, angle, 0]}>
          <circleGeometry args={[0.27, 16]} />
          <meshStandardMaterial color="#fff9df" roughness={0.5} />
        </mesh>
      ))}
      <mesh position={[0, 2.94, 0]}>
        <sphereGeometry args={[0.13, 8, 6]} />
        <meshStandardMaterial color="#f8c95d" metalness={0.2} roughness={0.45} />
      </mesh>
    </group>
  );
}

