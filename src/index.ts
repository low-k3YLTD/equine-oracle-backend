import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import { authMiddleware } from './middleware/authMiddleware';
import { getMlPredictions } from './services/mlPredictionService';

const app = express();
const PORT = Number(process.env.PORT) || 8080;

// Environment validation
const ALLOWED_ORIGINS = (process.env.CORS_ORIGIN || 'http://localhost:3000')
  .split(',')
  .map(origin => origin.trim());

console.log('🔐 Allowed CORS origins:', ALLOWED_ORIGINS);

// Oracle Engine Orchestrator
import { oracleEngineOrchestrator } from './src/agents/oracleEngineOrchestrator';

// Start the continuous prediction system
oracleEngineOrchestrator.start().catch((error) => {
  console.error("❌ Failed to start Oracle Engine:", error);
  process.exit(1);
});

// Graceful shutdown
process.on("SIGTERM", () => {
  console.log("🛑 Shutting down Oracle Engine...");
  oracleEngineOrchestrator.stop();
  process.exit(0);
});

// ==================== MIDDLEWARE ====================

// Body parser - BEFORE CORS
app.use(express.json({ limit: '10mb' }));

// CORS Configuration with Proper Preflight Handling
const corsOptions: cors.CorsOptions = {
  origin: (origin, callback) => {
    // Log every CORS request for debugging
    console.log(`📡 CORS Request from origin: ${origin || 'no-origin'}`);
    
    // Allow requests with no origin (mobile apps, curl, Postman)
    if (!origin) {
      console.log('✅ Allowing request with no origin');
      return callback(null, true);
    }

    // Check if origin matches allowed patterns
    const isAllowed = ALLOWED_ORIGINS.some(allowedOrigin => {
      // Exact match
      if (allowedOrigin === origin) return true;
      
      // Wildcard subdomain match (*.vercel.app)
      if (allowedOrigin.startsWith('*.')) {
        const domain = allowedOrigin.slice(1); // Remove *
        return origin.endsWith(domain);
      }
      
      return false;
    });

    if (isAllowed) {
      console.log(`✅ CORS allowed for: ${origin}`);
      callback(null, true);
    } else {
      console.error(`❌ CORS blocked for: ${origin}`);
      callback(new Error(`CORS policy: Origin ${origin} not allowed`));
    }
  },
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: [
    'Content-Type',
    'Authorization',
    'X-Requested-With',
    'Accept',
    'Origin',
  ],
  exposedHeaders: ['Content-Length', 'X-Request-ID'],
  credentials: true,
  maxAge: 86400, // 24 hours - cache preflight
  optionsSuccessStatus: 204, // For legacy browsers
};

// Apply CORS globally
app.use(cors(corsOptions));

// Explicit OPTIONS handler for all routes (preflight)
app.options('*', cors(corsOptions));

// Request logging middleware
app.use((req: Request, res: Response, next: NextFunction) => {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${req.method} ${req.path} - Origin: ${req.get('origin') || 'none'}`);
  next();
});

// ==================== PUBLIC ROUTES ====================

// Health Check
app.get('/health', (req: Request, res: Response) => {
  res.status(200).json({
    status: 'healthy',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    version: '2.0-oracle-engine',
  });
});

// Public: Model Info
app.get('/api/model_info', (req: Request, res: Response) => {
  res.json({
    modelName: 'Equine Oracle Ensemble Predictor',
    version: '2.0-oracle-engine',
    description: 'Ensemble model combining LightGBM Ranker with various classification models (LR, RF, GB, XGB) for horse race win probability prediction.',
    ndcg: 0.9529,
    inputFeatures: [
      'distance',
      'distance_numeric',
      'year',
      'month',
      'day',
      'day_of_week',
      'week_of_year',
      'days_since_last_race',
      'PREV_RACE_WON',
      'WIN_STREAK',
      'IMPLIED_PROBABILITY',
      'NORMALIZED_VOLUME',
      'MARKET_ACTIVITY_WINDOW_HOURS',
    ],
    output: {
      probability: 'Win probability (0.0 to 1.0)',
      confidence: 'Model confidence (0.0 to 1.0)',
    },
  });
});

// Public: Single Prediction Endpoint (MVP - No Auth)
app.post('/api/predict', async (req: Request, res: Response) => {
  const startTime = Date.now();
  const { raceId, horseId, features } = req.body;

  console.log(`🎯 Prediction request: raceId=${raceId}, horseId=${horseId}`);

  // Validation
  if (!features || typeof features !== 'object' || Object.keys(features).length === 0) {
    console.error('❌ Invalid features provided');
    return res.status(400).json({ 
      error: 'Invalid or missing features.',
      received: typeof features,
    });
  }

  try {
    const predictions = await getMlPredictions([features]);

    if (!predictions || predictions.length === 0) {
      console.error('❌ No prediction result from ML service');
      return res.status(500).json({ error: 'No prediction result.' });
    }

    const { probability, confidence } = predictions[0];
    const processingTime = Date.now() - startTime;

    console.log(`✅ Prediction: race ${raceId}, horse ${horseId}, prob ${probability.toFixed(4)}, conf ${confidence.toFixed(4)}, took ${processingTime}ms`);

    res.json({
      raceId,
      horseId,
      probability,
      confidence,
      modelVersion: '2.0-oracle-engine',
      processingTimeMs: processingTime,
    });
  } catch (error: any) {
    console.error('❌ Prediction error:', error.message || error);
    res.status(500).json({ 
      error: 'Failed to generate prediction.',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined,
    });
  }
});

// ==================== AUTHENTICATED ROUTES ====================

// Apply auth middleware ONLY to protected routes
app.use('/api/protected', authMiddleware);

// Placeholder for future authenticated endpoints
app.post('/api/protected/predict_streak', (req: Request, res: Response) => {
  res.status(501).json({
    error: 'Not Implemented',
    message: 'Requires dedicated multi-sequence model.',
  });
});

// ==================== ERROR HANDLERS ====================

// 404 Handler - Must be AFTER all routes
app.use((req: Request, res: Response) => {
  console.warn(`⚠️  404: ${req.method} ${req.path}`);
  res.status(404).json({ 
    error: 'Endpoint not found',
    path: req.path,
    method: req.method,
  });
});

// Global Error Handler - Must be LAST
app.use((err: any, req: Request, res: Response, next: NextFunction) => {
  console.error('💥 Unhandled error:', err.message || err);
  
  // CORS errors
  if (err.message && err.message.includes('CORS policy')) {
    return res.status(403).json({ 
      error: 'CORS policy violation',
      message: err.message,
    });
  }

  res.status(err.status || 500).json({ 
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'An error occurred',
  });
});

// ==================== SERVER START ====================

app.listen(PORT, '0.0.0.0', () => {
  console.log('');
  console.log('═════════════════════════════════════════════════');
  console.log('🏇 EQUINE ORACLE BACKEND - PRODUCTION READY');
  console.log('═════════════════════════════════════════════════');
  console.log(`🚀 Server:     http://0.0.0.0:${PORT}`);
  console.log(`❤️  Health:     http://0.0.0.0:${PORT}/health`);
  console.log(`📊 Model Info: http://0.0.0.0:${PORT}/api/model_info`);
  console.log(`🎯 Predict:    http://0.0.0.0:${PORT}/api/predict`);
  console.log(`🌍 Environment: ${process.env.NODE_ENV || 'production'}`);
  console.log(`🔐 CORS Origins: ${ALLOWED_ORIGINS.join(', ')}`);
  console.log('═════════════════════════════════════════════════');
  console.log('');
});
