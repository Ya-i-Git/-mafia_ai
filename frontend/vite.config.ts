import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000'
  const wsTarget = process.env.VITE_WS_PROXY_TARGET || 'ws://localhost:8000'

  console.log(`[Vite] API proxy target: ${apiTarget}`)
  console.log(`[Vite] WS proxy target: ${wsTarget}`)

  return {
    plugins: [react()],
    server: {
      port: 3000,
      host: true,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('proxy error', err);
            });
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              console.log(`[Proxy] ${req.method} ${req.url} -> ${proxyReq.protocol}//${proxyReq.host}${proxyReq.path}`);
            });
          }
        },
        '/ws': {
          target: wsTarget,
          ws: true,
          changeOrigin: true,
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('ws proxy error', err);
            });
            proxy.on('proxyReqWs', (proxyReq, req, socket, options, head) => {
              console.log(`[WS Proxy] ${req.url} -> ${wsTarget}`);
            });
          }
        }
      }
    }
  }
})