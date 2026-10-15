import { cp, mkdir, stat, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

// tsc 先输出 dist/core、dist/ui；此处仅收集同源静态资源。
// 构建必须从已安装的锁文件依赖读取，严禁运行时加载第三方 CDN。
await mkdir('dist/vendor', { recursive: true });
await cp('site/index.html', 'dist/index.html');
await cp('site/style.css', 'dist/style.css');
for (const [packageName, filename] of [
  ['react', 'react.production.min.js'],
  ['react-dom', 'react-dom.production.min.js']
]) {
  const source = join('node_modules', packageName, 'umd', filename);
  const info = await stat(source);
  if (info.size < 10000) throw new Error('React 本地运行时文件异常：' + source);
  await cp(source, join('dist/vendor', filename));
}
await writeFile('dist/.nojekyll', '');
console.log('静态构建成功：dist/（React 18.3.1 同源文件；无运行时 CDN）');
