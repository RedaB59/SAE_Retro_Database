from datetime import date
from typing import Annotated

from pydantic import PositiveFloat

from utils._types import Id

from .base_models import BaseModelDVFPlurial, BaseModelDVFSingular


class Mutation(BaseModelDVFSingular):
    id_mutation: Annotated[str, 14]
    numero_mutation: int
    date: date
    valeur_fonciere: PositiveFloat


class Mutations(BaseModelDVFPlurial):
    _values: dict[Id, Mutation]
