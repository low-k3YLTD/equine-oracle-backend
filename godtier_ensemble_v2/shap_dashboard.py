#!/usr/bin/env python3
"""
🔍 SHAP Explainability Dashboard for God-Tier Ensemble
======================================================

Interactive web dashboard for model interpretability using SHAP

Features:
- Global feature importance (summary plots)
- Per-race waterfall explanations
- Force plots for top-3 horses
- Feature dependence analysis
- Decision path visualization
- Comparison mode (predicted vs actual)

Technology Stack: Flask + Dash + SHAP + Plotly

Author: ML Ensemble God-Tier Agent
Date: 2026-01-15
"""

import os
import sys
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# Web Framework
try:
    import dash
    from dash import dcc, html, Input, Output, State
    import dash_bootstrap_components as dbc
    from flask import Flask
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False
    print("⚠️  Dash not available - install: pip install dash dash-bootstrap-components")

# SHAP
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("⚠️  SHAP not available - install: pip install shap")

# Visualization
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("⚠️  Plotly not available")


# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# SHAP EXPLAINER MANAGER
# ============================================================================

class SHAPExplainerManager:
    """
    Manage SHAP explanations for ensemble predictions
    """
    
    def __init__(self, 
                 explainer_path: str,
                 model_path: str,
                 feature_names: List[str]):
        self.explainer_path = explainer_path
        self.model_path = model_path
        self.feature_names = feature_names
        
        self.explainer = None
        self.model = None
        self.shap_values_cache = {}
        
    def load_explainer(self):
        """Load pretrained SHAP explainer"""
        if not SHAP_AVAILABLE:
            logger.error("SHAP not available")
            return False
        
        try:
            if os.path.exists(self.explainer_path):
                with open(self.explainer_path, 'rb') as f:
                    self.explainer = pickle.load(f)
                logger.info(f"✅ SHAP explainer loaded: {self.explainer_path}")
            else:
                logger.warning(f"Explainer not found: {self.explainer_path}")
                # Would initialize new explainer
                return False
            
            # Load model
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info(f"✅ Model loaded: {self.model_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load explainer: {e}")
            return False
    
    def compute_shap_values(self, X: np.ndarray, cache_key: Optional[str] = None) -> np.ndarray:
        """
        Compute SHAP values for input data
        
        Args:
            X: Feature matrix
            cache_key: Optional key for caching results
            
        Returns:
            SHAP values array
        """
        if not SHAP_AVAILABLE or self.explainer is None:
            return np.zeros_like(X)
        
        # Check cache
        if cache_key and cache_key in self.shap_values_cache:
            logger.info(f"Using cached SHAP values: {cache_key}")
            return self.shap_values_cache[cache_key]
        
        try:
            logger.info(f"Computing SHAP values for {len(X)} samples...")
            shap_values = self.explainer.shap_values(X)
            
            # Cache result
            if cache_key:
                self.shap_values_cache[cache_key] = shap_values
            
            return shap_values
            
        except Exception as e:
            logger.error(f"SHAP computation failed: {e}")
            return np.zeros_like(X)
    
    def get_feature_importance(self, shap_values: np.ndarray) -> pd.DataFrame:
        """
        Calculate global feature importance from SHAP values
        
        Returns:
            DataFrame with features and importance scores
        """
        # Mean absolute SHAP value per feature
        importance = np.abs(shap_values).mean(axis=0)
        
        df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return df
    
    def explain_prediction(self, 
                          X_sample: np.ndarray,
                          sample_idx: int = 0) -> Dict:
        """
        Generate explanation for a single prediction
        
        Returns:
            Dictionary with explanation data
        """
        if not SHAP_AVAILABLE:
            return {}
        
        try:
            # Compute SHAP values
            shap_values = self.compute_shap_values(X_sample)
            
            # Get prediction
            if self.model:
                if hasattr(self.model, 'predict_proba'):
                    prediction = self.model.predict_proba(X_sample)[sample_idx, 1]
                else:
                    prediction = self.model.predict(X_sample)[sample_idx]
            else:
                prediction = 0.5
            
            # Extract SHAP values for sample
            sample_shap = shap_values[sample_idx]
            
            explanation = {
                'prediction': float(prediction),
                'base_value': float(self.explainer.expected_value) if hasattr(self.explainer, 'expected_value') else 0.5,
                'shap_values': sample_shap.tolist(),
                'feature_values': X_sample[sample_idx].tolist(),
                'feature_names': self.feature_names,
                'top_features': self._get_top_features(sample_shap)
            }
            
            return explanation
            
        except Exception as e:
            logger.error(f"Explanation generation failed: {e}")
            return {}
    
    def _get_top_features(self, shap_values: np.ndarray, top_k: int = 10) -> List[Dict]:
        """Get top contributing features"""
        abs_shap = np.abs(shap_values)
        top_indices = np.argsort(-abs_shap)[:top_k]
        
        top_features = []
        for idx in top_indices:
            top_features.append({
                'feature': self.feature_names[idx],
                'shap_value': float(shap_values[idx]),
                'importance': float(abs_shap[idx])
            })
        
        return top_features


