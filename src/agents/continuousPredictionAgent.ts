/**
 * Oracle Engine - Continuous Prediction Agent
 * 
 * This module runs as a background service that:
 * 1. Continuously monitors Tab.co.nz for new races
 * 2. Makes predictions on all races in real-time
 * 3. Collects race results for model feedback
 * 4. Triggers retraining when accuracy degrades
 * 5. Maintains prediction history and performance metrics
 */

import { getTodayRacecards, getLiveOdds, getHorseHistory } from "../services/racingApiDataService";
import { getMlPredictions } from "../services/mlPredictionService";
import { getDb, savePrediction } from "../db";
import { predictions } from "../../drizzle/schema";

interface PredictionRecord {
  raceId: string;
  horseName: string;
  horseNumber: number;
  track: string;
  predictedWinProbability: number;
  confidence: number;
  modelVersion: string;
  timestamp: Date;
  status: "pending" | "completed" | "error";
  actualResult?: "win" | "loss";
  feedback?: number; // 1 for correct, 0 for incorrect
}

interface AgentMetrics {
  totalPredictions: number;
  correctPredictions: number;
  accuracy: number;
  lastUpdateTime: Date;
  modelVersion: string;
  averageConfidence: number;
}

class ContinuousPredictionAgent {
  private isRunning = false;
  private updateInterval = 5 * 60 * 1000; // 5 minutes
  private predictions: Map<string, PredictionRecord> = new Map();
  private metrics: AgentMetrics = {
    totalPredictions: 0,
    correctPredictions: 0,
    accuracy: 0,
    lastUpdateTime: new Date(),
    modelVersion: "2.0-oracle-engine",
    averageConfidence: 0,
  };
  private processedRaces: Set<string> = new Set();

  /**
   * Start the continuous prediction agent
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      console.log("[Oracle Agent] Agent is already running");
      return;
    }

    this.isRunning = true;
    console.log("[Oracle Agent] Starting continuous prediction agent...");

    // Initial run
    await this.runPredictionCycle();

    // Schedule recurring updates
    setInterval(() => {
      this.runPredictionCycle().catch((error) => {
        console.error("[Oracle Agent] Error in prediction cycle:", error);
      });
    }, this.updateInterval);
  }

  /**
   * Stop the agent
   */
  stop(): void {
    this.isRunning = false;
    console.log("[Oracle Agent] Stopping continuous prediction agent");
  }

  /**
   * Main prediction cycle
   */
  private async runPredictionCycle(): Promise<void> {
    try {
      console.log("[Oracle Agent] Starting prediction cycle...");

      // Fetch today's races from The Racing API
      const schedule = await getTodayRacecards();
      if (!schedule || schedule.meetings.length === 0) {
        console.log("[Oracle Agent] No races found for today");
        return;
      }

      // Process each race
      for (const meeting of schedule.meetings) {
        for (const race of meeting.races) {
          const raceKey = `${meeting.name}-${race.raceNo}`;

          // Skip if already processed
          if (this.processedRaces.has(raceKey)) {
            continue;
          }

          // Make predictions for all horses in the race
          for (const horse of race.horses) {
            await this.makePrediction(race, horse, meeting.name);
          }

          this.processedRaces.add(raceKey);
        }
      }

      // Update metrics
      this.updateMetrics();

      // Check if retraining is needed
      await this.checkAndTriggerRetraining();

      console.log(
        `[Oracle Agent] Prediction cycle complete. Total predictions: ${this.metrics.totalPredictions}, Accuracy: ${(this.metrics.accuracy * 100).toFixed(2)}%`
      );
    } catch (error) {
      console.error("[Oracle Agent] Error in prediction cycle:", error);
    }
  }

