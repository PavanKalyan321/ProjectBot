"""
Model Training Script
Run this script to train ML models on historical CSV data
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.ml_models import AviatorMLModels


def main():
    """Train all ML models on historical data."""
    print("\n" + "="*80)
    print("AVIATOR ML MODEL TRAINING")
    print("="*80)

    # Initialize models
    ml_models = AviatorMLModels(models_dir='models')

    # Train on historical data
    csv_file = 'aviator_rounds_history.csv'

    if not os.path.exists(csv_file):
        print(f"\nERROR: CSV file not found: {csv_file}")
        print("   Please ensure you have collected historical data first.")
        print("   Run the bot in observation mode to collect data.\n")
        return

    success = ml_models.train_models(csv_file=csv_file, min_samples=100)

    if success:
        print("\nSUCCESS!")
        print(f"   Models saved to: {ml_models.models_dir}/")
        print("\nNext steps:")
        print("  1. Run the bot: python bot_modular.py")
        print("  2. Models will automatically load and make predictions")
        print(f"  3. To retrain later, run: python train_models.py\n")
    else:
        print("\nTRAINING FAILED")
        print("   Check the errors above and ensure:")
        print("   - CSV file has valid data")
        print("   - At least 100 rounds of history")
        print("   - Required dependencies installed\n")


if __name__ == '__main__':
    main()
