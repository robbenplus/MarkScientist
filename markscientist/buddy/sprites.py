"""
MarkScientist Reviewer Buddy Sprites

ASCII art sprites for reviewer characters.
"""

from typing import Dict, List
from .types import ReviewerBuddy

# Compact face sprites for inline display
FACES: Dict[str, str] = {
    'owl': '(({E})({E}))',
    'cat': '={E}ω{E}=',
    'robot': '[{E}={E}]',
    'ghost': '/{E} {E}\\',
    'dragon': '<{E}~{E}>',
    'octopus': '~({E}{E})~',
}

# Full body sprites (5 lines each)
BODIES: Dict[str, List[str]] = {
    'owl': [
        '   /\\  /\\   ',
        '  (({E})({E}))  ',
        '  (  ><  )  ',
        '   \\    /   ',
        '    `--´    ',
    ],
    'cat': [
        '   /\\_/\\    ',
        '  ( {E}   {E})  ',
        '  (  ω  )   ',
        '  (")_(")   ',
        '     ~      ',
    ],
    'robot': [
        '   .[||].   ',
        '  [ {E}  {E} ]  ',
        '  [ ==== ]  ',
        '  |      |  ',
        '  `------´  ',
    ],
    'ghost': [
        '   .----.   ',
        '  / {E}  {E} \\  ',
        '  |      |  ',
        '  |      |  ',
        '  ~`~``~`~  ',
    ],
    'dragon': [
        '  /^\\  /^\\  ',
        ' <  {E}  {E}  > ',
        ' (   ~~   ) ',
        '  \\      /  ',
        '  `-vvvv-´  ',
    ],
    'octopus': [
        '   .----.   ',
        '  ( {E}  {E} )  ',
        '  (______)  ',
        '  /\\/\\/\\/\\  ',
        ' ~~~~~~~~~~ ',
    ],
}

# Review mood expressions
MOOD_SPRITES: Dict[str, Dict[str, str]] = {
    'excellent': {
        'owl': '  ✓ Excellent!  ',
        'cat': '  *purrs* Nice! ',
        'robot': ' [SCORE: HIGH] ',
        'ghost': '  ~Impressive~  ',
        'dragon': ' *nods wisely*  ',
        'octopus': ' 👍👍👍👍👍👍👍👍 ',
    },
    'good': {
        'owl': '  Quite good.   ',
        'cat': '  Acceptable... ',
        'robot': ' [SCORE: GOOD] ',
        'ghost': '  Not bad...    ',
        'dragon': ' Has potential. ',
        'octopus': '  Solid work.   ',
    },
    'needs_work': {
        'owl': '  Needs work... ',
        'cat': '  *squints*     ',
        'robot': ' [ISSUES FOUND]',
        'ghost': '  I see gaps... ',
        'dragon': ' Reconsider...  ',
        'octopus': '  Hmm, issues.  ',
    },
    'poor': {
        'owl': '  Major issues! ',
        'cat': '  *hisses*      ',
        'robot': ' [ERROR: LOW]  ',
        'ghost': '  Very weak...  ',
        'dragon': ' *sighs deeply* ',
        'octopus': '  Problematic.  ',
    },
}


def render_face(buddy: ReviewerBuddy) -> str:
    """Render a compact one-line face for the reviewer."""
    face_template = FACES.get(buddy.species, '({E}{E})')
    return face_template.replace('{E}', buddy.eye)


def render_sprite(buddy: ReviewerBuddy) -> List[str]:
    """Render the full body sprite."""
    body = BODIES.get(buddy.species, BODIES['owl'])
    return [line.replace('{E}', buddy.eye) for line in body]


def render_sprite_string(buddy: ReviewerBuddy) -> str:
    """Render the full sprite as a single string."""
    return '\n'.join(render_sprite(buddy))


def get_mood_from_score(score: float) -> str:
    """Get mood category from score."""
    if score >= 8:
        return 'excellent'
    elif score >= 6:
        return 'good'
    elif score >= 4:
        return 'needs_work'
    else:
        return 'poor'


def get_reaction(buddy: ReviewerBuddy, score: float) -> str:
    """Get a reaction message based on score."""
    mood = get_mood_from_score(score)
    reactions = MOOD_SPRITES.get(mood, {})
    return reactions.get(buddy.species, '...')


def render_review_header(buddy: ReviewerBuddy, score: float) -> str:
    """Render a review header with the buddy."""
    face = render_face(buddy)
    reaction = get_reaction(buddy, score)

    return f"{face} {buddy.name}: {reaction}"
