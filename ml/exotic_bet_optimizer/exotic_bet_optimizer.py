"""
Exotic Bet Optimizer - Quick Win Strategy Implementation
========================================================

Focus: Implement the three core recommendations from the alignment report immediately:
1. Re-optimize for joint probability calibration (shift from ranking to probability)
2. Build exotic combination generator (Exacta, Trifecta, Superfecta)
3. EV signal generation (identify profitable bets)

Author: AI Assistant
Date: 2025-12-28
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from itertools import permutations, combinations
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Horse:
    """Represents a horse with its racing attributes."""
    id: int
    name: str
    win_probability: float
    place_probability: float
    show_probability: float
    odds: float
    jockey: str
    trainer: str
    form_rating: float
    speed_rating: float
    class_rating: float


@dataclass
class ExoticBet:
    """Represents an exotic bet combination."""
    bet_type: str
    combination: List[int]  # Horse IDs in order
    probability: float
    payout_odds: float
    expected_value: float
    kelly_fraction: float
    confidence_score: float


class ProbabilityCalibrator:
    """
    Core Recommendation #1: Re-optimize for joint probability calibration
    Shifts from ranking-based to probability-based approach
    """
    
    def __init__(self):
        self.calibration_history = []
        self.market_efficiency_factor = 0.85  # Market tends to be 85% efficient
        
    def calibrate_win_probabilities(self, horses: List[Horse]) -> List[Horse]:
        """
        Calibrate win probabilities using market odds and proprietary models
        """
        logger.info("Starting probability calibration for win bets")
        
        # Convert odds to implied probabilities
        implied_probs = []
        for horse in horses:
            # Convert decimal odds to probability (accounting for bookmaker margin)
            implied_prob = 1 / horse.odds if horse.odds > 0 else 0.01
            implied_probs.append(implied_prob)
        
        # Normalize to ensure probabilities sum to 1
        total_implied = sum(implied_probs)
        normalized_probs = [prob / total_implied for prob in implied_probs]
        
        # Apply calibration based on historical performance
        calibrated_horses = []
        for i, horse in enumerate(horses):
            # Blend market probability with model probability
            market_prob = normalized_probs[i]
            model_prob = horse.win_probability
            
            # Weighted average (70% model, 30% market for better edge)
            calibrated_prob = (0.7 * model_prob + 0.3 * market_prob)
            
            # Create new horse object with calibrated probability
            calibrated_horse = Horse(
                id=horse.id,
                name=horse.name,
                win_probability=calibrated_prob,
                place_probability=self._estimate_place_probability(calibrated_prob, len(horses)),
                show_probability=self._estimate_show_probability(calibrated_prob, len(horses)),
                odds=horse.odds,
                jockey=horse.jockey,
                trainer=horse.trainer,
                form_rating=horse.form_rating,
                speed_rating=horse.speed_rating,
                class_rating=horse.class_rating
            )
            calibrated_horses.append(calibrated_horse)
        
        logger.info(f"Calibrated probabilities for {len(calibrated_horses)} horses")
        return calibrated_horses
    
    def _estimate_place_probability(self, win_prob: float, field_size: int) -> float:
        """Estimate place (top 2) probability from win probability"""
        # Statistical approximation based on field size
        if field_size <= 4:
            return min(win_prob * 2.5, 0.95)
        elif field_size <= 8:
            return min(win_prob * 2.2, 0.90)
        else:
            return min(win_prob * 1.8, 0.85)
    
    def _estimate_show_probability(self, win_prob: float, field_size: int) -> float:
        """Estimate show (top 3) probability from win probability"""
        # Statistical approximation based on field size
        if field_size <= 5:
            return min(win_prob * 3.0, 0.98)
        elif field_size <= 10:
            return min(win_prob * 2.5, 0.95)
        else:
            return min(win_prob * 2.0, 0.90)
    
    def calculate_joint_probabilities(self, horses: List[Horse]) -> Dict[str, Any]:
        """
        Calculate joint probabilities for exotic bet combinations
        """
        logger.info("Calculating joint probabilities for exotic combinations")
        
        joint_probs = {
            'exacta': self._calculate_exacta_probabilities(horses),
            'trifecta': self._calculate_trifecta_probabilities(horses),
            'superfecta': self._calculate_superfecta_probabilities(horses)
        }
        
        return joint_probs
    
    def _calculate_exacta_probabilities(self, horses: List[Horse]) -> Dict[Tuple[int, int], float]:
        """Calculate probabilities for all exacta combinations"""
        exacta_probs = {}
        
        for perm in permutations([h.id for h in horses], 2):
            horse1 = next(h for h in horses if h.id == perm[0])
            horse2 = next(h for h in horses if h.id == perm[1])
            
            # P(Horse1 wins AND Horse2 comes second)
            # Using conditional probability: P(A and B) = P(A) * P(B|A)
            prob_1st = horse1.win_probability
            prob_2nd_given_1st = horse2.win_probability / (1 - horse1.win_probability + 1e-10)
            
            joint_prob = prob_1st * prob_2nd_given_1st
            exacta_probs[perm] = joint_prob
        
        return exacta_probs
    
    def _calculate_trifecta_probabilities(self, horses: List[Horse]) -> Dict[Tuple[int, int, int], float]:
        """Calculate probabilities for trifecta combinations (limited to top contenders)"""
        trifecta_probs = {}
        
        # Limit to top 6 horses for computational efficiency
        top_horses = sorted(horses, key=lambda h: h.win_probability, reverse=True)[:6]
        
        for perm in permutations([h.id for h in top_horses], 3):
            horse1 = next(h for h in horses if h.id == perm[0])
            horse2 = next(h for h in horses if h.id == perm[1])
            horse3 = next(h for h in horses if h.id == perm[2])
            
            # Sequential conditional probabilities
            prob_1st = horse1.win_probability
            prob_2nd_given_1st = horse2.win_probability / (1 - horse1.win_probability + 1e-10)
            remaining_prob = 1 - horse1.win_probability - horse2.win_probability
            prob_3rd_given_12 = horse3.win_probability / (remaining_prob + 1e-10)
            
            joint_prob = prob_1st * prob_2nd_given_1st * prob_3rd_given_12
            trifecta_probs[perm] = joint_prob
        
        return trifecta_probs
    
    def _calculate_superfecta_probabilities(self, horses: List[Horse]) -> Dict[Tuple[int, int, int, int], float]:
        """Calculate probabilities for superfecta combinations (top contenders only)"""
        superfecta_probs = {}
        
        # Limit to top 5 horses for computational efficiency
        top_horses = sorted(horses, key=lambda h: h.win_probability, reverse=True)[:5]
        
        for perm in permutations([h.id for h in top_horses], 4):
            # Calculate sequential conditional probabilities
            prob = 1.0
            remaining_horses = list(horses)
            
            for i, horse_id in enumerate(perm):
                horse = next(h for h in remaining_horses if h.id == horse_id)
                position_prob = horse.win_probability / sum(h.win_probability for h in remaining_horses)
                prob *= position_prob
                remaining_horses.remove(horse)
            
            superfecta_probs[perm] = prob
        
        return superfecta_probs


class ExoticCombinationGenerator:
    """
    Core Recommendation #2: Build exotic combination generator
    Generates optimized Exacta, Trifecta, and Superfecta combinations
    """
    
    def __init__(self, calibrator: ProbabilityCalibrator):
        self.calibrator = calibrator
        self.min_probability_threshold = 0.001  # Minimum probability to consider
        
    def generate_exacta_combinations(self, horses: List[Horse], 
                                   max_combinations: int = 20) -> List[ExoticBet]:
        """Generate top exacta combinations with EV calculations"""
        logger.info("Generating exacta combinations")
        
        exacta_probs = self.calibrator._calculate_exacta_probabilities(horses)
        exacta_bets = []
        
        for combination, probability in exacta_probs.items():
            if probability < self.min_probability_threshold:
                continue
                
            # Estimate payout odds (simplified - would need actual market data)
            payout_odds = self._estimate_exacta_payout(combination, horses)
            
            # Calculate expected value
            expected_value = (probability * payout_odds) - 1.0
            
            # Calculate Kelly fraction for bet sizing
            kelly_fraction = self._calculate_kelly_fraction(probability, payout_odds)
            
            # Calculate confidence score based on probability and horse ratings
            confidence_score = self._calculate_confidence_score(combination, horses, probability)
            
            exacta_bet = ExoticBet(
                bet_type="exacta",
                combination=list(combination),
                probability=probability,
                payout_odds=payout_odds,
                expected_value=expected_value,
                kelly_fraction=kelly_fraction,
                confidence_score=confidence_score
            )
            
            exacta_bets.append(exacta_bet)
        
        # Sort by expected value and return top combinations
        exacta_bets.sort(key=lambda bet: bet.expected_value, reverse=True)
        return exacta_bets[:max_combinations]
    
    def generate_trifecta_combinations(self, horses: List[Horse], 
                                     max_combinations: int = 15) -> List[ExoticBet]:
        """Generate top trifecta combinations with EV calculations"""
        logger.info("Generating trifecta combinations")
        
        trifecta_probs = self.calibrator._calculate_trifecta_probabilities(horses)
        trifecta_bets = []
        
        for combination, probability in trifecta_probs.items():
            if probability < self.min_probability_threshold:
                continue
                
            payout_odds = self._estimate_trifecta_payout(combination, horses)
            expected_value = (probability * payout_odds) - 1.0
            kelly_fraction = self._calculate_kelly_fraction(probability, payout_odds)
            confidence_score = self._calculate_confidence_score(combination, horses, probability)
            
            trifecta_bet = ExoticBet(
                bet_type="trifecta",
                combination=list(combination),
                probability=probability,
                payout_odds=payout_odds,
                expected_value=expected_value,
                kelly_fraction=kelly_fraction,
                confidence_score=confidence_score
            )
            
            trifecta_bets.append(trifecta_bet)
        
        trifecta_bets.sort(key=lambda bet: bet.expected_value, reverse=True)
        return trifecta_bets[:max_combinations]
    
    def generate_superfecta_combinations(self, horses: List[Horse], 
                                       max_combinations: int = 10) -> List[ExoticBet]:
        """Generate top superfecta combinations with EV calculations"""
        logger.info("Generating superfecta combinations")
        
        superfecta_probs = self.calibrator._calculate_superfecta_probabilities(horses)
        superfecta_bets = []
        
        for combination, probability in superfecta_probs.items():
            if probability < self.min_probability_threshold:
                continue
                
            payout_odds = self._estimate_superfecta_payout(combination, horses)
            expected_value = (probability * payout_odds) - 1.0
            kelly_fraction = self._calculate_kelly_fraction(probability, payout_odds)
            confidence_score = self._calculate_confidence_score(combination, horses, probability)
            
            superfecta_bet = ExoticBet(
                bet_type="superfecta",
                combination=list(combination),
                probability=probability,
                payout_odds=payout_odds,
                expected_value=expected_value,
                kelly_fraction=kelly_fraction,
                confidence_score=confidence_score
            )
            
            superfecta_bets.append(superfecta_bet)
        
        superfecta_bets.sort(key=lambda bet: bet.expected_value, reverse=True)
        return superfecta_bets[:max_combinations]
    
    def _estimate_exacta_payout(self, combination: Tuple[int, int], horses: List[Horse]) -> float:
        """Estimate exacta payout based on horse odds"""
        horse1 = next(h for h in horses if h.id == combination[0])
        horse2 = next(h for h in horses if h.id == combination[1])
        
        # Simplified payout calculation (actual would use track takeout rates)
        base_payout = horse1.odds * horse2.odds * 0.8  # 20% track takeout
        return max(base_payout, 2.0)  # Minimum $2 return
    
    def _estimate_trifecta_payout(self, combination: Tuple[int, int, int], horses: List[Horse]) -> float:
        """Estimate trifecta payout based on horse odds"""
        payouts = []
        for horse_id in combination:
            horse = next(h for h in horses if h.id == horse_id)
            payouts.append(horse.odds)
        
        base_payout = np.prod(payouts) * 0.75  # 25% track takeout
        return max(base_payout, 5.0)  # Minimum $5 return
    
    def _estimate_superfecta_payout(self, combination: Tuple[int, int, int, int], horses: List[Horse]) -> float:
        """Estimate superfecta payout based on horse odds"""
        payouts = []
        for horse_id in combination:
            horse = next(h for h in horses if h.id == horse_id)
            payouts.append(horse.odds)
        
        base_payout = np.prod(payouts) * 0.7  # 30% track takeout
        return max(base_payout, 10.0)  # Minimum $10 return
    
    def _calculate_kelly_fraction(self, probability: float, odds: float) -> float:
        """Calculate optimal bet size using Kelly Criterion"""
        if odds <= 1.0:
            return 0.0
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds - 1, p = probability, q = 1 - p
        b = odds - 1
        p = probability
        q = 1 - p
        
        kelly = (b * p - q) / b
        
        # Cap Kelly fraction at 25% for risk management
        return max(0.0, min(kelly, 0.25))
    
    def _calculate_confidence_score(self, combination: Tuple, horses: List[Horse], 
                                  probability: float) -> float:
        """Calculate confidence score based on multiple factors"""
        # Get horses in combination
        combo_horses = [next(h for h in horses if h.id == horse_id) for horse_id in combination]
        
        # Factor 1: Average form rating
        avg_form = np.mean([h.form_rating for h in combo_horses])
        
        # Factor 2: Speed rating consistency
        avg_speed = np.mean([h.speed_rating for h in combo_horses])
        
        # Factor 3: Probability magnitude
        prob_factor = min(probability * 100, 10.0) / 10.0  # Normalize to 0-1
        
        # Factor 4: Class rating
        avg_class = np.mean([h.class_rating for h in combo_horses])
        
        # Weighted combination
        confidence = (0.3 * avg_form + 0.25 * avg_speed + 0.25 * prob_factor + 0.2 * avg_class) / 100
        
        return min(max(confidence, 0.0), 1.0)


class EVSignalGenerator:
    """
    Core Recommendation #3: EV signal generation
    Identifies profitable bets with positive expected value
    """
    
    def __init__(self, min_ev_threshold: float = 0.05):
        self.min_ev_threshold = min_ev_threshold
        self.signal_history = []
        
    def generate_ev_signals(self, exotic_bets: List[ExoticBet]) -> List[Dict[str, Any]]:
        """Generate EV signals for profitable bets"""
        logger.info("Generating EV signals for profitable opportunities")
        
        positive_ev_bets = [bet for bet in exotic_bets if bet.expected_value > self.min_ev_threshold]
        
        signals = []
        for bet in positive_ev_bets:
            signal = {
                'timestamp': datetime.now().isoformat(),
                'bet_type': bet.bet_type,
                'combination': bet.combination,
                'probability': bet.probability,
                'expected_value': bet.expected_value,
                'kelly_fraction': bet.kelly_fraction,
                'confidence_score': bet.confidence_score,
                'signal_strength': self._calculate_signal_strength(bet),
                'risk_level': self._assess_risk_level(bet),
                'recommended_stake': self._calculate_recommended_stake(bet)
            }
            signals.append(signal)
        
        # Sort by signal strength
        signals.sort(key=lambda s: s['signal_strength'], reverse=True)
        
        self.signal_history.extend(signals)
        return signals
    
    def _calculate_signal_strength(self, bet: ExoticBet) -> float:
        """Calculate signal strength combining EV, confidence, and Kelly fraction"""
        ev_component = min(bet.expected_value * 2, 1.0)  # Cap at 1.0
        confidence_component = bet.confidence_score
        kelly_component = min(bet.kelly_fraction * 4, 1.0)  # Cap at 1.0
        
        # Weighted average
        signal_strength = (0.4 * ev_component + 0.35 * confidence_component + 0.25 * kelly_component)
        
        return signal_strength
    
    def _assess_risk_level(self, bet: ExoticBet) -> str:
        """Assess risk level based on probability and variance"""
        if bet.probability > 0.1:
            return "LOW"
        elif bet.probability > 0.05:
            return "MEDIUM"
        elif bet.probability > 0.01:
            return "HIGH"
        else:
            return "VERY_HIGH"
    
    def _calculate_recommended_stake(self, bet: ExoticBet, bankroll: float = 1000.0) -> float:
        """Calculate recommended stake based on Kelly criterion"""
        return bankroll * bet.kelly_fraction
    
    def get_top_signals(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get top N signals by strength"""
        return sorted(self.signal_history, key=lambda s: s['signal_strength'], reverse=True)[:n]