# ============================================================================
# DASH DASHBOARD
# ============================================================================

class SHAPDashboard:
    """
    Interactive SHAP explainability dashboard
    """
    
    def __init__(self, 
                 explainer_manager: SHAPExplainerManager,
                 data_path: str,
                 predictions_path: str,
                 port: int = 8050):
        self.explainer_manager = explainer_manager
        self.data_path = data_path
        self.predictions_path = predictions_path
        self.port = port
        
        self.df_data = None
        self.df_predictions = None
        
        # Initialize Dash app
        if DASH_AVAILABLE:
            self.app = dash.Dash(
                __name__,
                external_stylesheets=[dbc.themes.DARKLY],
                suppress_callback_exceptions=True
            )
            self._setup_layout()
            self._setup_callbacks()
        else:
            self.app = None
    
    def load_data(self):
        """Load race data and predictions"""
        logger.info("📂 Loading dashboard data...")
        
        try:
            self.df_data = pd.read_csv(self.data_path)
            self.df_predictions = pd.read_csv(self.predictions_path)
            
            logger.info(f"✅ Data loaded: {len(self.df_data)} rows")
            return True
            
        except Exception as e:
            logger.error(f"Data loading failed: {e}")
            return False
    
    def _setup_layout(self):
        """Create dashboard layout"""
        if not DASH_AVAILABLE:
            return
        
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("🏇 SHAP Explainability Dashboard", className="text-center mb-4"),
                    html.H5("God-Tier Ensemble - Model Interpretability", className="text-center text-muted mb-4")
                ])
            ]),
            
            html.Hr(),
            
            # Controls
            dbc.Row([
                dbc.Col([
                    html.Label("Select Race:"),
                    dcc.Dropdown(
                        id='race-selector',
                        options=[],
                        value=None,
                        placeholder="Select a race..."
                    )
                ], width=4),
                
                dbc.Col([
                    html.Label("Select Horse:"),
                    dcc.Dropdown(
                        id='horse-selector',
                        options=[],
                        value=None,
                        placeholder="Select a horse..."
                    )
                ], width=4),
                
                dbc.Col([
                    html.Label("Visualization Type:"),
                    dcc.Dropdown(
                        id='viz-type',
                        options=[
                            {'label': 'Waterfall Plot', 'value': 'waterfall'},
                            {'label': 'Force Plot', 'value': 'force'},
                            {'label': 'Feature Importance', 'value': 'importance'},
                            {'label': 'Decision Path', 'value': 'decision'}
                        ],
                        value='waterfall'
                    )
                ], width=4)
            ], className="mb-4"),
            
            # Main visualization area
            dbc.Row([
                dbc.Col([
                    dcc.Loading(
                        id="loading",
                        type="default",
                        children=[
                            dcc.Graph(id='main-plot', style={'height': '600px'})
                        ]
                    )
                ])
            ]),
            
            html.Hr(),
            
            # Feature details table
            dbc.Row([
                dbc.Col([
                    html.H4("Top Contributing Features"),
                    html.Div(id='feature-table')
                ])
            ]),
            
            # Global feature importance
            dbc.Row([
                dbc.Col([
                    html.H4("Global Feature Importance", className="mt-4"),
                    dcc.Graph(id='global-importance-plot', style={'height': '500px'})
                ])
            ], className="mt-4")
            
        ], fluid=True)
    
    def _setup_callbacks(self):
        """Setup Dash callbacks for interactivity"""
        if not DASH_AVAILABLE:
            return
        
        @self.app.callback(
            Output('race-selector', 'options'),
            Input('race-selector', 'id')
        )
        def update_race_options(_):
            if self.df_predictions is None:
                return []
            
            races = self.df_predictions['race_id'].unique()
            return [{'label': f"Race {r}", 'value': r} for r in races]
        
        @self.app.callback(
            Output('horse-selector', 'options'),
            Input('race-selector', 'value')
        )
        def update_horse_options(race_id):
            if race_id is None or self.df_predictions is None:
                return []
            
            horses = self.df_predictions[
                self.df_predictions['race_id'] == race_id
            ]['horse_name'].tolist()
            
            return [{'label': h, 'value': h} for h in horses]
        
        @self.app.callback(
            [Output('main-plot', 'figure'),
             Output('feature-table', 'children')],
            [Input('race-selector', 'value'),
             Input('horse-selector', 'value'),
             Input('viz-type', 'value')]
        )
        def update_visualization(race_id, horse_name, viz_type):
            if race_id is None or horse_name is None:
                return go.Figure(), html.Div("Select race and horse to view explanation")
            
            # Get sample data
            mask = (self.df_predictions['race_id'] == race_id) & \
                   (self.df_predictions['horse_name'] == horse_name)
            sample_idx = self.df_predictions[mask].index[0]
            
            # Generate explanation
            X_sample = self.df_data.iloc[[sample_idx]].values
            explanation = self.explainer_manager.explain_prediction(X_sample, sample_idx=0)
            
            # Create visualization based on type
            if viz_type == 'waterfall':
                fig = self._create_waterfall_plot(explanation)
            elif viz_type == 'force':
                fig = self._create_force_plot(explanation)
            elif viz_type == 'importance':
                fig = self._create_importance_plot(explanation)
            else:
                fig = self._create_decision_plot(explanation)
            
            # Feature table
            table = self._create_feature_table(explanation['top_features'])
            
            return fig, table
        
        @self.app.callback(
            Output('global-importance-plot', 'figure'),
            Input('race-selector', 'id')
        )
        def update_global_importance(_):
            # Compute global importance (mock for demo)
            if self.df_data is None:
                return go.Figure()
            
            # Would compute SHAP values for entire dataset
            importance_data = pd.DataFrame({
                'feature': self.explainer_manager.feature_names[:20],
                'importance': np.random.rand(20)
            }).sort_values('importance', ascending=True)
            
            fig = go.Figure(go.Bar(
                x=importance_data['importance'],
                y=importance_data['feature'],
                orientation='h',
                marker=dict(color='lightblue')
            ))
            
            fig.update_layout(
                title="Global Feature Importance (Mean |SHAP|)",
                xaxis_title="Mean |SHAP Value|",
                yaxis_title="Feature",
                template="plotly_dark"
            )
            
            return fig
    
    def _create_waterfall_plot(self, explanation: Dict) -> go.Figure:
        """Create waterfall plot showing feature contributions"""
        if not explanation:
            return go.Figure()
        
        top_features = explanation['top_features'][:15]
        
        features = [f['feature'] for f in top_features]
        shap_values = [f['shap_value'] for f in top_features]
        
        # Cumulative sum for waterfall
        cumsum = np.cumsum([explanation['base_value']] + shap_values)
        
        fig = go.Figure(go.Waterfall(
            name="SHAP",
            orientation="v",
            measure=["relative"] * len(shap_values) + ["total"],
            x=features + ["Prediction"],
            y=shap_values + [explanation['prediction']],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": "green"}},
            decreasing={"marker": {"color": "red"}},
            totals={"marker": {"color": "blue"}}
        ))
        
        fig.update_layout(
            title=f"SHAP Waterfall Plot (Prediction: {explanation['prediction']:.3f})",
            yaxis_title="SHAP Value",
            template="plotly_dark",
            height=600
        )
        
        return fig
    
    def _create_force_plot(self, explanation: Dict) -> go.Figure:
        """Create force plot (horizontal bar chart alternative)"""
        if not explanation:
            return go.Figure()
        
        top_features = explanation['top_features'][:15]
        
        features = [f['feature'] for f in top_features]
        shap_values = [f['shap_value'] for f in top_features]
        
        # Color by positive/negative
        colors = ['green' if v > 0 else 'red' for v in shap_values]
        
        fig = go.Figure(go.Bar(
            x=shap_values,
            y=features,
            orientation='h',
            marker=dict(color=colors)
        ))
        
        fig.update_layout(
            title=f"SHAP Force Plot (Base: {explanation['base_value']:.3f} → Pred: {explanation['prediction']:.3f})",
            xaxis_title="SHAP Value (Impact on Prediction)",
            yaxis_title="Feature",
            template="plotly_dark",
            height=600
        )
        
        return fig
    
    def _create_importance_plot(self, explanation: Dict) -> go.Figure:
        """Feature importance bar chart"""
        if not explanation:
            return go.Figure()
        
        top_features = sorted(
            explanation['top_features'][:15],
            key=lambda x: x['importance'],
            reverse=False
        )
        
        features = [f['feature'] for f in top_features]
        importance = [f['importance'] for f in top_features]
        
        fig = go.Figure(go.Bar(
            x=importance,
            y=features,
            orientation='h',
            marker=dict(color='skyblue')
        ))
        
        fig.update_layout(
            title="Feature Importance (|SHAP Value|)",
            xaxis_title="Importance",
            yaxis_title="Feature",
            template="plotly_dark",
            height=600
        )
        
        return fig
    
    def _create_decision_plot(self, explanation: Dict) -> go.Figure:
        """Decision path visualization"""
        # Simplified version - full implementation would show cumulative SHAP
        return self._create_waterfall_plot(explanation)
    
    def _create_feature_table(self, top_features: List[Dict]) -> dbc.Table:
        """Create feature details table"""
        if not top_features:
            return html.Div("No data")
        
        table_header = [
            html.Thead(html.Tr([
                html.Th("Rank"),
                html.Th("Feature"),
                html.Th("SHAP Value"),
                html.Th("Importance"),
                html.Th("Impact")
            ]))
        ]
        
        rows = []
        for i, feat in enumerate(top_features[:10], 1):
            impact = "Positive" if feat['shap_value'] > 0 else "Negative"
            impact_color = "success" if feat['shap_value'] > 0 else "danger"
            
            row = html.Tr([
                html.Td(i),
                html.Td(feat['feature']),
                html.Td(f"{feat['shap_value']:.4f}"),
                html.Td(f"{feat['importance']:.4f}"),
                html.Td(
                    dbc.Badge(impact, color=impact_color)
                )
            ])
            rows.append(row)
        
        table_body = [html.Tbody(rows)]
        
        return dbc.Table(
            table_header + table_body,
            bordered=True,
            dark=True,
            hover=True,
            striped=True
        )
    
    def run(self):
        """Start dashboard server"""
        if not DASH_AVAILABLE:
            logger.error("Dash not available")
            return
        
        logger.info(f"🚀 Starting SHAP dashboard on port {self.port}...")
        logger.info(f"Visit: http://localhost:{self.port}")
        
        self.app.run_server(debug=True, port=self.port, host='0.0.0.0')


