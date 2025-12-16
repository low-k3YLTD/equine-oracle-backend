import { protectedProcedure, router } from "../_core/trpc";
import { z } from "zod";
import { generatePredictions } from "../prediction";
import { createRace, createPrediction } from "../db";
import Papa from "papaparse";

const horseDataSchema = z.object({
  horseName: z.string(),
  distanceNumeric: z.number(),
  daysSinceLastRace: z.number(),
  horseRankRollingMean: z.number(),
  horseRankRollingStd: z.number(),
  horseTop3RateRollingMean: z.number(),
  horseTop3RateRollingStd: z.number(),
  horseNameDecayForm: z.number(),
  horsePerfAvgRollingMean: z.number(),
  horsePerfAvgRollingStd: z.number(),
  prevPerfIndex: z.number(),
  trackDistAvgPos: z.number(),
  raceClassScore: z.number(),
  isWinner: z.number().optional(),
  isTop3: z.number().optional(),
});

export const csvUploadRouter = router({
  uploadAndPredict: protectedProcedure
    .input(
      z.object({
        csvContent: z.string(),
        track: z.string(),
        raceType: z.string(),
        distance: z.number(),
      })
    )
    .mutation(async ({ input, ctx }) => {
      try {
        // Parse CSV content
        const parseResult = await new Promise<any[]>((resolve, reject) => {
          Papa.parse(input.csvContent, {
            header: true,
            skipEmptyLines: true,
            dynamicTyping: true,
            complete: (results: any) => {
              resolve(results.data);
            },
            error: (error: any) => {
              reject(new Error(`CSV parsing error: ${error.message}`));
            },
          });
        });

        if (!parseResult || parseResult.length === 0) {
          throw new Error("No valid data found in CSV");
        }

        // Validate and convert data
        const horses = parseResult.map((row: any) => ({
          horseName: row.horseName || row.horse_name || "",
          distanceNumeric: parseFloat(row.distanceNumeric || row.distance_numeric || 0),
          daysSinceLastRace: parseFloat(row.daysSinceLastRace || row.days_since_last_race || 0),
          horseRankRollingMean: parseFloat(row.horseRankRollingMean || row.horse_rank_rolling_mean || 0),
          horseRankRollingStd: parseFloat(row.horseRankRollingStd || row.horse_rank_rolling_std || 0),
          horseTop3RateRollingMean: parseFloat(row.horseTop3RateRollingMean || row.horse_top3_rate_rolling_mean || 0),
          horseTop3RateRollingStd: parseFloat(row.horseTop3RateRollingStd || row.horse_top3_rate_rolling_std || 0),
          horseNameDecayForm: parseFloat(row.horseNameDecayForm || row.horse_name_decay_form || 0),
          horsePerfAvgRollingMean: parseFloat(row.horsePerfAvgRollingMean || row.horse_perf_avg_rolling_mean || 0),
          horsePerfAvgRollingStd: parseFloat(row.horsePerfAvgRollingStd || row.horse_perf_avg_rolling_std || 0),
          prevPerfIndex: parseFloat(row.prevPerfIndex || row.prev_perf_index || 0),
          trackDistAvgPos: parseFloat(row.trackDistAvgPos || row.track_dist_avg_pos || 0),
          raceClassScore: parseFloat(row.raceClassScore || row.race_class_score || 0),
        }));

        if (horses.length === 0) {
          throw new Error("No valid horse data found in CSV");
        }

        // Generate predictions
        const predictions = await generatePredictions(horses);

        // Create race record
        const race = await createRace({
          date: new Date(),
          track: input.track,
          raceType: input.raceType,
          distance: input.distance,
        });

        // Store predictions
        if (race) {
          for (const pred of predictions) {
            await createPrediction({
              userId: ctx.user.id,
              raceId: race.id,
              horseName: pred.horseName,
              predictedRank: pred.predictedRank,
              confidenceScore: pred.confidenceScore,
            });
          }
        }

        return {
          success: true,
          predictions,
          raceId: race?.id,
          rowsProcessed: horses.length,
        };
      } catch (error) {
        console.error("CSV upload error:", error);
        throw error;
      }
    }),
});
