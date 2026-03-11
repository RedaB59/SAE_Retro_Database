from datetime import date
from typing import Annotated

from pydantic import PositiveFloat

from .base_models import BaseModelDVFSingular


class Mutation(BaseModelDVFSingular):
    id_mutation: Annotated[str, 14]
    numero_mutation: int
    date: date
    valeur_fonciere: PositiveFloat
