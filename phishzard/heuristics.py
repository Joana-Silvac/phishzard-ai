

import re
from typing import List
from urllib.parse import urlparse

from .models import EmailMessage, HeuristicResult

try:
    import tldextract
    _HAS_TLDEXTRACT = True
except ImportError:
    _HAS_TLDEXTRACT = False

try:
    import Levenshtein
    _HAS_LEVENSHTEIN = True
except ImportError:
    _HAS_LEVENSHTEIN = False


KNOWN_BRANDS = [
    "paypal", "google", "microsoft", "apple", "amazon",
    "netflix", "itau", "bradesco", "santander", "caixa", "nubank","linkedIn",
    "inter",
]

URGENCY_KEYWORDS = [
    "urgente", "imediatamente", "bloqueada", "bloqueado", "suspensa",
    "clique aqui", "verifique agora", "última chance", "expira hoje",
    "ação necessária", "confirme seus dados", "sua conta será",
]

URL_SHORTENERS = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "ow.ly"]


def _levenshtein_distance(a: str, b: str) -> int:
    
    if _HAS_LEVENSHTEIN:
        return Levenshtein.distance(a, b)

    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)

    previous_row = range(len(b) + 1)
    for i, char_a in enumerate(a):
        current_row = [i + 1]
        for j, char_b in enumerate(b):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (char_a != char_b)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def _extract_domain(domain: str) -> str:
    
    if _HAS_TLDEXTRACT:
        extracted = tldextract.extract(domain)
        return extracted.domain.lower()

    parts = domain.lower().split(".")
    if len(parts) >= 2:
        return parts[-2]
    return domain.lower()


def check_typosquatting(email: EmailMessage) -> HeuristicResult:
    
    sender_domain = email.sender.split("@")[-1] if "@" in email.sender else email.sender
    root = _extract_domain(sender_domain)

    for brand in KNOWN_BRANDS:
        if root == brand:
            continue  # é o domínio verdadeiro
        distance = _levenshtein_distance(root, brand)
        if 0 < distance <= 2 and len(root) >= 4:
            return HeuristicResult(
                name="typosquatting",
                score=0.9,
                reason=f"Domínio '{sender_domain}' é muito parecido com a marca '{brand}' "
                       f"(distância da edição: {distance})",
                triggered=True,
            )

    return HeuristicResult(name="typosquatting", score=0.0, reason="", triggered=False)


def check_urgency_language(email: EmailMessage) -> HeuristicResult:
    text = f"{email.subject} {email.body}".lower()
    found = [kw for kw in URGENCY_KEYWORDS if kw in text]

    if found:
        score = min(0.6, 0.2 * len(found))
        return HeuristicResult(
            name="urgency_language",
            score=score,
            reason=f"Linguagem de urgência detectada: {', '.join(found)}",
            triggered=True,
        )
    return HeuristicResult(name="urgency_language", score=0.0, reason="", triggered=False)


def check_suspicious_links(email: EmailMessage) -> HeuristicResult:
    reasons: List[str] = []
    max_score = 0.0

    for link in email.links:
        parsed = urlparse(link)
        host = parsed.netloc.lower()

        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
            reasons.append(f"Link usa IP direto em vez de domínio: {link}")
            max_score = max(max_score, 0.7)

        if any(shortener in host for shortener in URL_SHORTENERS):
            reasons.append(f"Link usa encurtador de URL: {link}")
            max_score = max(max_score, 0.5)

    return HeuristicResult(
        name="suspicious_links",
        score=max_score,
        reason="; ".join(reasons),
        triggered=bool(reasons),
    )


def check_display_name_mismatch(email: EmailMessage) -> HeuristicResult:
  
    if not email.display_name:
        return HeuristicResult(name="display_name_mismatch", score=0.0, reason="", triggered=False)

    display_lower = email.display_name.lower()
    sender_domain = email.sender.split("@")[-1] if "@" in email.sender else email.sender
    root = _extract_domain(sender_domain)

    for brand in KNOWN_BRANDS:
        if brand in display_lower and brand != root:
            return HeuristicResult(
                name="display_name_mismatch",
                score=0.85,
                reason=f"Nome exibido menciona '{brand}' mas o domínio real é '{sender_domain}'",
                triggered=True,
            )
    return HeuristicResult(name="display_name_mismatch", score=0.0, reason="", triggered=False)


def run_all_heuristics(email: EmailMessage) -> List[HeuristicResult]:
    return [
        check_typosquatting(email),
        check_urgency_language(email),
        check_suspicious_links(email),
        check_display_name_mismatch(email),
    ]