import { useEffect, useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

type DiceProps = Readonly<{ value: number | null; nonce: number; reducedMotion: boolean }>;

const PIPS: Readonly<Record<number, readonly [number, number][]>> = {
  1: [[0, 0]],
  2: [[-0.2, 0.2], [0.2, -0.2]],
  3: [[-0.22, 0.22], [0, 0], [0.22, -0.22]],
  4: [[-0.2, -0.2], [-0.2, 0.2], [0.2, -0.2], [0.2, 0.2]],
  5: [[-0.22, -0.22], [-0.22, 0.22], [0, 0], [0.22, -0.22], [0.22, 0.22]],
  6: [[-0.2, -0.24], [-0.2, 0], [-0.2, 0.24], [0.2, -0.24], [0.2, 0], [0.2, 0.24]]
};

const FACE_TRANSFORMS: readonly Readonly<{
  value: number;
  position: [number, number, number];
  rotation: [number, number, number];
}>[] = [
  { value: 1, position: [0, 0.511, 0], rotation: [-Math.PI / 2, 0, 0] },
  { value: 6, position: [0, -0.511, 0], rotation: [Math.PI / 2, 0, 0] },
  { value: 2, position: [0, 0, 0.511], rotation: [0, 0, 0] },
  { value: 5, position: [0, 0, -0.511], rotation: [0, Math.PI, 0] },
  { value: 3, position: [0.511, 0, 0], rotation: [0, Math.PI / 2, 0] },
  { value: 4, position: [-0.511, 0, 0], rotation: [0, -Math.PI / 2, 0] }
];

function targetRotation(value: number): THREE.Euler {
  switch (value) {
    case 2: return new THREE.Euler(-Math.PI / 2, 0, 0);
    case 3: return new THREE.Euler(0, 0, Math.PI / 2);
    case 4: return new THREE.Euler(0, 0, -Math.PI / 2);
    case 5: return new THREE.Euler(Math.PI / 2, 0, 0);
    case 6: return new THREE.Euler(Math.PI, 0, 0);
    default: return new THREE.Euler(0, 0, 0);
  }
}

export function Dice({ value, nonce, reducedMotion }: DiceProps): React.JSX.Element | null {
  const root = useRef<THREE.Group>(null);
  const startedAt = useRef(0);
  const settling = useRef(false);
  const target = useMemo(() => new THREE.Quaternion(), []);
  const from = useMemo(() => new THREE.Quaternion(), []);

  useEffect(() => {
    startedAt.current = performance.now() / 1000;
    settling.current = false;
    if (value !== null) target.setFromEuler(targetRotation(value));
  }, [from, nonce, target, value]);

  useFrame(() => {
    if (root.current === null || value === null) return;
    const elapsed = performance.now() / 1000 - startedAt.current;
    if (reducedMotion) {
      root.current.quaternion.copy(target);
      root.current.position.y = 2.25;
      return;
    }
    if (elapsed < 0.62) {
      root.current.rotation.set(elapsed * 10.5, elapsed * 13.2, elapsed * 8.4);
      root.current.position.y = 2.25 + Math.sin(Math.min(1, elapsed / 0.62) * Math.PI) * 1.15;
    } else {
      if (!settling.current) {
        from.copy(root.current.quaternion);
        settling.current = true;
      }
      const settle = THREE.MathUtils.smoothstep(elapsed, 0.62, 0.98);
      root.current.quaternion.slerpQuaternions(from, target, settle);
      root.current.position.y = 2.25 + Math.abs(Math.sin((elapsed - 0.62) * 12)) * Math.max(0, 0.25 - (elapsed - 0.62) * 0.32);
    }
  });

  if (value === null) return null;
  return (
    <group ref={root} position={[0, 2.25, 0]} scale={0.56}>
      <mesh>
        <boxGeometry args={[1, 1, 1, 3, 3, 3]} />
        <meshStandardMaterial color="#fffaf0" roughness={0.32} metalness={0.02} />
      </mesh>
      {FACE_TRANSFORMS.map(face => (
        <group key={face.value} position={face.position} rotation={face.rotation}>
          {PIPS[face.value].map(([x, y], index) => (
            <mesh key={index} position={[x, y, 0]}>
              <circleGeometry args={[0.065, 12]} />
              <meshBasicMaterial color="#173a36" />
            </mesh>
          ))}
        </group>
      ))}
    </group>
  );
}

