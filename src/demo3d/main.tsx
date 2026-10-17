import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { DemoApp } from './DemoApp.js';

const root = document.getElementById('root');
if (root === null) throw new Error('3D 演示缺少根节点');

createRoot(root).render(
  <StrictMode>
    <DemoApp />
  </StrictMode>
);

