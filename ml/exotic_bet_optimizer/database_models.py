"""
Database Models for Exotic Bet Optimizer
========================================

SQLAlchemy models for storing optimization results, signals, and performance data
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import json
from typing import Dict, List, Any, Optional

Base = declarative_base()


class Race(Base):
    """Model for race information"""
    __tablename__ = 'races'
    
    id = Column(Integer, primary_key=True)
    race_id = Column(String(100), unique=True, nullable=False, index=True)
    race_name = Column(String(200))
    track_name = Column(String(100))
    race_date = Column(DateTime, nullable=False)
    race_time = Column(String(10))
    distance = Column(String(20))
    surface = Column(String(20))  # Dirt, Turf, Synthetic
    race_class = Column(String(50))
    purse = Column(Float)
    field_size = Column(Integer)
    weather_conditions = Column(String(100))
    track_condition = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    horses = relationship("RaceHorse", back_populates="race")
    optimizations = relationship("OptimizationRun", back_populates="race")


class RaceHorse(Base):
    """Model for horses in a specific race"""
    __tablename__ = 'race_horses'
    
    id = Column(Integer, primary_key=True)
    race_id = Column(Integer, ForeignKey('races.id'), nullable=False)
    horse_id = Column(Integer, nullable=False)
    horse_name = Column(String(100), nullable=False)
    post_position = Column(Integer)
    jockey_name = Column(String(100))
    trainer_name = Column(String(100))
    owner_name = Column(String(100))
    
    # Odds and probabilities
    morning_line_odds = Column(Float)
    final_odds = Column(Float)
    original_win_probability = Column(Float)
    calibrated_win_probability = Column(Float)
    place_probability = Column(Float)
    show_probability = Column(Float)
    
    # Ratings
    form_rating = Column(Float)
    speed_rating = Column(Float)
    class_rating = Column(Float)
    pace_rating = Column(Float)
    
    # Horse details
    age = Column(Integer)
    sex = Column(String(10))
    weight = Column(Integer)
    equipment_change = Column(String(200))
    medication = Column(String(200))
    
    # Performance data
    recent_form = Column(JSON)  # Last 5-10 race results
    lifetime_stats = Column(JSON)  # Career statistics
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    race = relationship("Race", back_populates="horses")


class OptimizationRun(Base):
    """Model for optimization run results"""
    __tablename__ = 'optimization_runs'
    
    id = Column(Integer, primary_key=True)
    race_id = Column(Integer, ForeignKey('races.id'), nullable=False)
    run_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Configuration
    min_ev_threshold = Column(Float, default=0.05)
    max_exacta_combinations = Column(Integer, default=20)
    max_trifecta_combinations = Column(Integer, default=15)
    max_superfecta_combinations = Column(Integer, default=10)
    
    # Results summary
    total_combinations_analyzed = Column(Integer)
    profitable_opportunities = Column(Integer)
    profitability_rate = Column(Float)
    average_expected_value = Column(Float)
    max_expected_value = Column(Float)
    total_kelly_allocation = Column(Float)
    
    # Processing metadata
    processing_time_seconds = Column(Float)
    optimization_version = Column(String(20), default='1.0.0')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    race = relationship("Race", back_populates="optimizations")
    exotic_bets = relationship("ExoticBetResult", back_populates="optimization_run")
    ev_signals = relationship("EVSignal", back_populates="optimization_run")


class ExoticBetResult(Base):
    """Model for individual exotic bet combinations and their analysis"""
    __tablename__ = 'exotic_bet_results'
    
    id = Column(Integer, primary_key=True)
    optimization_run_id = Column(Integer, ForeignKey('optimization_runs.id'), nullable=False)
    
    # Bet details
    bet_type = Column(String(20), nullable=False)  # exacta, trifecta, superfecta
    combination = Column(JSON, nullable=False)  # [horse_id1, horse_id2, ...]
    combination_names = Column(JSON)  # [horse_name1, horse_name2, ...]
    
    # Probabilities and odds
    probability = Column(Float, nullable=False)
    payout_odds = Column(Float)
    
    # Expected value analysis
    expected_value = Column(Float, nullable=False)
    kelly_fraction = Column(Float)
    confidence_score = Column(Float)
    
    # Rankings
    ev_rank = Column(Integer)  # Rank by expected value
    probability_rank = Column(Integer)  # Rank by probability
    confidence_rank = Column(Integer)  # Rank by confidence
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    optimization_run = relationship("OptimizationRun", back_populates="exotic_bets")


class EVSignal(Base):
    """Model for EV signals - profitable betting opportunities"""
    __tablename__ = 'ev_signals'
    
    id = Column(Integer, primary_key=True)
    optimization_run_id = Column(Integer, ForeignKey('optimization_runs.id'), nullable=False)
    
    # Signal details
    signal_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    bet_type = Column(String(20), nullable=False)
    combination = Column(JSON, nullable=False)
    
    # Analysis metrics
    probability = Column(Float, nullable=False)
    expected_value = Column(Float, nullable=False)
    kelly_fraction = Column(Float)
    confidence_score = Column(Float)
    signal_strength = Column(Float)
    
    # Risk assessment
    risk_level = Column(String(20))  # LOW, MEDIUM, HIGH, VERY_HIGH
    recommended_stake = Column(Float)
    max_loss = Column(Float)
    potential_profit = Column(Float)
    
    # Signal status
    is_active = Column(Boolean, default=True)
    is_profitable = Column(Boolean, default=True)
    alert_sent = Column(Boolean, default=False)
    
    # Performance tracking (for backtesting)
    actual_result = Column(String(20))  # WIN, LOSS, PENDING
    actual_payout = Column(Float)
    roi = Column(Float)  # Return on investment
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    optimization_run = relationship("OptimizationRun", back_populates="ev_signals")


class OptimizationConfig(Base):
    """Model for storing optimization configurations"""
    __tablename__ = 'optimization_configs'
    
    id = Column(Integer, primary_key=True)
    config_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    
    # Probability calibration settings
    market_efficiency_factor = Column(Float, default=0.85)
    model_weight = Column(Float, default=0.7)
    market_weight = Column(Float, default=0.3)
    
    # Combination generation settings
    min_probability_threshold = Column(Float, default=0.001)
    max_exacta_combinations = Column(Integer, default=20)
    max_trifecta_combinations = Column(Integer, default=15)
    max_superfecta_combinations = Column(Integer, default=10)
    
    # EV signal settings
    min_ev_threshold = Column(Float, default=0.05)
    max_kelly_fraction = Column(Float, default=0.25)
    confidence_weight = Column(Float, default=0.35)
    
    # Risk management
    max_daily_exposure = Column(Float, default=1000.0)
    max_per_bet_exposure = Column(Float, default=100.0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PerformanceMetrics(Base):
    """Model for tracking optimization performance over time"""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, index=True)
    
    # Daily aggregates
    total_races_analyzed = Column(Integer, default=0)
    total_signals_generated = Column(Integer, default=0)
    profitable_signals = Column(Integer, default=0)
    
    # Performance metrics
    avg_expected_value = Column(Float, default=0.0)
    avg_signal_strength = Column(Float, default=0.0)
    avg_confidence_score = Column(Float, default=0.0)
    total_kelly_allocation = Column(Float, default=0.0)
    
    # ROI tracking (when actual results are available)
    total_bets_placed = Column(Integer, default=0)
    winning_bets = Column(Integer, default=0)
    total_wagered = Column(Float, default=0.0)
    total_returned = Column(Float, default=0.0)
    net_profit = Column(Float, default=0.0)
    roi_percentage = Column(Float, default=0.0)
    
    # Risk metrics
    max_drawdown = Column(Float, default=0.0)
    volatility = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# Database utility functions
class DatabaseManager:
    """Utility class for database operations"""
    
    def __init__(self, database_url: str = "sqlite:///exotic_bet_optimizer.db"):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def save_optimization_results(self, race_data: Dict[str, Any], 
                                optimization_results: Dict[str, Any]) -> int:
        """Save complete optimization results to database"""
        session = self.get_session()
        
        try:
            # Save or get race
            race = self._save_race(session, race_data)
            
            # Save optimization run
            optimization_run = self._save_optimization_run(session, race.id, optimization_results)
            
            # Save horses
            self._save_race_horses(session, race.id, race_data.get('horses', []))
            
            # Save exotic bet results
            self._save_exotic_bet_results(session, optimization_run.id, optimization_results)
            
            # Save EV signals
            self._save_ev_signals(session, optimization_run.id, optimization_results.get('top_opportunities', []))
            
            session.commit()
            return optimization_run.id
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def _save_race(self, session, race_data: Dict[str, Any]) -> Race:
        """Save or update race information"""
        race_id = race_data.get('race_id', 'unknown')
        
        race = session.query(Race).filter_by(race_id=race_id).first()
        
        if not race:
            race = Race(
                race_id=race_id,
                race_name=race_data.get('race_name'),
                track_name=race_data.get('track_name'),
                race_date=datetime.fromisoformat(race_data.get('race_date', datetime.now().isoformat())),
                race_time=race_data.get('race_time'),
                distance=race_data.get('distance'),
                surface=race_data.get('surface'),
                race_class=race_data.get('race_class'),
                purse=race_data.get('purse'),
                field_size=race_data.get('field_size', 0),
                weather_conditions=race_data.get('weather_conditions'),
                track_condition=race_data.get('track_condition')
            )
            session.add(race)
            session.flush()  # Get the ID
        
        return race
    
    def _save_optimization_run(self, session, race_id: int, 
                             results: Dict[str, Any]) -> OptimizationRun:
        """Save optimization run information"""
        summary_stats = results.get('summary_stats', {})
        
        optimization_run = OptimizationRun(
            race_id=race_id,
            total_combinations_analyzed=summary_stats.get('total_combinations_analyzed', 0),
            profitable_opportunities=results.get('profitable_signals', 0),
            profitability_rate=summary_stats.get('profitability_rate', 0.0),
            average_expected_value=summary_stats.get('average_expected_value', 0.0),
            max_expected_value=summary_stats.get('max_expected_value', 0.0),
            total_kelly_allocation=summary_stats.get('total_kelly_allocation', 0.0)
        )
        
        session.add(optimization_run)
        session.flush()  # Get the ID
        return optimization_run
    
    def _save_race_horses(self, session, race_id: int, horses_data: List[Dict[str, Any]]):
        """Save race horses information"""
        for horse_data in horses_data:
            horse = RaceHorse(
                race_id=race_id,
                horse_id=horse_data.get('id'),
                horse_name=horse_data.get('name'),
                jockey_name=horse_data.get('jockey'),
                trainer_name=horse_data.get('trainer'),
                final_odds=horse_data.get('odds'),
                original_win_probability=horse_data.get('win_probability'),
                calibrated_win_probability=horse_data.get('calibrated_win_prob'),
                place_probability=horse_data.get('place_prob'),
                show_probability=horse_data.get('show_prob'),
                form_rating=horse_data.get('form_rating'),
                speed_rating=horse_data.get('speed_rating'),
                class_rating=horse_data.get('class_rating')
            )
            session.add(horse)
    
    def _save_exotic_bet_results(self, session, optimization_run_id: int, 
                               results: Dict[str, Any]):
        """Save exotic bet results"""
        # This would need to be implemented based on the full results structure
        # For now, we'll skip detailed bet results
        pass
    
    def _save_ev_signals(self, session, optimization_run_id: int, 
                        signals: List[Dict[str, Any]]):
        """Save EV signals"""
        for signal in signals:
            ev_signal = EVSignal(
                optimization_run_id=optimization_run_id,
                bet_type=signal.get('bet_type'),
                combination=signal.get('combination'),
                probability=signal.get('probability'),
                expected_value=signal.get('expected_value'),
                kelly_fraction=signal.get('kelly_fraction'),
                confidence_score=signal.get('confidence_score'),
                signal_strength=signal.get('signal_strength'),
                risk_level=signal.get('risk_level'),
                recommended_stake=signal.get('recommended_stake')
            )
            session.add(ev_signal)
    
    def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get performance summary for the last N days"""
        session = self.get_session()
        
        try:
            from datetime import datetime, timedelta
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Get optimization runs from the period
            runs = session.query(OptimizationRun)\
                          .join(Race)\
                          .filter(Race.race_date >= start_date)\
                          .all()
            
            if not runs:
                return {'total_runs': 0}
            
            # Calculate summary statistics
            total_runs = len(runs)
            total_profitable_opportunities = sum(run.profitable_opportunities or 0 for run in runs)
            avg_profitability_rate = sum(run.profitability_rate or 0 for run in runs) / total_runs
            avg_expected_value = sum(run.average_expected_value or 0 for run in runs) / total_runs
            
            return {
                'period_days': days,
                'total_runs': total_runs,
                'total_profitable_opportunities': total_profitable_opportunities,
                'avg_profitability_rate': avg_profitability_rate,
                'avg_expected_value': avg_expected_value,
                'avg_opportunities_per_race': total_profitable_opportunities / total_runs if total_runs > 0 else 0
            }
            
        finally:
            session.close()


# Initialize database manager
def get_database_manager(database_url: str = "sqlite:///exotic_bet_optimizer.db") -> DatabaseManager:
    """Get initialized database manager"""
    db_manager = DatabaseManager(database_url)
    db_manager.create_tables()
    return db_manager


if __name__ == "__main__":
    # Test database creation
    db_manager = get_database_manager()
    print("Database tables created successfully!")
    
    # Test performance summary
    summary = db_manager.get_performance_summary()
    print(f"Performance summary: {summary}")