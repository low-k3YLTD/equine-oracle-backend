"""
Implementation Guide for Equine Oracle Backend Integration
=========================================================

This guide provides step-by-step instructions for integrating the Exotic Bet Optimizer
into your existing equine-oracle-backend project.

## Quick Integration Steps

### 1. File Placement
Copy these files into your equine-oracle-backend project:

```
equine-oracle-backend/
├── exotic_betting/                    # New directory
│   ├── __init__.py                   # Empty file
│   ├── exotic_bet_optimizer.py       # Core optimization logic
│   ├── database_models.py            # Database schema
│   ├── config.py                     # Configuration management
│   └── test_and_demo.py             # Tests and examples
├── api/
│   ├── exotic_bet_api.py             # API endpoints (integrate with existing routes)
├── requirements.txt                   # Add new dependencies
└── README.md                         # Update with new features
```

### 2. Update Dependencies
Add to your requirements.txt:
```
numpy>=1.21.0
pandas>=1.3.0
sqlalchemy>=1.4.0
flask-cors>=3.0.0
scipy>=1.7.0
```

### 3. Database Integration
If using existing database:
```python
# In your main app.py or database setup
from exotic_betting.database_models import Base

# Add exotic betting tables to your existing database
Base.metadata.create_all(bind=your_engine)
```

### 4. API Integration
Add to your main Flask app:
```python
from api.exotic_bet_api import exotic_bp

# Register the exotic betting blueprint
app.register_blueprint(exotic_bp)
```

### 5. Environment Variables
Add to your .env file:
```bash
# Exotic Bet Optimizer Configuration
MIN_EV_THRESHOLD=0.05
MAX_KELLY_FRACTION=0.25
MARKET_EFFICIENCY_FACTOR=0.85
MODEL_WEIGHT=0.7
MARKET_WEIGHT=0.3
```

## API Usage Examples

### Optimize Race for Exotic Bets
```python
import requests

race_data = {
    "race_id": "BEL_2025_R01",
    "horses": [
        {
            "id": 1,
            "name": "Thunder Bolt",
            "win_probability": 0.25,
            "odds": 4.0,
            "jockey": "J. Rodriguez",
            "trainer": "B. Smith",
            "form_rating": 92,
            "speed_rating": 95,
            "class_rating": 90
        },
        # ... more horses
    ]
}

response = requests.post('http://localhost:5000/api/v1/exotic/optimize', json=race_data)
results = response.json()

# Get top profitable opportunities
opportunities = results['data']['top_opportunities']
for opp in opportunities[:5]:
    print(f"{opp['bet_type']}: {opp['combination']} - EV: {opp['expected_value']:.3f}")
```

### Generate Specific Bet Type
```python
# Generate only trifecta combinations
response = requests.post('http://localhost:5000/api/v1/exotic/combinations/trifecta', 
                        json={"horses": horse_data, "max_combinations": 10})
```

### Get EV Signals
```python
# Get profitable betting signals
response = requests.post('http://localhost:5000/api/v1/exotic/signals', json={"horses": horse_data})
signals = response.json()['signals']
```

## Testing the Integration

Run the comprehensive test:
```bash
python exotic_betting/test_and_demo.py
```

Expected output should show:
- ✅ All unit tests passed
- 🏇 Demo with realistic race data
- 📊 Profitable opportunities identified
- 💾 Database storage successful

## Performance Considerations

### Production Optimizations
1. **Database**: Use PostgreSQL with connection pooling
2. **Caching**: Implement Redis for frequently accessed probability calculations
3. **Background Processing**: Use Celery for heavy optimization tasks
4. **Monitoring**: Add metrics for optimization performance

### Scaling Recommendations
- Limit analysis to top 8-10 horses per race
- Implement probability caching for horses with stable form
- Use background tasks for non-critical optimizations
- Monitor memory usage for large field sizes

## Troubleshooting

### Common Issues
1. **Slow optimization**: Reduce max_combinations parameters
2. **No profitable signals**: Lower min_ev_threshold
3. **Database errors**: Check connection string and permissions
4. **Memory usage**: Limit field size analysis

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Success Metrics

After integration, monitor these KPIs:
- **Profitability Rate**: % of races with profitable opportunities
- **Average EV**: Expected value of recommended bets  
- **Signal Quality**: Confidence scores of generated signals
- **Processing Time**: Optimization speed per race
- **User Adoption**: Usage of exotic betting features

## Next Steps

1. **Deploy** the integration to your development environment
2. **Test** with historical race data
3. **Monitor** performance and adjust parameters
4. **Expand** with additional exotic bet types (Pick 3, Pick 4, etc.)
5. **Integrate** with your existing UI components

The Exotic Bet Optimizer is now ready to provide immediate value through the three core recommendations:
✅ Joint probability calibration
✅ Exotic combination generation  
✅ EV signal generation
"""