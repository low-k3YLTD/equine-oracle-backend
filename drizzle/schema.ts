import { pgTable, serial, text, timestamp, integer, boolean, unique, primaryKey, real } from "drizzle-orm/pg-core";

// --- 1. Subscriptions Table ---
export const subscriptions = pgTable("subscriptions", {
  id: serial("id").primaryKey(),
  tier: text("tier").notNull().unique(), // e.g., 'Free', 'Basic', 'Premium', 'Elite'
  maxPredictionsPerMonth: integer("max_predictions_per_month").notNull(),
  apiAccess: boolean("api_access").notNull(),
  customModels: boolean("custom_models").notNull(),
  prioritySupport: boolean("priority_support").notNull(),
  priceMonthly: real("price_monthly").notNull(), // Price in USD
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

// --- 2. Users Table (Implicitly needed for foreign keys) ---
// Assuming a separate user management system (e.g., Manus OAuth) provides the core user table.
// We'll define a minimal one for foreign key constraints.
export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  externalId: text("external_id").unique().notNull(), // ID from Manus OAuth or similar
  email: text("email").unique().notNull(),
  subscriptionId: integer("subscription_id").references(() => subscriptions.id),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

// --- 3. API Keys Table ---
export const apiKeys = pgTable("api_keys", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").references(() => users.id).notNull(),
  keyHash: text("key_hash").notNull().unique(), // Store a hash of the API key
  keyPrefix: text("key_prefix").notNull().unique(), // Store a prefix for quick lookup (e.g., 'eo_')
  name: text("name").notNull(), // User-defined name for the key
  isActive: boolean("is_active").default(true).notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  expiresAt: timestamp("expires_at"),
  lastUsedAt: timestamp("last_used_at"),
});

// --- 4. User Credits Table (for API call tracking) ---
export const userCredits = pgTable("user_credits", {
  userId: integer("user_id").references(() => users.id).notNull(),
  dailyLimit: integer("daily_limit").notNull(),
  dailyUsed: integer("daily_used").default(0).notNull(),
  monthlyLimit: integer("monthly_limit").notNull(),
  monthlyUsed: integer("monthly_used").default(0).notNull(),
  lastReset: timestamp("last_reset").defaultNow().notNull(),
}, (table) => {
  return {
    pk: primaryKey({ columns: [table.userId] }),
  };
});

// --- 5. Predictions Table ---
export const predictions = pgTable("predictions", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").references(() => users.id).notNull(), // 0 for system predictions
  type: text("type").notNull(), // e.g., 'live_race_prediction', 'single_race_request', 'four_race_streak'
  modelVersion: text("model_version").notNull(),
  inputData: text("input_data").notNull(), // JSON string of input features
  outputData: text("output_data").notNull(), // JSON string of prediction results
  createdAt: timestamp("created_at").defaultNow().notNull(),
  raceId: text("race_id"), // Optional, for linking to a specific race
  track: text("track"),
  horseName: text("horse_name"),
  isCorrect: boolean("is_correct"), // For system predictions, updated by result collector
  feedback: integer("feedback"), // 1 for correct, 0 for incorrect
});

// Add indexes for efficient querying
export const predictionsIndexes = unique("predictions_user_race_idx").on(predictions.userId, predictions.raceId);
export const apiKeysIndex = unique("api_keys_user_idx").on(apiKeys.userId);
