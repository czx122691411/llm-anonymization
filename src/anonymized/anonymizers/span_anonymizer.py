"""
Span-based Anonymizer using NER for precise PII masking.

This module implements an anonymizer that uses Named Entity Recognition (NER)
to detect and mask precise spans of personally identifiable information.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import re

from src.anonymized.anonymizers.anonymizer import Anonymizer
from src.configs import AnonymizerConfig
from src.reddit.reddit_types import Profile, Comment


@dataclass
class EntitySpan:
    """Represents a detected PII entity with its span."""
    entity_type: str  # e.g., PERSON, LOCATION, ORG
    text: str  # The actual entity text
    start: int  # Character start position
    end: int  # Character end position
    confidence: float  # Detection confidence 0-1


class SpanAnonymizer(Anonymizer):
    """
    Span-based anonymizer using NER for precise entity detection and masking.

    This approach:
    1. Detects PII entities using NER model
    2. Applies different masking strategies (replace, generalize, remove)
    3. Preserves non-PII text exactly as-is
    """

    # Entity types that correspond to PII categories
    PII_ENTITY_TYPES = {
        "PERSON",  # Names
        "LOCATION", "GPE", "LOC",  # Locations
        "ORG",  # Organizations
        "DATE", "TIME",  # Temporal info
        "EMAIL", "PHONE", "URL", "IP_ADDRESS",  # Direct identifiers
        "NORP",  # Nationalities, religious, political groups
        "CARDINAL", "ORDINAL",  # Numbers that might be ages
    }

    # Mapping from entity types to PII categories
    ENTITY_TO_PII = {
        "PERSON": "name",
        "LOCATION": "location",
        "GPE": "location",
        "LOC": "location",
        "ORG": "organization",
        "DATE": "date",
        "TIME": "time",
        "EMAIL": "email",
        "PHONE": "phone",
        "URL": "url",
        "IP_ADDRESS": "ip",
        "NORP": "demographic",
        "CARDINAL": "number",
        "ORDINAL": "number",
    }

    def __init__(self, cfg: AnonymizerConfig):
        self.cfg = cfg
        self.replacement_type = cfg.replacement_type
        self.model_dir = cfg.model_dir

        # Load NER model if needed
        self.ner_model = None
        self._load_ner_model()

    def _load_ner_model(self):
        """Load the NER model for entity detection."""
        try:
            # Try to load from spaCy
            import spacy
            model_name = "en_core_web_sm"  # Fast, good for web text
            try:
                self.ner_model = spacy.load(model_name)
            except OSError:
                # Fallback to en_core_web_sm
                self.ner_model = spacy.load("en_core_web_sm")
        except ImportError:
            print("Warning: spaCy not installed. Using regex-based entity detection.")
            self.ner_model = None

    def detect_entities(self, text: str) -> List[EntitySpan]:
        """
        Detect PII entities in the given text.

        Args:
            text: Input text to analyze

        Returns:
            List of detected entity spans
        """
        entities = []

        if self.ner_model is not None:
            # Use spaCy NER
            doc = self.ner_model(text)
            for ent in doc.ents:
                if ent.label_ in self.PII_ENTITY_TYPES:
                    entities.append(EntitySpan(
                        entity_type=ent.label_,
                        text=ent.text,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=1.0,  # spaCy doesn't give confidence
                    ))
        else:
            # Fallback: Regex-based detection
            entities.extend(self._regex_detect_entities(text))

        # Post-process: Remove overlapping entities (keep longer)
        entities = self._remove_overlaps(entities)

        return entities

    def _regex_detect_entities(self, text: str) -> List[EntitySpan]:
        """Regex-based entity detection as fallback."""
        entities = []

        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            entities.append(EntitySpan(
                entity_type="EMAIL",
                text=match.group(),
                start=match.start(),
                end=match.end(),
                confidence=0.9,
            ))

        # Phone pattern (various formats)
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
        for match in re.finditer(phone_pattern, text):
            entities.append(EntitySpan(
                entity_type="PHONE",
                text=match.group(),
                start=match.start(),
                end=match.end(),
                confidence=0.8,
            ))

        # URL pattern
        url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?/=]*)'
        for match in re.finditer(url_pattern, text):
            entities.append(EntitySpan(
                entity_type="URL",
                text=match.group(),
                start=match.start(),
                end=match.end(),
                confidence=0.95,
            ))

        # IP address pattern
        ip_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        for match in re.finditer(ip_pattern, text):
            entities.append(EntitySpan(
                entity_type="IP_ADDRESS",
                text=match.group(),
                start=match.start(),
                end=match.end(),
                confidence=0.95,
            ))

        # Date pattern
        date_patterns = [
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s?\d{1,2}(?:st|nd|rd|th)?,?\s?\d{4}\b',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
        ]
        for date_pattern in date_patterns:
            for match in re.finditer(date_pattern, text):
                entities.append(EntitySpan(
                    entity_type="DATE",
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.7,
                ))

        # Age pattern (numbers in typical age ranges)
        age_pattern = r'\b(?:[1-9]\d|1[01-8])\s?(?:years? old|y\.o\.?)\b'
        for match in re.finditer(age_pattern, text):
            entities.append(EntitySpan(
                entity_type="CARDINAL",
                text=match.group(),
                start=match.start(),
                end=match.end(),
                confidence=0.6,
            ))

        # Location patterns (city, state combinations)
        location_patterns = [
            r'\b[A-Z][a-z]+,\s*[A-Z][a-z]+(?:,\s*[A-Z]{2})?\b',  # City, State
            r'\b(?:New York|Los Angeles|San Francisco|Chicago|Houston|Phoenix|Philadelphia|San Antonio|San Diego|Dallas|San Jose|Austin|Jacksonville|Fort Worth|Columbus|Charlotte|Detroit|El Paso|Memphis|Seattle|Denver|Washington|Boston|Nashville|Baltimore|Louisville|Portland|Las Vegas|Milwaukee|Albuquerque|Tucson|Fresno|Sacramento|Kansas City|Mesa|Atlanta|Omaha|Colorado Springs|Raleigh|Miami|Long Beach|Virginia Beach|Oakland|Minneapolis|Tulsa|Arlington|Tampa|New Orleans|Wichita|Cleveland|Paradise|Arlington|Honolulu|Lexington|Louisville|Henderson|Chula Vista|Newark|Anaheim|Santa Ana|Riverside|Corona|Fort Lauderdale|St. Petersburg|Chandler|Glendale|Scottsdale|Gilbert|Tempe|Lubbock|Chesapeake|Irving|Laredo|Henderson|Chandler|Norwalk|Glendale|Chandler|Madison|Denton|Vancouver|Winston Salem|Fontana|Reno|Oceanside|Stockton|Garland|Plano|North Las Vegas|Rochester|Hialeah| Surprise|Sunnyvale|Elk Grove|Warren|McKinney|Columbia|Murrieta|Orange City|Fullerton|Miramar|Richardson|Daly City)\\\b',
        ]
        for location_pattern in location_patterns:
            for match in re.finditer(location_pattern, text):
                entities.append(EntitySpan(
                    entity_type="LOCATION",
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.7,
                ))

        return entities

    def _remove_overlaps(self, entities: List[EntitySpan]) -> List[EntitySpan]:
        """
        Remove overlapping entities, keeping the longest/most specific one.
        """
        if not entities:
            return []

        # Sort by start position, then by length (descending)
        entities.sort(key=lambda e: (e.start, -(e.end - e.start)))

        filtered = []
        for entity in entities:
            # Check if overlaps with any in filtered
            overlaps = False
            for kept in filtered:
                if not (entity.end <= kept.start or entity.start >= kept.end):
                    overlaps = True
                    break

            if not overlaps:
                filtered.append(entity)

        return filtered

    def mask_spans(
        self,
        text: str,
        entities: List[EntitySpan],
    ) -> str:
        """
        Apply masking to the detected entity spans.

        Args:
            text: Original text
            entities: List of entities to mask

        Returns:
            Text with masked entities
        """
        if not entities:
            return text

        # Sort entities by start position (reverse order for safe replacement)
        entities_sorted = sorted(entities, key=lambda e: e.start, reverse=True)

        masked_text = text
        offsets = 0  # Track position shifts due to replacements

        for entity in entities_sorted:
            # Adjust positions based on previous replacements
            actual_start = entity.start + offsets
            actual_end = entity.end + offsets

            replacement = self._get_replacement(entity)

            # Apply replacement
            before = masked_text[:actual_start]
            after = masked_text[actual_end:]

            # Calculate new offset adjustment
            old_length = actual_end - actual_start
            new_length = len(replacement)
            offsets += new_length - old_length

            masked_text = before + replacement + after

        return masked_text

    def _get_replacement(self, entity: EntitySpan) -> str:
        """
        Get replacement text based on configuration.
        """
        if self.replacement_type == "*":
            # Use asterisks matching length
            return "[" + "".join(["*" for _ in range(len(entity.text))]) + "]"

        elif self.replacement_type == "entity":
            # Use entity type placeholder
            pii_type = self.ENTITY_TO_PII.get(entity.entity_type, "pii")
            return f"[{pii_type.upper()}]"

        elif self.replacement_type == "model":
            # Use generalized form
            return self._generalize_entity(entity)

        else:
            # Default to asterisk
            return "[" + "".join(["*" for _ in range(len(entity.text))}) + "]"

    def _generalize_entity(self, entity: EntitySpan) -> str:
        """
        Generate a generalized version of the entity.

        E.g.:
        - "John" -> "[NAME]"
        - "New York" -> "[LOCATION]"
        - "25 years old" -> "[AGE]"
        """
        pii_type = self.ENTITY_TO_PII.get(entity.entity_type, "pii")

        # Specific generalizations by type
        generalizations = {
            "name": "[NAME]",
            "location": "[LOCATION]",
            "organization": "[ORGANIZATION]",
            "date": "[DATE]",
            "time": "[TIME]",
            "email": "[EMAIL]",
            "phone": "[PHONE]",
            "url": "[URL]",
            "ip": "[IP_ADDRESS]",
            "demographic": "[DEMOGRAPHIC]",
            "number": "[NUMBER]",
        }

        return generalizations.get(pii_type, "[PII]")

    def generalize_spans(
        self,
        text: str,
        entities: List[EntitySpan],
    ) -> str:
        """
        Apply generalization to detected entity spans.

        This is a more sophisticated approach that preserves some information
        while protecting privacy.
        """
        if not entities:
            return text

        # Sort entities by start position (reverse order for safe replacement)
        entities_sorted = sorted(entities, key=lambda e: e.start, reverse=True)

        generalized_text = text
        offsets = 0

        for entity in entities_sorted:
            actual_start = entity.start + offsets
            actual_end = entity.end + offsets

            generalized = self._get_generalized_form(entity)

            before = generalized_text[:actual_start]
            after = generalized_text[actual_end:]

            old_length = actual_end - actual_start
            new_length = len(generalized)
            offsets += new_length - old_length

            generalized_text = before + generalized + after

        return generalized_text

    def _get_generalized_form(self, entity: EntitySpan) -> str:
        """
        Get a generalized form that preserves some semantic information.
        """
        entity_type = entity.entity_type
        text = entity.text

        # Location generalizations
        if entity_type in ["LOCATION", "GPE", "LOC"]:
            # Check if it's a country, state, or city
            # Could use a geocoding service, but use heuristics
            return "[LOCATION]"

        # Person names
        if entity_type == "PERSON":
            return "[PERSON]"

        # Organizations
        if entity_type == "ORG":
            return "[ORGANIZATION]"

        # Dates
        if entity_type == "DATE":
            return "[DATE]"

        # Numbers (could be age)
        if entity_type in ["CARDINAL", "ORDINAL"]:
            # Check if it looks like an age
            if any(word in text.lower() for word in ["years", "old", "age", "y/o"]):
                return "[AGE]"
            return "[NUMBER]"

        # Default
        return f"[{entity_type}]"

    def anonymize(self, text: str) -> str:
        """
        Anonymize a single text string.

        Args:
            text: Input text to anonymize

        Returns:
            Anonymized text
        """
        # Step 1: Detect entities
        entities = self.detect_entities(text)

        # Step 2: Apply masking or generalization
        if self.replacement_type == "model" or self.cfg.target_mode == "generalize":
            return self.generalize_spans(text, entities)
        else:
            return self.mask_spans(text, entities)

    def anonymize_profiles(self, profiles: List[Profile]) -> List[Profile]:
        """
        Anonymize a list of profiles.

        Args:
            profiles: List of profiles to anonymize

        Yields:
            Anonymized profiles
        """
        from src.reddit.reddit_types import AnnotatedComments, Comment

        for profile in profiles:
            # Get original comments
            if not profile.comments:
                yield profile
                continue

            original_comments = profile.get_original_comments().comments

            # Anonymize each comment
            anonymized_comments = []
            for comment in original_comments:
                anonymized_text = self.anonymize(comment.text)

                # Create new comment with anonymized text
                new_comment = Comment(
                    text=anonymized_text,
                    subreddit=comment.subreddit,
                    user=comment.user,
                    timestamp=comment.timestamp,
                )
                anonymized_comments.append(new_comment)

            # Create new annotated comments object
            annotated = AnnotatedComments(
                comments=anonymized_comments,
                review_pii=profile.get_original_comments().review_pii,
                predictions={},  # Will be filled by inference
                utility={},  # Will be filled by utility scoring
            )

            # Add to profile
            profile.comments.append(annotated)

            yield profile