class ExoticBetOptimizer:
    """
    Main optimizer class that orchestrates all components
    """
    
    def __init__(self):
        self.calibrator = ProbabilityCalibrator()
        self.combination_generator = ExoticCombinationGenerator(self.calibrator)
        self.signal_generator = EVSignalGenerator()
        
    def optimize_exotic_bets(self, horses: List[Horse]) -> Dict[str, Any]:
        """
        Main optimization function that implements all three core recommendations
        """
        logger.info(f"Starting exotic bet optimization for {len(horses)} horses")
        
        # Step 1: Calibrate probabilities (Recommendation #1)
        calibrated_horses = self.calibrator.calibrate_win_probabilities(horses)
        
        # Step 2: Generate exotic combinations (Recommendation #2)
        exacta_bets = self.combination_generator.generate_exacta_combinations(calibrated_horses)
        trifecta_bets = self.combination_generator.generate_trifecta_combinations(calibrated_horses)
        superfecta_bets = self.combination_generator.generate_superfecta_combinations(calibrated_horses)
        
        # Combine all bets
        all_exotic_bets = exacta_bets + trifecta_bets + superfecta_bets
        
        # Step 3: Generate EV signals (Recommendation #3)
        ev_signals = self.signal_generator.generate_ev_signals(all_exotic_bets)
        
        # Compile results
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_horses': len(horses),
            'calibrated_horses': [
                {
                    'id': h.id,
                    'name': h.name,
                    'calibrated_win_prob': h.win_probability,
                    'place_prob': h.place_probability,
                    'show_prob': h.show_probability
                }
                for h in calibrated_horses
            ],
            'exotic_combinations': {
                'exacta': len(exacta_bets),
                'trifecta': len(trifecta_bets),
                'superfecta': len(superfecta_bets)
            },
            'profitable_signals': len(ev_signals),
            'top_opportunities': ev_signals[:10],
            'summary_stats': self._calculate_summary_stats(all_exotic_bets, ev_signals)
        }
        
        logger.info(f"Optimization complete. Found {len(ev_signals)} profitable opportunities")
        return results
    
    def _calculate_summary_stats(self, all_bets: List[ExoticBet], signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics"""
        if not all_bets:
            return {}
        
        expected_values = [bet.expected_value for bet in all_bets]
        
        return {
            'total_combinations_analyzed': len(all_bets),
            'profitable_opportunities': len(signals),
            'profitability_rate': len(signals) / len(all_bets) if all_bets else 0,
            'average_expected_value': np.mean(expected_values),
            'max_expected_value': np.max(expected_values),
            'total_kelly_allocation': sum(bet.kelly_fraction for bet in all_bets if bet.expected_value > 0)
        }


# Example usage and testing
def create_sample_horses() -> List[Horse]:
    """Create sample horses for testing"""
    return [
        Horse(1, "Thunder Bolt", 0.25, 0.45, 0.65, 4.0, "J. Smith", "T. Brown", 85, 92, 88),
        Horse(2, "Lightning Strike", 0.20, 0.40, 0.60, 5.0, "M. Johnson", "R. Wilson", 80, 88, 85),
        Horse(3, "Storm Runner", 0.18, 0.38, 0.58, 5.5, "L. Davis", "S. Miller", 82, 90, 86),
        Horse(4, "Wind Chaser", 0.15, 0.35, 0.55, 6.5, "K. Wilson", "D. Taylor", 78, 85, 82),
        Horse(5, "Fire Bolt", 0.12, 0.30, 0.50, 8.0, "P. Anderson", "C. Moore", 75, 82, 79),
        Horse(6, "Swift Arrow", 0.10, 0.25, 0.45, 10.0, "R. Thomas", "J. Jackson", 72, 78, 76)
    ]


def main():
    """Main function to demonstrate the Exotic Bet Optimizer"""
    print("🏇 Exotic Bet Optimizer - Quick Win Strategy")
    print("=" * 50)
    
    # Create sample data
    horses = create_sample_horses()
    
    # Initialize optimizer
    optimizer = ExoticBetOptimizer()
    
    # Run optimization
    results = optimizer.optimize_exotic_bets(horses)
    
    # Display results
    print(f"\n📊 Optimization Results:")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Total horses analyzed: {results['total_horses']}")
    print(f"Profitable opportunities found: {results['profitable_signals']}")
    
    print(f"\n🎯 Top Opportunities:")
    for i, signal in enumerate(results['top_opportunities'][:5], 1):
        print(f"{i}. {signal['bet_type'].upper()} - Combination {signal['combination']}")
        print(f"   EV: {signal['expected_value']:.3f} | Confidence: {signal['confidence_score']:.3f}")
        print(f"   Kelly: {signal['kelly_fraction']:.3f} | Risk: {signal['risk_level']}")
        print(f"   Recommended Stake: ${signal['recommended_stake']:.2f}")
        print()
    
    # Save results to JSON
    with open('/mnt/user-data/outputs/exotic_bet_optimization_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("📁 Results saved to exotic_bet_optimization_results.json")
    
    return results


if __name__ == "__main__":
    results = main()