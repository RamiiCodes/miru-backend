"""seed semantic signal catalog entries

Revision ID: 0c51568e5ab6
Revises: 3c6abe1fd0b6
Create Date: 2026-07-14 11:37:49.938743

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision: str = '0c51568e5ab6'
down_revision: Union[str, Sequence[str], None] = '3c6abe1fd0b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SEMANTIC_SIGNAL_CATALOG = [
    {
        "code": "semantic_valence",
        "name": "Semantic Valence",
        "domain": "semantic",
        "description": "Generic semantic dimension: negative to positive emotional tone.",
    },
    {
        "code": "semantic_arousal",
        "name": "Semantic Arousal",
        "domain": "semantic",
        "description": "Generic semantic dimension: calm/deactivated to activated/intense.",
    },
    {
        "code": "semantic_threat",
        "name": "Semantic Threat",
        "domain": "semantic",
        "description": "Generic semantic dimension: felt danger, pressure, alarm, or risk.",
    },
    {
        "code": "semantic_control",
        "name": "Semantic Control",
        "domain": "semantic",
        "description": "Generic semantic dimension: sense of agency and ability to act.",
    },
    {
        "code": "semantic_social_connection",
        "name": "Semantic Social Connection",
        "domain": "semantic",
        "description": "Generic semantic dimension: isolation/rejection to connection/support.",
    },
    {
        "code": "semantic_uncertainty",
        "name": "Semantic Uncertainty",
        "domain": "semantic",
        "description": "Generic semantic dimension: clarity/certainty to uncertainty/confusion.",
    },
    {
        "code": "semantic_self_evaluation",
        "name": "Semantic Self Evaluation",
        "domain": "semantic",
        "description": "Generic semantic dimension: self-criticism/shame to self-acceptance/pride.",
    },
    {
        "code": "semantic_energy",
        "name": "Semantic Energy",
        "domain": "semantic",
        "description": "Generic semantic dimension: depleted to energized.",
    },
]


def upgrade() -> None:
    connection = op.get_bind()

    for signal in SEMANTIC_SIGNAL_CATALOG:
        params = {
            "id": str(uuid.uuid4()),
            **signal,
        }

        connection.execute(
            sa.text(
                """
                INSERT INTO signal_catalog
                    (id, code, name, domain, description, is_active)
                SELECT
                    CAST(:id AS UUID),
                    CAST(:code AS VARCHAR),
                    CAST(:name AS VARCHAR),
                    CAST(:domain AS VARCHAR),
                    CAST(:description AS TEXT),
                    true
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM signal_catalog
                    WHERE code = CAST(:code AS VARCHAR)
                )
                """
            ),
            params,
        )

def downgrade() -> None:
    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            DELETE FROM signal_catalog
            WHERE code IN (
                'semantic_valence',
                'semantic_arousal',
                'semantic_threat',
                'semantic_control',
                'semantic_social_connection',
                'semantic_uncertainty',
                'semantic_self_evaluation',
                'semantic_energy'
            )
            """
        )
    )