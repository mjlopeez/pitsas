const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');

let PORT = parseInt(process.env.PORT, 10) || 3001;
const NGROK_HOST = 'ebook-shun-moonwalk.ngrok-free.dev';

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

function proxyToBackend(req, res, targetPath) {
  const options = {
    hostname: NGROK_HOST,
    port: 443,
    path: targetPath,
    method: req.method,
    headers: {
      ...req.headers,
      host: NGROK_HOST,
      'ngrok-skip-browser-warning': 'true'
    }
  };

  const proxyReq = https.request(options, (proxyRes) => {
    const responseHeaders = {
      ...proxyRes.headers,
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'GET, POST, OPTIONS, PUT, DELETE',
      'access-control-allow-headers': 'Content-Type, ngrok-skip-browser-warning, Authorization, x-hub-token'
    };
    res.writeHead(proxyRes.statusCode, responseHeaders);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    console.error(`[PROXY ERROR] ${req.method} ${targetPath}:`, err.message);
    res.writeHead(502, { 
      'Content-Type': 'application/json; charset=utf-8',
      'Access-Control-Allow-Origin': '*'
    });
    res.end(JSON.stringify({ error: 'Backend unreachable via proxy', detail: err.message }));
  });

  req.pipe(proxyReq);
}

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, ngrok-skip-browser-warning, Authorization, x-hub-token');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  let pathname = parsedUrl.pathname;
  const search = parsedUrl.search || '';

  // Reverse Proxy transparente para endpoints de Backend API
  const isApiRoute = pathname.startsWith('/api/') || 
                     pathname === '/health' || 
                     pathname.startsWith('/health/') || 
                     pathname.startsWith('/ingest/') || 
                     pathname.startsWith('/webhooks/') || 
                     pathname.startsWith('/admin/');

  if (isApiRoute) {
    proxyToBackend(req, res, pathname + search);
    return;
  }

  if (pathname === '/') {
    pathname = '/index.html';
  }

  const filePath = path.join(__dirname, pathname);

  fs.stat(filePath, (err, stats) => {
    if (!err && stats.isFile()) {
      const ext = path.extname(filePath).toLowerCase();
      const contentType = MIME_TYPES[ext] || 'application/octet-stream';
      res.writeHead(200, { 'Content-Type': contentType });
      fs.createReadStream(filePath).pipe(res);
    } else {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end(`404 No encontrado: ${pathname}`);
    }
  });
});

function startServer(portToTry) {
  server.listen(portToTry, '0.0.0.0', () => {
    console.log(`====================================================`);
    console.log(` HUB DE OPERACIONES — GRUPO ECON`);
    console.log(` Frontend corriendo en: http://localhost:${portToTry}`);
    console.log(` Disponible en red local para celulares: http://<tu-ip>:${portToTry}`);
    console.log(` Reverse Proxy activo hacia: https://${NGROK_HOST}`);
    console.log(`====================================================`);
  });
}

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.warn(`Puerto ${PORT} en uso, probando puerto ${PORT + 1}...`);
    PORT++;
    startServer(PORT);
  } else {
    console.error('Error en servidor:', err);
  }
});

startServer(PORT);
