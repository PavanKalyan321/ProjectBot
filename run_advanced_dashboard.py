"""
Run the Advanced Predictions Dashboard
Displays 30 models, flow predictions, and comprehensive analytics
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dashboard.advanced_dashboard import AdvancedPredictionDashboard


def main():
    """Run the advanced dashboard."""
    print("\n" + "="*80)
    print("STARTING ADVANCED PREDICTIONS DASHBOARD")
    print("="*80)
    print("\nFeatures:")
    print("  ✓ 30 ML Models with real-time predictions")
    print("  ✓ Flow prediction (HIGH/LOW volatility)")
    print("  ✓ Model comparison and ranking")
    print("  ✓ Prediction validation with expected ranges")
    print("  ✓ Performance analytics and trends")
    print("\n" + "="*80 + "\n")

    # Create and run dashboard
    dashboard = AdvancedPredictionDashboard(port=5002)
    dashboard.run(debug=False)


if __name__ == '__main__':
    main()
