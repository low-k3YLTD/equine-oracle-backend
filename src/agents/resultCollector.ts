/**
 * Oracle Engine - Result Collector
 * 
 * This module handles:
 * 1. Fetching race results from Tab.co.nz
 * 2. Matching results with predictions
 * 3. Calculating prediction accuracy
 * 4. Feeding results back to the retraining engine
 * 5. Maintaining result history and statistics
 */

import { getTodayRacecards, getRaceResult } from "../services/racingApiDataService";
import { autoRetrainingEngine } from "./autoRetrainingEngine";

interface RaceResult {
  raceId: string;
  track: string;
  raceNo: number;
  winnerNumber: number;
  winnerName: string;
  placedHorses: string[];
  timestamp: Date;
  status: "completed" | "abandoned" | "postponed";
}

interface PredictionResult {
  raceId: string;
  horseName: string;
  track: string;
  predictedProbability: number;
  actualResult: "win" | "loss";
  isCorrect: boolean;
  modelVersion: string;
  timestamp: Date;
}

interface CollectorMetrics {
  totalResultsCollected: number;
  totalPredictionsMatched: number;
  matchedAccuracy: number;
  lastCollectionTime: Date;
  resultsThisHour: number;
  resultsThisDay: number;
}

class ResultCollector {
  private isRunning = false;
  private collectionInterval = 10 * 60 * 1000; // 10 minutes
  private results: Map<string, RaceResult> = new Map();
  private predictions: Map<string, PredictionResult> = new Map();
  private metrics: CollectorMetrics = {
    totalResultsCollected: 0,
    totalPredictionsMatched: 0,
    matchedAccuracy: 0,
    lastCollectionTime: new Date(),
    resultsThisHour: 0,
    resultsThisDay: 0,
  };
  private processedRaces: Set<string> = new Set();
  private lastHourReset = new Date();
  private lastDayReset = new Date();

  /**
   * Start the result collector
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      console.log("[Result Collector] Collector is already running");
      return;
    }

    this.isRunning = true;
    console.log("[Result Collector] Starting result collector...");

    // Initial run
    await this.runCollectionCycle();

    // Schedule recurring collection
    setInterval(() => {
      this.runCollectionCycle().catch((error) => {
        console.error("[Result Collector] Error in collection cycle:", error);
      });
    }, this.collectionInterval);

    // Reset hourly and daily counters
    setInterval(() => {
      this.resetHourlyMetrics();
    }, 60 * 60 * 1000);

    setInterval(() => {
      this.resetDailyMetrics();
    }, 24 * 60 * 60 * 1000);
  }

  /**
   * Stop the collector
   */
  stop(): void {
    this.isRunning = false;
    console.log("[Result Collector] Stopping result collector");
  }

  /**
   * Main collection cycle
   */
  private async runCollectionCycle(): Promise<void> {
    try {
      console.log("[Result Collector] Starting collection cycle...");

      // Fetch today's schedule
      const schedule = await getTodayRacecards();
      if (!schedule || schedule.meetings.length === 0) {
        console.log("[Result Collector] No races found");
        return;
      }

      // Process each race
      let newResultsCount = 0;
      for (const meeting of schedule.meetings) {
        for (const race of meeting.races) {
          const raceKey = `${meeting.name}-${race.raceNo}`;

          // Skip if already processed
          if (this.processedRaces.has(raceKey)) {
            continue;
          }

          // Check if race is completed
          if ((race as any).status === "completed") {
            // Fetch the final result from the API
            const resultData = await getRaceResult(race.id);

            if (resultData && resultData.winner) {
                const result = this.extractRaceResult(race, meeting.name, resultData);
                await this.processRaceResult(result);
                this.processedRaces.add(raceKey);
                newResultsCount++;
            }
          }
        }
      }

      // Update metrics
      this.updateMetrics();

      console.log(
        `[Result Collector] Collection cycle complete. New results: ${newResultsCount}, Total matched: ${this.metrics.totalPredictionsMatched}`
      );
    } catch (error) {
      console.error("[Result Collector] Error in collection cycle:", error);
    }
  }

  /**
   * Extract race result from Tab.co.nz data
   */
  private extractRaceResult(race: any, track: string, resultData: any): RaceResult {
    const winner = resultData.winner;
    return {
      raceId: race.id,
      track: track,
      raceNo: race.raceNo,
      winnerNumber: winner?.number || 0,
      winnerName: winner?.name || "Unknown",
      placedHorses: resultData.placings || [],
      timestamp: new Date(),
      status: race.status || "completed",
    };
  }

  /**
   * Process a race result
   */
  private async processRaceResult(result: RaceResult): Promise<void> {
    try {
      // Store result
      const key = `${result.raceId}`;
      this.results.set(key, result);

      // Match with predictions
      const matchedPredictions = this.matchPredictions(result);

      // Feed results to retraining engine
      for (const prediction of matchedPredictions) {
        autoRetrainingEngine.addFeedback({
          raceId: prediction.raceId,
          horseName: prediction.horseName,
          track: prediction.track,
          predictedProbability: prediction.predictedProbability,
          actualResult: prediction.actualResult,
          timestamp: prediction.timestamp,
          modelVersion: prediction.modelVersion,
        });
      }

      this.metrics.totalResultsCollected++;
      this.metrics.resultsThisHour++;
      this.metrics.resultsThisDay++;

      console.log(
        `[Result Collector] Processed result for race ${result.raceId}: Winner ${result.winnerName}`
      );
    } catch (error) {
      console.error("[Result Collector] Error processing race result:", error);
    }
  }