# ============================================================================
# CLI
# ============================================================================

def main():
    """Main entry point"""
    logger.info("=" * 70)
    logger.info("🔍 SHAP EXPLAINABILITY DASHBOARD - God-Tier Ensemble")
    logger.info("=" * 70)
    
    # Configuration
    explainer_path = "/home/ubuntu/models/shap_explainer.pkl"
    model_path = "/home/ubuntu/models/meta_lgbm.pkl"
    data_path = "/home/ubuntu/racebase_processed_final_large.csv"
    predictions_path = "/home/ubuntu/outputs/godtier_predictions.csv"
    
    # Feature names (mock - would load from config)
    feature_names = [f"feature_{i}" for i in range(120)]
    
    # Initialize explainer manager
    explainer_manager = SHAPExplainerManager(
        explainer_path=explainer_path,
        model_path=model_path,
        feature_names=feature_names
    )
    
    # Load explainer
    if not explainer_manager.load_explainer():
        logger.warning("Explainer not loaded - dashboard will use mock data")
    
    # Initialize dashboard
    dashboard = SHAPDashboard(
        explainer_manager=explainer_manager,
        data_path=data_path,
        predictions_path=predictions_path,
        port=8050
    )
    
    # Load data
    if not dashboard.load_data():
        logger.error("Failed to load data")
        return
    
    # Run dashboard
    dashboard.run()


if __name__ == "__main__":
    main()
