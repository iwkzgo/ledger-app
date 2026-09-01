// 오프라인 캐싱은 하지 않는 최소 서비스 워커입니다.
// Android Chrome이 "홈 화면에 추가"를 정식 앱 설치로 인식해서
// 주소창 없이(standalone) 실행되도록 하는 최소 요건만 채웁니다.

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  event.respondWith(fetch(event.request));
});