  /**
   * Match predictions with race results
   */
  private matchPredictions(result: RaceResult): PredictionResult[] {
    const matchedPredictions: PredictionResult[] = [];
    const keysToDelete: string[] = [];

    // Find all predictions for this race
    this.predictions.forEach((prediction, key) => {
      if (prediction.raceId === result.raceId) {
        // Determine if prediction was correct
        const isWinCorrect = prediction.horseName === result.winnerName;
        const isPlaceCorrect = result.placedHorses.includes(
          prediction.horseName
        );

        const predictionResult: PredictionResult = {
          raceId: prediction.raceId,
          horseName: prediction.horseName,
          track: prediction.track,
          predictedProbability: prediction.predictedProbability,
          actualResult: isWinCorrect ? "win" : "loss",
          isCorrect: isWinCorrect,
          modelVersion: prediction.modelVersion,
          timestamp: new Date(),
        };

        matchedPredictions.push(predictionResult);
        keysToDelete.push(key);
        this.metrics.totalPredictionsMatched++;
      }
    });

    for (const key of keysToDelete) {
      this.predictions.delete(key);
    }

    return matchedPredictions;
  }

  /**
   * Register a prediction for tracking
   */
  registerPrediction(
    raceId: string,
    horseName: string,
    track: string,
    predictedProbability: number,
    modelVersion: string
  ): void {
    const key = `${raceId}-${horseName}`;
    this.predictions.set(key, {
      raceId,
      horseName,
      track,
      predictedProbability,
      actualResult: "loss", // Default, will be updated
      isCorrect: false,
      modelVersion,
      timestamp: new Date(),
    });
  }

  /**
   * Update metrics
   */
  private updateMetrics(): void {
    if (this.metrics.totalPredictionsMatched === 0) return;

    let correctCount = 0;
    this.predictions.forEach((prediction) => {
      if (prediction.isCorrect) {
        correctCount++;
      }
    });

    this.metrics.matchedAccuracy =
      correctCount / this.metrics.totalPredictionsMatched;
    this.metrics.lastCollectionTime = new Date();
  }

  /**
   * Reset hourly metrics
   */
  private resetHourlyMetrics(): void {
    const now = new Date();
    const hourAgo = new Date(now.getTime() - 60 * 60 * 1000);

    if (this.lastHourReset < hourAgo) {
      this.metrics.resultsThisHour = 0;
      this.lastHourReset = now;
    }
  }

  /**
   * Reset daily metrics
   */
  private resetDailyMetrics(): void {
    const now = new Date();
    const dayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    if (this.lastDayReset < dayAgo) {
      this.metrics.resultsThisDay = 0;
      this.lastDayReset = now;
    }
  }

  /**
   * Get current metrics
   */
  getMetrics(): CollectorMetrics {
    return { ...this.metrics };
  }

  /**
   * Get result history
   */
  getResultHistory(limit: number = 100): RaceResult[] {
    const results: RaceResult[] = [];
    this.results.forEach((result) => {
      results.push(result);
    });
    return results.slice(-limit);
  }

  /**
   * Get pending predictions
   */
  getPendingPredictions(limit: number = 100): PredictionResult[] {
    const predictions: PredictionResult[] = [];
    const predictionsArray: PredictionResult[] = [];
    this.predictions.forEach((prediction) => {
      predictionsArray.push(prediction);
    });
    return predictionsArray.slice(-limit);
  }

  /**
   * Get accuracy statistics by track
   */
  getAccuracyByTrack(): Map<string, number> {
    const trackAccuracy: Map<string, { correct: number; total: number }> =
      new Map();

    this.predictions.forEach((prediction) => {
      if (!trackAccuracy.has(prediction.track)) {
        trackAccuracy.set(prediction.track, { correct: 0, total: 0 });
      }

      const stats = trackAccuracy.get(prediction.track)!;
      stats.total++;
      if (prediction.isCorrect) {
        stats.correct++;
      }
    });

    const result: Map<string, number> = new Map();
    trackAccuracy.forEach((stats, track) => {
      result.set(track, stats.correct / stats.total);
    });

    return result;
  }

  /**
   * Get accuracy statistics by horse
   */
  getAccuracyByHorse(): Map<string, number> {
    const horseAccuracy: Map<string, { correct: number; total: number }> =
      new Map();

    this.predictions.forEach((prediction) => {
      if (!horseAccuracy.has(prediction.horseName)) {
        horseAccuracy.set(prediction.horseName, { correct: 0, total: 0 });
      }

      const stats = horseAccuracy.get(prediction.horseName)!;
      stats.total++;
      if (prediction.isCorrect) {
        stats.correct++;
      }
    });

    const result: Map<string, number> = new Map();
    horseAccuracy.forEach((stats, horse) => {
      result.set(horse, stats.correct / stats.total);
    });

    return result;
  }
}

// Export singleton instance
export const resultCollector = new ResultCollector();

