// Service Worker para Taller Mecánica PWA
// Versión del cache - incrementar para forzar actualización
const CACHE_NAME = 'taller-mecanica-v1.0.0';
const STATIC_CACHE = 'taller-static-v1.0.0';
const DYNAMIC_CACHE = 'taller-dynamic-v1.0.0';

// Recursos para cachear inmediatamente
const STATIC_ASSETS = [
  '/',
  '/static/manifest.json',
  '/whatsapp/',
  '/whatsapp/chatbot/',
  // Bootstrap CSS
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  // Bootstrap JS
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
  // Font Awesome
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css',
  // Bootstrap Icons
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css',
  // HTMX
  'https://unpkg.com/htmx.org@1.9.6'
];

// Recursos que NO deben cachearse (datos dinámicos)
const NEVER_CACHE = [
  '/webhook/',
  '/api/',
  '/admin/',
  'chrome-extension://'
];

// Instalación del Service Worker
self.addEventListener('install', event => {
  console.log('🔧 Service Worker: Instalando...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('📦 Service Worker: Cacheando recursos estáticos');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('✅ Service Worker: Instalación completada');
        return self.skipWaiting(); // Activar inmediatamente
      })
      .catch(error => {
        console.error('❌ Service Worker: Error en instalación:', error);
      })
  );
});

// Activación del Service Worker
self.addEventListener('activate', event => {
  console.log('🚀 Service Worker: Activando...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            // Eliminar caches antiguos
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('🗑️ Service Worker: Eliminando cache antiguo:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('✅ Service Worker: Activación completada');
        return self.clients.claim(); // Controlar todas las páginas inmediatamente
      })
  );
});

// Interceptar requests (estrategia de cache)
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Ignorar requests que no deben cachearse
  if (NEVER_CACHE.some(path => url.pathname.startsWith(path))) {
    return; // Dejar que pase normalmente
  }
  
  // Ignorar chrome-extension y otros protocolos
  if (!url.protocol.startsWith('http')) {
    return;
  }
  
  event.respondWith(
    caches.match(request)
      .then(cachedResponse => {
        // Si está en cache, devolverlo
        if (cachedResponse) {
          console.log('📦 Cache HIT:', request.url);
          return cachedResponse;
        }
        
        // Si no está en cache, hacer fetch
        console.log('🌐 Cache MISS:', request.url);
        return fetch(request)
          .then(response => {
            // Solo cachear respuestas exitosas
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Clonar la respuesta (solo se puede leer una vez)
            const responseToCache = response.clone();
            
            // Cachear dinámicamente
            caches.open(DYNAMIC_CACHE)
              .then(cache => {
                cache.put(request, responseToCache);
                console.log('💾 Cacheado dinámicamente:', request.url);
              });
            
            return response;
          })
          .catch(error => {
            console.error('❌ Fetch error:', error);
            
            // Fallback para páginas HTML cuando no hay conexión
            if (request.headers.get('accept').includes('text/html')) {
              return caches.match('/').then(fallback => {
                return fallback || new Response('Sin conexión', {
                  status: 503,
                  statusText: 'Service Unavailable',
                  headers: new Headers({
                    'Content-Type': 'text/html'
                  })
                });
              });
            }
            
            throw error;
          });
      })
  );
});

// Manejar notificaciones push (para chatbot WhatsApp)
self.addEventListener('push', event => {
  console.log('📱 Push notification recibida');
  
  const options = {
    body: 'Nuevo mensaje en el chatbot de WhatsApp',
    icon: '/static/img/IQAutoEC.png',
    badge: '/static/img/IQAutoEC.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: '1',
      url: '/whatsapp/chatbot/'
    },
    actions: [
      {
        action: 'view-chatbot',
        title: 'Ver Chatbot',
        icon: '/static/img/IQAutoEC.png'
      },
      {
        action: 'dismiss',
        title: 'Cerrar'
      }
    ],
    requireInteraction: true,
    silent: false
  };
  
  if (event.data) {
    const data = event.data.json();
    options.body = data.message || options.body;
    options.data.url = data.url || options.data.url;
  }
  
  event.waitUntil(
    self.registration.showNotification('Taller Mecánica - WhatsApp', options)
  );
});

// Manejar clicks en notificaciones
self.addEventListener('notificationclick', event => {
  console.log('🔔 Notification click:', event.action);
  
  event.notification.close();
  
  if (event.action === 'view-chatbot') {
    event.waitUntil(
      clients.openWindow('/whatsapp/chatbot/')
    );
  } else if (event.action !== 'dismiss') {
    // Click en la notificación (no en botón)
    const url = event.notification.data.url || '/whatsapp/chatbot/';
    event.waitUntil(
      clients.openWindow(url)
    );
  }
});

// Sincronización en background (para envío offline de mensajes)
self.addEventListener('sync', event => {
  console.log('🔄 Background sync:', event.tag);
  
  if (event.tag === 'send-whatsapp-message') {
    event.waitUntil(
      // Aquí podrías implementar lógica para enviar mensajes pendientes
      console.log('📤 Enviando mensajes pendientes de WhatsApp...')
    );
  }
});

// Mensaje de bienvenida
console.log('🎉 Service Worker de Taller Mecánica cargado correctamente');
console.log('📱 PWA lista para funcionar offline');
console.log('🤖 Notificaciones de chatbot WhatsApp habilitadas');
