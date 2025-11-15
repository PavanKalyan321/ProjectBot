"""Format prediction table with selected models."""

def create_model_table(predictions, selected_models, model_names, ensemble=None):
    """
    Create a formatted prediction table with selected models.

    Args:
        predictions: List of model predictions [{"name": "XGBoost", "value": 2.35, ...}, ...]
        selected_models: List of model names to show ["Random Forest", "XGBoost", ...]
        model_names: Dict mapping model internal names to display names
        ensemble: Ensemble prediction dict (always shown last)

    Returns:
        str: Formatted table as string
    """

    # Filter predictions to only include selected models
    filtered_preds = [p for p in predictions if p.get("name") in selected_models]

    # Sort by selected_models order
    filtered_preds.sort(
        key=lambda x: selected_models.index(x.get("name"))
        if x.get("name") in selected_models
        else 999
    )

    # Build table
    lines = []

    # Header
    header = (
        "┌─────────────────────────┬────────────┬──────────┬────────────┬────────┬──────────┐"
    )
    lines.append(header)

    # Column headers
    header_row = (
        "│ Model                   │ Prediction │ Range    │ Confidence │ Weight │ Accuracy │"
    )
    lines.append(header_row)
    lines.append("├─────────────────────────┼────────────┼──────────┼────────────┼────────┼──────────┤")

    # Data rows
    for pred in filtered_preds:
        name = pred.get("name", "Unknown")
        value = pred.get("value", 0)
        range_str = pred.get("range", "N/A")
        confidence = pred.get("confidence", 0)
        weight = pred.get("weight", 1.0)
        accuracy = pred.get("accuracy", 0)

        # Format: Model name (left-aligned, 23 chars), prediction (right-aligned, 10 chars),
        # range (center, 8 chars), confidence (right, 10 chars), weight (right, 6 chars),
        # accuracy (right, 8 chars)
        row = (
            f"│ {name:<23} │ {value:>8.2f}x │ {range_str:^8} │ "
            f"{confidence:>9.0f}% │ {weight:>6.3f} │ {accuracy:>7.2f}% │"
        )
        lines.append(row)

    # Separator before ensemble
    lines.append("├─────────────────────────┼────────────┼──────────┼────────────┼────────┼──────────┤")

    # Ensemble row (always shown)
    if ensemble:
        ens_name = ensemble.get("name", "ENSEMBLE")
        ens_value = ensemble.get("value", 0)
        ens_range = ensemble.get("range", "N/A")
        ens_confidence = ensemble.get("confidence", 0)
        ens_weight = ensemble.get("weight", 1.0)
        ens_accuracy = ensemble.get("accuracy", 0)

        ens_row = (
            f"│ {ens_name:<23} │ {ens_value:>8.2f}x │ {ens_range:^8} │ "
            f"{ens_confidence:>9.0f}% │ {ens_weight:>6.3f} │ {ens_accuracy:>7.2f}% │"
        )
        lines.append(ens_row)

    # Footer
    footer = (
        "└─────────────────────────┴────────────┴──────────┴────────────┴────────┴──────────┘"
    )
    lines.append(footer)

    return "\n".join(lines)


def create_simple_model_table(models_data, selected_models):
    """
    Create a simpler table format with just the essentials.

    Args:
        models_data: List of {"name": "XGBoost", "prediction": 2.35, "confidence": 72, ...}
        selected_models: List of model names to show

    Returns:
        str: Formatted table
    """

    # Filter and sort
    filtered = [m for m in models_data if m.get("name") in selected_models]
    filtered.sort(key=lambda x: selected_models.index(x.get("name")) if x.get("name") in selected_models else 999)

    lines = []
    lines.append("┌──────────────────┬────────────┬────────────┐")
    lines.append("│ Model            │ Prediction │ Confidence │")
    lines.append("├──────────────────┼────────────┼────────────┤")

    for model in filtered:
        name = model.get("name", "Unknown")
        pred = model.get("prediction", 0)
        conf = model.get("confidence", 0)
        row = f"│ {name:<16} │ {pred:>10.2f}x │ {conf:>10.0f}% │"
        lines.append(row)

    # Add ensemble if available
    if any(m.get("is_ensemble") for m in models_data):
        lines.append("├──────────────────┼────────────┼────────────┤")
        for model in models_data:
            if model.get("is_ensemble"):
                name = "ENSEMBLE"
                pred = model.get("prediction", 0)
                conf = model.get("confidence", 0)
                row = f"│ {name:<16} │ {pred:>10.2f}x │ {conf:>10.0f}% │"
                lines.append(row)

    lines.append("└──────────────────┴────────────┴────────────┘")

    return "\n".join(lines)


def get_recommendation_emoji(prediction):
    """Get emoji based on prediction value."""
    if prediction >= 3.0:
        return "🟢"  # Green - high confidence
    elif prediction >= 2.0:
        return "🟡"  # Yellow - medium
    elif prediction >= 1.5:
        return "🟠"  # Orange - low
    else:
        return "🔴"  # Red - very low


def format_models_summary(predictions, selected_models):
    """
    Create a one-line summary of selected models.

    Args:
        predictions: List of model predictions
        selected_models: Selected models to show

    Returns:
        str: Summary line
    """
    filtered = [p for p in predictions if p.get("name") in selected_models]

    if not filtered:
        return "No models selected"

    summary_parts = []
    for pred in filtered[:3]:  # Show top 3
        name = pred.get("name", "?")
        value = pred.get("value", 0)
        summary_parts.append(f"{name}: {value:.2f}x")

    if len(filtered) > 3:
        summary_parts.append(f"... +{len(filtered) - 3} more")

    return " | ".join(summary_parts)
