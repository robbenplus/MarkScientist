"""
MarkScientist Reviewer Buddy Types

Defines reviewer character types, personalities, and traits.
"""

from dataclasses import dataclass, field
from typing import Dict, List

# Reviewer species available
REVIEWER_SPECIES = (
    'owl',        # Professor Owl - Rigorous, methodical
    'cat',        # Dr. Cat - Curious, picky about details
    'robot',      # Robot-9000 - Objective, data-driven
    'ghost',      # Ghost Scholar - Finds hidden issues
    'dragon',     # Dragon Sage - Big-picture thinking
    'octopus',    # Dr. Octopus - Multi-dimensional analysis
)

# Rarity levels
RARITIES = ('common', 'uncommon', 'rare', 'epic', 'legendary')

RARITY_COLORS: Dict[str, str] = {
    'common': 'dim',
    'uncommon': 'green',
    'rare': 'blue',
    'epic': 'magenta',
    'legendary': 'yellow',
}

# Eyes for different moods
EYES = {
    'neutral': '•',
    'happy': '◠',
    'strict': '▪',
    'curious': '◉',
    'thinking': '°',
    'skeptical': '¬',
}

# Personality traits that affect review style
PERSONALITIES: Dict[str, Dict] = {
    'owl': {
        'name': 'Professor Owl',
        'title': 'The Methodologist',
        'traits': ['rigorous', 'methodical', 'thorough'],
        'focus': 'methodology and rigor',
        'catchphrase': 'Let me examine the methodology...',
        'color': 'blue',
    },
    'cat': {
        'name': 'Dr. Whiskers',
        'title': 'The Detail Detective',
        'traits': ['curious', 'picky', 'observant'],
        'focus': 'details and edge cases',
        'catchphrase': 'Hmm, interesting... but what about...',
        'color': 'magenta',
    },
    'robot': {
        'name': 'EVAL-9000',
        'title': 'The Objective Analyzer',
        'traits': ['objective', 'systematic', 'quantitative'],
        'focus': 'metrics and data',
        'catchphrase': 'Computing evaluation scores...',
        'color': 'cyan',
    },
    'ghost': {
        'name': 'The Specter',
        'title': 'The Hidden Issue Finder',
        'traits': ['perceptive', 'mysterious', 'thorough'],
        'focus': 'hidden problems and assumptions',
        'catchphrase': 'I sense something overlooked...',
        'color': 'dim white',
    },
    'dragon': {
        'name': 'Elder Dragon',
        'title': 'The Wise Sage',
        'traits': ['wise', 'experienced', 'holistic'],
        'focus': 'big picture and impact',
        'catchphrase': 'Consider the broader implications...',
        'color': 'red',
    },
    'octopus': {
        'name': 'Dr. Tentacle',
        'title': 'The Multi-Analyst',
        'traits': ['multitasking', 'comprehensive', 'flexible'],
        'focus': 'multiple dimensions simultaneously',
        'catchphrase': 'Let me analyze this from all angles...',
        'color': 'green',
    },
}

# Task type to recommended reviewer mapping
TASK_REVIEWER_AFFINITY: Dict[str, List[str]] = {
    'factual_query': ['robot', 'owl'],
    'literature_review': ['owl', 'octopus'],
    'code_analysis': ['robot', 'cat'],
    'idea_proposal': ['dragon', 'ghost'],
    'experiment_design': ['owl', 'robot'],
    'writing_draft': ['cat', 'owl'],
    'data_analysis': ['robot', 'octopus'],
    'problem_solving': ['cat', 'dragon'],
}


@dataclass
class ReviewerBuddy:
    """A reviewer buddy character."""
    species: str
    name: str
    title: str
    traits: List[str]
    focus: str
    catchphrase: str
    color: str
    eye: str = '•'
    mood: str = 'neutral'

    @classmethod
    def from_species(cls, species: str, mood: str = 'neutral') -> 'ReviewerBuddy':
        """Create a reviewer from species."""
        if species not in PERSONALITIES:
            species = 'owl'  # Default

        p = PERSONALITIES[species]
        eye = EYES.get(mood, EYES['neutral'])

        return cls(
            species=species,
            name=p['name'],
            title=p['title'],
            traits=p['traits'],
            focus=p['focus'],
            catchphrase=p['catchphrase'],
            color=p['color'],
            eye=eye,
            mood=mood,
        )

    @classmethod
    def for_task_type(cls, task_type: str) -> 'ReviewerBuddy':
        """Get the best reviewer for a task type."""
        preferred = TASK_REVIEWER_AFFINITY.get(task_type, ['owl'])
        return cls.from_species(preferred[0])

    def get_intro(self) -> str:
        """Get introduction message."""
        return f"{self.catchphrase}"

    def get_mood_eye(self, score: float) -> str:
        """Get eye based on review score."""
        if score >= 8:
            return EYES['happy']
        elif score >= 6:
            return EYES['neutral']
        elif score >= 4:
            return EYES['thinking']
        else:
            return EYES['skeptical']
