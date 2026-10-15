import { cp, mkdir, writeFile } from 'node:fs/promises';
await mkdir('dist', { recursive: true });
await cp('site/index.html', 'dist/index.html');
await cp('site/style.css', 'dist/style.css');
await writeFile('dist/.nojekyll', '');
console.log('静态页面构建完成：dist/');
