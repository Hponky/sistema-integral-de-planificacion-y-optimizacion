import { APP_BASE_HREF } from '@angular/common';
import { CommonEngine } from '@angular/ssr';
import express from 'express';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import { createProxyMiddleware } from 'http-proxy-middleware';
import bootstrap from './src/main.server';

interface LogEntry {
  timestamp: string;
  method: string;
  url: string;
  status?: number;
  error?: string;
  duration?: number;
}

class StructuredLogger {
  private logs: LogEntry[] = [];
  
  log(entry: LogEntry): void {
    this.logs.push(entry);
    console.log(JSON.stringify(entry));
  }
  
  getLogs(): LogEntry[] {
    return [...this.logs];
  }
  
  clearLogs(): void {
    this.logs = [];
  }
}

const logger = new StructuredLogger();

// The Express app is exported so that it can be used by serverless Functions.
export function app(): express.Express {
  const server = express();
  const serverDistFolder = dirname(fileURLToPath(import.meta.url));
  const browserDistFolder = resolve(serverDistFolder, '../browser');
  const indexHtml = join(serverDistFolder, 'index.server.html');

  const commonEngine = new CommonEngine();

  server.set('view engine', 'html');
  server.set('views', browserDistFolder);

  // Serve static files from /browser with proper headers
  server.get('*.*', express.static(browserDistFolder, {
    maxAge: '1y',
    setHeaders: (res, path) => {
      // Ensure proper content type for JavaScript files
      if (path.endsWith('.js')) {
        res.setHeader('Content-Type', 'application/javascript');
      }
      // Add security headers
      res.setHeader('X-Content-Type-Options', 'nosniff');
      res.setHeader('X-Frame-Options', 'DENY');
      res.setHeader('X-XSS-Protection', '1; mode=block');
    }
  }));

  // API routes - proxy to backend
  server.use('/api', createProxyMiddleware({
    target: 'http://localhost:5000',
    changeOrigin: true,
    secure: false
  }));

  // All regular routes use the Angular engine
  server.get('*', (req, res, next) => {
    const startTime = Date.now();
    const { protocol, originalUrl, baseUrl, headers } = req;
    
    // Skip SSR for API routes to prevent JSON parsing errors
    if (originalUrl.startsWith('/api/')) {
      return next();
    }

    const logEntry: LogEntry = {
      timestamp: new Date().toISOString(),
      method: req.method,
      url: originalUrl
    };

    commonEngine
      .render({
        bootstrap,
        documentFilePath: indexHtml,
        url: `${protocol}://${headers.host}${originalUrl}`,
        publicPath: browserDistFolder,
        providers: [{ provide: APP_BASE_HREF, useValue: baseUrl }],
      })
      .then((html) => {
        logEntry.status = 200;
        logEntry.duration = Date.now() - startTime;
        logger.log(logEntry);
        res.send(html);
      })
      .catch((err) => {
        logEntry.status = 500;
        logEntry.error = err.message;
        logEntry.duration = Date.now() - startTime;
        logger.log(logEntry);
        
        console.error('SSR Error:', err);
        
        // Fallback to client-side rendering if SSR fails
        res.sendFile(join(browserDistFolder, 'index.html'));
      });
  });

  // Error handling middleware
  server.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
    const logEntry: LogEntry = {
      timestamp: new Date().toISOString(),
      method: req.method,
      url: req.url,
      status: 500,
      error: err.message
    };
    
    logger.log(logEntry);
    
    console.error('Server Error:', err);
    
    // Fallback to client-side rendering
    res.sendFile(join(browserDistFolder, 'index.html'));
  });

  return server;
}

function run(): void {
  const port = process.env['PORT'] || 4000;

  // Start up the Node server
  const httpServer = app();
  const server = httpServer.listen(port, () => {
    console.log(`Node Express server listening on http://localhost:${port}`);
    console.log(`Environment: ${process.env['NODE_ENV'] || 'development'}`);
  });

  // Graceful shutdown
  process.on('SIGTERM', () => {
    console.log('SIGTERM received, shutting down gracefully');
    server.close(() => {
      console.log('Process terminated');
    });
  });

  process.on('SIGINT', () => {
    console.log('SIGINT received, shutting down gracefully');
    server.close(() => {
      console.log('Process terminated');
    });
  });
}

run();
