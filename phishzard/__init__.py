"""PhishZard AI — biblioteca de detecção de phishing em e-mails."""

from .core import analyze_email
from .models import AnalysisReport, EmailMessage, HeuristicResult

__all__ = ["analyze_email", "EmailMessage", "AnalysisReport", "HeuristicResult"]
__version__ = "0.1.0"