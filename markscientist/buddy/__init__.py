"""
MarkScientist Reviewer Buddy System

Fun reviewer characters that bring personality to the Judge agent.
"""

from .types import (
    ReviewerBuddy,
    REVIEWER_SPECIES,
    PERSONALITIES,
    TASK_REVIEWER_AFFINITY,
    EYES,
)
from .sprites import (
    render_face,
    render_sprite,
    render_sprite_string,
    get_reaction,
    get_mood_from_score,
    render_review_header,
)

__all__ = [
    'ReviewerBuddy',
    'REVIEWER_SPECIES',
    'PERSONALITIES',
    'TASK_REVIEWER_AFFINITY',
    'EYES',
    'render_face',
    'render_sprite',
    'render_sprite_string',
    'get_reaction',
    'get_mood_from_score',
    'render_review_header',
]
