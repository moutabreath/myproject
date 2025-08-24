from dataclasses import dataclass


@dataclass
class ForecastResult:
    prediction: bool
    confidence: float