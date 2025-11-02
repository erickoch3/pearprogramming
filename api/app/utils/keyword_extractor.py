"""Extract activity keywords from events for tweet searching."""

import re
from typing import List
from collections import Counter

from ..schemas.events import Event

# Common stop words to exclude from keyword extraction
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "must", "can", "this",
    "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "what", "which", "who", "whom", "whose", "where", "when", "why", "how",
    "all", "each", "every", "both", "few", "more", "most", "other", "some",
    "such", "only", "own", "same", "so", "than", "too", "very", "just",
    "now", "then", "here", "there", "where", "why", "how", "also", "about",
    "into", "through", "during", "before", "after", "above", "below", "up",
    "down", "out", "off", "over", "under", "again", "further", "once",
    "edinburgh", "join", "local", "bring", "free", "get", "see", "visit"
}

# Activity-related patterns to prioritize
ACTIVITY_PATTERNS = [
    r'\b(festival|fest|celebration)\w*\b',
    r'\b(concert|music|gig|performance|show|gig)\w*\b',
    r'\b(market|bazaar|fair|stall|vendor)\w*\b',
    r'\b(food|cuisine|dining|restaurant|cafe|brunch|dinner|breakfast|lunch)\w*\b',
    r'\b(exhibition|museum|gallery|art|display)\w*\b',
    r'\b(workshop|class|lesson|course|training)\w*\b',
    r'\b(meetup|meeting|gathering|social|event)\w*\b',
    r'\b(hike|walk|trail|outdoor|park|nature)\w*\b',
    r'\b(tour|guided|walking|exploration)\w*\b',
    r'\b(yoga|fitness|exercise|sport|sports)\w*\b',
    r'\b(comedy|theater|theatre|play|drama)\w*\b',
    r'\b(workshop|craft|artisan|handmade)\w*\b',
    r'\b(popup|pop-up|pop up)\w*\b',
    r'\b(live|entertainment|venue)\w*\b',
]


def extract_keywords_from_events(events: List[Event], max_keywords: int = 30) -> List[str]:
    """
    Extract activity-related keywords from a list of events.
    
    Prioritizes activity-related terms from event names and descriptions.
    Returns a list of keywords suitable for X API query building.
    
    Args:
        events: List of Event objects to extract keywords from
        max_keywords: Maximum number of keywords to return (default: 30)
    
    Returns:
        List of keyword strings, prioritized by relevance
    """
    if not events:
        return []
    
    # Collect all text from events
    all_text = []
    for event in events:
        if event.name:
            all_text.append(event.name.lower())
        if event.description:
            all_text.append(event.description.lower())
    
    combined_text = " ".join(all_text)
    
    # Extract words (handle multi-word terms by preserving common phrases)
    # First, identify and preserve multi-word activity terms
    preserved_phrases = []
    for pattern in ACTIVITY_PATTERNS:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        preserved_phrases.extend([m.lower() if isinstance(m, str) else m[0].lower() for m in matches])
    
    # Tokenize text, handling multi-word terms
    # Split on common delimiters but preserve quoted phrases
    words = re.findall(r'\b\w+\b', combined_text)
    
    # Combine single words and preserved phrases
    all_terms = words + preserved_phrases
    
    # Count term frequencies
    term_counts = Counter(all_terms)
    
    # Filter and score terms
    keywords = []
    keyword_scores = {}
    
    for term, count in term_counts.items():
        # Skip stop words and very short terms
        if term in STOP_WORDS or len(term) < 3:
            continue
        
        # Skip pure numbers
        if term.isdigit():
            continue
        
        # Calculate score: frequency + bonus for activity patterns
        score = count
        if any(re.search(pattern, term, re.IGNORECASE) for pattern in ACTIVITY_PATTERNS):
            score += 5  # Boost activity-related terms
        
        keyword_scores[term] = score
        keywords.append(term)
    
    # Sort by score and remove duplicates (preserving order)
    keywords_sorted = sorted(set(keywords), key=lambda k: keyword_scores.get(k, 0), reverse=True)
    
    # Handle multi-word terms from preserved phrases separately
    # Extract common 2-word phrases from text
    two_word_phrases = []
    for text in all_text:
        words_list = text.split()
        for i in range(len(words_list) - 1):
            phrase = f"{words_list[i]} {words_list[i+1]}"
            # Only keep phrases that seem activity-related
            if any(re.search(pattern, phrase, re.IGNORECASE) for pattern in ACTIVITY_PATTERNS):
                two_word_phrases.append(phrase.lower())
    
    two_word_counts = Counter(two_word_phrases)
    two_word_keywords = [
        phrase for phrase, count in two_word_counts.most_common(10)
        if count >= 1 and phrase not in STOP_WORDS
    ]
    
    # Combine single keywords with multi-word phrases, prioritizing phrases
    # Create a set of words from two-word phrases for efficient lookup
    two_word_words = set()
    for phrase in two_word_keywords:
        two_word_words.update(phrase.split())
    
    # Only add single keywords that don't already appear in the two-word phrases
    final_keywords = two_word_keywords + [
        k for k in keywords_sorted 
        if k not in two_word_keywords and k not in two_word_words
    ]
    
    # Limit to max_keywords
    return final_keywords[:max_keywords]


def extract_keywords_from_event(event: Event, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from a single event for filtering tweets.
    
    Args:
        event: Event object to extract keywords from
        max_keywords: Maximum number of keywords to return (default: 10)
    
    Returns:
        List of keyword strings relevant to the event
    """
    return extract_keywords_from_events([event], max_keywords=max_keywords)

