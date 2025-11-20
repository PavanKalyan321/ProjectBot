"""
Training Script for 30-Model Ensemble and Flow Predictor
Trains all models on historical data
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from core.advanced_ml_ensemble import AdvancedMLEnsemble
from core.flow_predictor import FlowPredictor


def main():
    """Train all models."""
    print("\n" + "="*80)
    print("ADVANCED ML ENSEMBLE TRAINING")
    print("="*80 + "\n")

    # Paths
    rounds_csv = "backend/aviator_rounds_history.csv"

    # Check if data exists
    if not os.path.exists(rounds_csv):
        print(f"ERROR: Historical data not found at {rounds_csv}")
        print("Please ensure you have historical data before training.")
        return False

    # 1. Train 30-Model Ensemble
    print("\n[STEP 1/2] Training 30-Model Ensemble...")
    print("-" * 80)

    ensemble = AdvancedMLEnsemble()
    success = ensemble.train_all_models(csv_file=rounds_csv, min_samples=100)

    if not success:
        print("\n[ERROR] Failed to train ensemble models")
        return False

    print("\n[SUCCESS] Ensemble training complete!")

    # 2. Train Flow Predictor
    print("\n[STEP 2/2] Training Flow Prediction System...")
    print("-" * 80)

    flow_predictor = FlowPredictor()
    success = flow_predictor.train(csv_file=rounds_csv, min_samples=200)

    if not success:
        print("\n[ERROR] Failed to train flow predictor")
        return False

    print("\n[SUCCESS] Flow predictor training complete!")

    # Summary
    print("\n" + "="*80)
    print("TRAINING SUMMARY")
    print("="*80)
    print(f"✓ Ensemble Models: {len(ensemble.models)} models trained")
    print(f"✓ Flow Predictor: Trained successfully")
    print(f"✓ All models saved to disk")
    print("\nNext steps:")
    print("  1. Run the dashboard: python run_advanced_dashboard.py")
    print("  2. View predictions at: http://localhost:5002")
    print("="*80 + "\n")

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
