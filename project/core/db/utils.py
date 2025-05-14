"""Database-related utils."""

from typing import Sequence

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase, joinedload
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.orm.strategy_options import LoaderOption

from project.core.db.base import Base


def load_all_relationships(
    model_class: type[DeclarativeBase],
) -> Sequence[LoaderOption]:
    """Create list of joinedload options with all model relationships."""
    options: list[LoaderOption] = []
    cls_mapper: Mapper = inspect(model_class)

    for rel in cls_mapper.relationships:
        options.append(joinedload(getattr(model_class, rel.key)))

    return options


def check_active_relationships(model_instance: Base) -> list[str]:
    """Check that model instance have the list of relationships."""
    cls_mapper: Mapper = inspect(model_instance.__class__)
    active_relationships: list[str] = []

    # rel_property: sqlalchemy.orm.RelationshipProperty
    # rel_property.key - имя атрибута связи (например, "users")
    # rel_property.uselist=True, если коллекция (one-to-many, many-to-many)
    for rel_property in cls_mapper.relationships:
        if rel_property.uselist and getattr(model_instance, rel_property.key):
            active_relationships.append(rel_property.key)

    return active_relationships
