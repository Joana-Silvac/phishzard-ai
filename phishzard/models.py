

from dataclasses import dataclass, field
from typing import List


@dataclass
class EmailMessage:
   

    subject: str
    body: str
    sender: str
    display_name: str = ""
    links: List[str] = field(default_factory=list)
    headers: dict = field(default_factory=dict)


@dataclass
class HeuristicResult:
    

    name: str
    score: float
    reason: str
    triggered: bool


@dataclass
class AnalysisReport:
    
    risk_score: float
    risk_level: str
    reasons: List[str] = field(default_factory=list)
    details: List[HeuristicResult] = field(default_factory=list)