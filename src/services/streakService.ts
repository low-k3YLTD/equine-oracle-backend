import { getMlPredictions } from './mlPredictionService';

export async function predictStreak(horseId: string, currentStreak: number, features: any) {
  // Mock streak prediction logic
  // In a real scenario, this would use a specialized RNN or LSTM model
  const basePrediction = await getMlPredictions([features]);
  const { probability, confidence } = basePrediction[0];
  
  // Adjust probability based on streak (momentum factor)
  const momentumFactor = 1 + (currentStreak * 0.05);
  const streakProbability = Math.min(0.99, probability * momentumFactor);
  
  return {
    horseId,
    currentStreak,
    streakProbability,
    confidence: confidence * 0.9, // Slightly lower confidence for streak predictions
    recommendation: streakProbability > 0.75 ? 'Strong Momentum' : 'Mean Reversion Likely',
  };
}
