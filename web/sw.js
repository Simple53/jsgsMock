const CACHE_NAME = 'jsgsMock-v29';
const ASSETS = [
  './',
  './index.html',
  './quiz_data_official_2026.json',
  './quiz_data_official_2026.js',
  './quiz_data.json',
  './quiz_data.js',
  './course_videos.js',
  './manifest.json',
  './icon.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// HTML 页面采用网络优先 (Network-First)，断网时回退离线缓存；静态资源缓存优先
self.addEventListener('fetch', (event) => {
  const url = event.request.url;

  // 视频体积较大，交给浏览器原生流式播放，不进入 PWA 离线缓存。
  if (event.request.destination === 'video' || /\.mp4(?:\?|$)/i.test(url)) return;

  // 外部 AI API 及后端同步接口 /api/ 请求直接穿透
  if (url.includes('/api/') || url.includes('/chat/completions') || url.includes('/models') || url.includes('openrouter.ai')) {
    return;
  }

  // HTML 页面请求：网络优先
  if (event.request.mode === 'navigate' || url.endsWith('.html') || url.endsWith('/')) {
    event.respondWith(
      fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(() => {
        return caches.match(event.request).then(cached => cached || caches.match('./index.html'));
      })
    );
    return;
  }

  // 其他静态资源（JSON、图标）：缓存优先 + 后台更新
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, networkResponse);
            });
          }
        }).catch(() => {});
        return cachedResponse;
      }
      return fetch(event.request);
    })
  );
});
