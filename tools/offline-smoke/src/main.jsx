import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import * as THREE from 'three';

function App() {
  const canvasRef = useRef(null);
  const [clicks, setClicks] = useState(0);
  useEffect(() => {
    const renderer = new THREE.WebGLRenderer({ canvas: canvasRef.current, antialias: true });
    renderer.setSize(360, 240, false);
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#17263d');
    const camera = new THREE.PerspectiveCamera(60, 1.5, 0.1, 100);
    camera.position.z = 3.2;
    const cube = new THREE.Mesh(
      new THREE.BoxGeometry(1.4, 1.4, 1.4),
      new THREE.MeshNormalMaterial()
    );
    scene.add(cube);
    let animation;
    function frame() {
      cube.rotation.x += 0.008;
      cube.rotation.y += 0.012;
      renderer.render(scene, camera);
      animation = requestAnimationFrame(frame);
    }
    frame();
    window.__offlineThreeReady = true;
    window.__offlineThreeVersion = THREE.REVISION;
    return () => {
      cancelAnimationFrame(animation);
      cube.geometry.dispose();
      cube.material.dispose();
      renderer.dispose();
    };
  }, []);
  return <main>
    <h1 id="status">React + Three.js 离线运行成功</h1>
    <button id="counter" onClick={() => setClicks(n => n + 1)}>点击 {clicks}</button>
    <p>3D 旋转立方体：</p>
    <canvas id="scene" ref={canvasRef} width="360" height="240" />
  </main>;
}
createRoot(document.getElementById('root')).render(<App />);
