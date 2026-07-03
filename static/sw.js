// ============================================================
// sw.js — Service Worker (PWA) do Cronograma FORAVE
// ============================================================
// O service worker é um pequeno script que o browser corre em
// segundo plano. É o que torna a página "instalável" como app e
// permite algum funcionamento offline (guardando ficheiros em cache).
//
// REGRA DE PRIVACIDADE/RGPD: NUNCA guardamos em cache as páginas
// nem os dados pessoais (área do aluno /aluno, /api, login, /admin...).
// Essas vão sempre buscar à rede. Só guardamos a "casca" pública e os
// ficheiros estáticos (ícones, manifest, página pública do cronograma).
//
// ESTRATÉGIA DE CACHE (revista 01/Jul/2026):
//   - HTML (a página pública "/"): NETWORK-FIRST — online mostra sempre
//     a versão fresca; offline cai na cópia guardada. Antes era
//     cache-first, o que servia HTML antigo após cada deploy (o botão
//     "Área do coordenador" não aparecia até limpar a cache). Corrigido.
//   - CSS/JS (forave.css, calendario.js, forave.js): NETWORK-FIRST — mudam a
//     cada deploy, por isso online mostra-se SEMPRE a versão fresca (e a cópia
//     offline actualiza-se); offline cai na última guardada. Antes eram
//     cache-first, o que servia CSS/JS antigo após um deploy (ex.: a grelha do
//     calendário não aparecia até limpar a cache). Corrigido.
//   - Imagens/manifest (ícones, manifest): CACHE-FIRST — raramente mudam, ficam
//     rápidos e disponíveis offline.
//   - Versão da cache: ao activar, o worker apaga as versões anteriores,
//     purgando os estáticos antigos.
//
// Bloco 4 / Fase D (wow factors — PWA)
// ============================================================

const CACHE = 'cronograma-forave-v4';

// Ficheiros da "casca" a guardar logo na instalação. O "/" fica como
// FALLBACK OFFLINE (a estratégia em uso é network-first — ver fetch).
const ASSETS = [
  '/',
  '/static/icon-192.png',
  '/static/icon-512.png',
  '/static/manifest.json'
];

// Instalação: pré-carregar a casca
self.addEventListener('install', (evento) => {
  evento.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

// Activação: limpar caches antigas (versões anteriores)
self.addEventListener('activate', (evento) => {
  evento.waitUntil(
    caches.keys().then((nomes) =>
      Promise.all(
        nomes.filter((nome) => nome !== CACHE).map((nome) => caches.delete(nome))
      )
    )
  );
  self.clients.claim();
});

// Intercepção de pedidos
self.addEventListener('fetch', (evento) => {
  const req = evento.request;
  const url = new URL(req.url);

  // Só tratamos GET do próprio site; o resto segue normal.
  if (req.method !== 'GET' || url.origin !== self.location.origin) {
    return;
  }

  // Páginas/dados dinâmicos e PESSOAIS: nunca cache, sempre rede.
  // (Inclui /admin — tem todas as notas — e as páginas de reposição.)
  if (
    url.pathname.startsWith('/cronograma') ||
    url.pathname.startsWith('/aluno') ||
    url.pathname.startsWith('/api') ||
    url.pathname.startsWith('/login') ||
    url.pathname.startsWith('/logout') ||
    url.pathname.startsWith('/registar') ||
    url.pathname.startsWith('/admin') ||
    url.pathname.startsWith('/recuperar') ||
    url.pathname.startsWith('/repor')
  ) {
    return; // deixa o browser ir à rede normalmente
  }

  // HTML / navegações (ex: a página pública "/"): NETWORK-FIRST.
  // Online → versão fresca (e actualiza a cópia offline);
  // offline → devolve a última cópia guardada (ou o "/").
  if (req.mode === 'navigate' || url.pathname === '/') {
    evento.respondWith(
      fetch(req)
        .then((resposta) => {
          if (resposta.ok) {
            const copia = resposta.clone();
            caches.open(CACHE).then((cache) => cache.put(req, copia));
          }
          return resposta;
        })
        .catch(() => caches.match(req).then((c) => c || caches.match('/')))
    );
    return;
  }

  // CSS/JS mudam a cada deploy -> NETWORK-FIRST: online devolve sempre a versão
  // fresca (e actualiza a cópia); offline cai na última guardada.
  if (url.pathname.endsWith('.css') || url.pathname.endsWith('.js')) {
    evento.respondWith(
      fetch(req)
        .then((resposta) => {
          if (resposta.ok) {
            const copia = resposta.clone();
            caches.open(CACHE).then((cache) => cache.put(req, copia));
          }
          return resposta;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // Restantes estáticos (ícones, manifest, ...): CACHE-FIRST, fallback à rede.
  evento.respondWith(
    caches.match(req).then((emCache) => {
      if (emCache) {
        return emCache;
      }
      return fetch(req).then((resposta) => {
        if (resposta.ok) {
          const copia = resposta.clone();
          caches.open(CACHE).then((cache) => cache.put(req, copia));
        }
        return resposta;
      });
    })
  );
});