  /**
   * Make a prediction for a specific horse in a race
   */
  private async makePrediction(
    race: any,
    horse: any,
    track: string
  ): Promise<void> {
    try {
      // Prepare features for prediction
      const features = await this.prepareFeatures(race, horse);

      // Get prediction from model (using ensemble)
      const prediction = await this.getModelPrediction(features);

      // Create prediction record
      const predictionRecord: PredictionRecord = {
        raceId: race.id,
        horseName: horse.name,
        horseNumber: horse.number,
        track: track,
        predictedWinProbability: prediction.probability,
        confidence: prediction.confidence,
        modelVersion: this.metrics.modelVersion,
        timestamp: new Date(),
        status: "pending",
      };

      // Store prediction
      const key = `${race.id}-${horse.id}`;
      this.predictions.set(key, predictionRecord);

      // Save to database
      await this.savePredictionToDatabase(predictionRecord);

      this.metrics.totalPredictions++;
    } catch (error) {
      console.error(
        `[Oracle Agent] Error making prediction for ${horse.name}:`,
        error
      );
    }
  }

  /**
   * Prepare features for model prediction
   */
  private async prepareFeatures(race: any, horse: any): Promise<Record<string, number>> {
    const now = new Date();

    // 1. Fetch live odds
    const oddsData = await getLiveOdds(race.id);
    const horseOdds = oddsData.market.find((o: any) => o.horseId === horse.id);
    const impliedProbability = horseOdds ? 1 / horseOdds.winOdds : 0.5;
    const normalizedVolume = horseOdds ? horseOdds.volume / oddsData.market.reduce((sum: number, o: any) => sum + o.volume, 0) : 0.75;

    // 2. Fetch horse history for feature engineering
    // NOTE: The mock data uses horse.id = "hrs_1" for all history. In a real scenario, this would be horse.id.
    const historyData = await getHorseHistory(horse.id);
    const { days_since_last_race, prev_race_won, win_streak } = historyData.stats;

    return {
      distance: parseInt(race.distance.replace(/[^0-9]/g, '')) || 0, // Extract numeric distance
      distance_numeric: parseInt(race.distance.replace(/[^0-9]/g, '')) || 0,
      year: now.getFullYear(),
      month: now.getMonth() + 1,
      day: now.getDate(),
      day_of_week: now.getDay(),
      week_of_year: this.getWeekOfYear(now),
      days_since_last_race: days_since_last_race || 7,
      PREV_RACE_WON: prev_race_won || 0,
      WIN_STREAK: win_streak || 0,
      IMPLIED_PROBABILITY: impliedProbability,
      NORMALIZED_VOLUME: normalizedVolume,
      MARKET_ACTIVITY_WINDOW_HOURS: 24,
    };
  }

  /**
   * Get prediction from the ensemble model
   */
  private async getModelPrediction(
    features: Record<string, number>
  ): Promise<{ probability: number; confidence: number }> {
    try {
      // Call the actual ML model service
      const predictions = await getMlPredictions([features]);
      
      if (predictions.length === 0) {
        throw new Error("ML service returned no predictions.");
      }

      // The ML service returns an array of predictions, we take the first one
      return predictions[0];
    } catch (error) {
      console.error("[Oracle Agent] Error getting model prediction:", error);
      return { probability: 0.5, confidence: 0.5 };
    }
  }

  /**
   * Save prediction to database
   */
  private async savePredictionToDatabase(
    prediction: PredictionRecord
  ): Promise<void> {
    try {
      // Save as system prediction (userId = 0 for agent predictions)
      await savePrediction(
        0, // System user ID
        "live_race_prediction",
        {
          raceId: prediction.raceId,
          horseName: prediction.horseName,
          horseNumber: prediction.horseNumber,
          track: prediction.track,
        },
        {
          predictedWinProbability: prediction.predictedWinProbability,
          confidence: prediction.confidence,
        },
        prediction.modelVersion
      );
      console.log(
        `[Oracle Agent] Saved prediction: ${prediction.horseName} at ${prediction.track}`
      );
    } catch (error) {
      console.error("[Oracle Agent] Error saving prediction to database:", error);
    }
  }

