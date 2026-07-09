from jarvis.forecasting.classifier import ForecastClassifier


def test_forecast_classifier_flags_future_language():
    classifier = ForecastClassifier()
    result = classifier.classify("The system will reboot next week", metadata={"confidence_interval": (0.2, 0.8)})
    assert result.is_forecast
    assert result.knowledge_class == "forecast"