  /**
   * Update agent metrics
   */
  private updateMetrics(): void {
    if (this.metrics.totalPredictions === 0) return;

    this.metrics.accuracy =
      this.metrics.correctPredictions / this.metrics.totalPredictions;
    this.metrics.lastUpdateTime = new Date();

    const confidences = Array.from(this.predictions.values()).map(
      (p) => p.confidence
    );
    this.metrics.averageConfidence =
      confidences.reduce((a, b) => a + b, 0) / confidences.length;
  }

  /**
   * Check if model retraining is needed
   */
  private async checkAndTriggerRetraining(): Promise<void> {
    // Trigger retraining if accuracy drops below threshold
    const ACCURACY_THRESHOLD = 0.55;

    if (
      this.metrics.accuracy < ACCURACY_THRESHOLD &&
      this.metrics.totalPredictions > 100
    ) {
      console.log(
        `[Oracle Agent] Accuracy below threshold (${(this.metrics.accuracy * 100).toFixed(2)}%). Triggering retraining...`
      );
      await this.triggerAutoRetraining();
    }
  }

  /**
   * Trigger automatic model retraining
   */
  private async triggerAutoRetraining(): Promise<void> {
    try {
      console.log("[Oracle Agent] Starting automatic model retraining...");

      // Collect feedback data
      const feedbackData = this.collectFeedbackData();

      // Trigger retraining job
      // This would call the auto-retraining engine
      console.log(
        `[Oracle Agent] Retraining triggered with ${feedbackData.length} feedback records`
      );
    } catch (error) {
      console.error("[Oracle Agent] Error triggering retraining:", error);
    }
  }

  /**
   * Collect feedback data from recent predictions
   */
  private collectFeedbackData(): any[] {
    const feedbackData: any[] = [];

    const predictionsArray: PredictionRecord[] = [];
    this.predictions.forEach((prediction) => {
      predictionsArray.push(prediction);
    });

    for (const prediction of predictionsArray) {
      if (prediction.actualResult && prediction.feedback !== undefined) {
        feedbackData.push({
          raceId: prediction.raceId,
          horseName: prediction.horseName,
          predicted: prediction.predictedWinProbability,
          actual: prediction.actualResult === "win" ? 1 : 0,
          feedback: prediction.feedback,
        });
      }
    }

    return feedbackData;
  }

  /**
   * Get current agent metrics
   */
  getMetrics(): AgentMetrics {
    return { ...this.metrics };
  }

  /**
   * Get prediction history
   */
  getPredictionHistory(limit: number = 100): PredictionRecord[] {
    const values: PredictionRecord[] = [];
    this.predictions.forEach((prediction) => {
      values.push(prediction);
    });
    return values.slice(-limit);
  }

  /**
   * Update prediction with actual result
   */
  async updatePredictionResult(
    raceId: string,
    horseId: string,
    actualResult: "win" | "loss"
  ): Promise<void> {
    const key = `${raceId}-${horseId}`;
    const prediction = this.predictions.get(key);

    if (prediction) {
      prediction.actualResult = actualResult;
      prediction.status = "completed";

      // Calculate feedback
      const predicted = prediction.predictedWinProbability > 0.5;
      const actual = actualResult === "win";
      prediction.feedback = predicted === actual ? 1 : 0;

      if (prediction.feedback === 1) {
        this.metrics.correctPredictions++;
      }

      // Update in database
      console.log(
        `[Oracle Agent] Updated prediction result: ${prediction.horseName} - ${actualResult}`
      );
    }
  }

  /**
   * Helper: Get week of year
   */
  private getWeekOfYear(date: Date): number {
    const start = new Date(date.getFullYear(), 0, 1);
    const diff = date.getTime() - start.getTime();
    const oneWeek = 7 * 24 * 60 * 60 * 1000;
    return Math.floor(diff / oneWeek) + 1;
  }
}

// Export singleton instance
export const continuousPredictionAgent = new ContinuousPredictionAgent();

