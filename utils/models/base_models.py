from pathlib import Path
import csv
from typing import Any, Dict
import logging

from pydantic import BaseModel

from utils._types import Id


logger = logging.getLogger(__name__)


class BaseModelDVFSingular(BaseModel):
    def key(self):
        return None  # À modif dans les sous models pour renvoyer l'id

    def items(self):
        return self.model_dump().items()

    def _merge(self, other: "BaseModel") -> None:
        for k, v in other.items():
            if self[k] is None:
                self[k] = v


class BaseModelDVFPlurial(BaseModel):
    _values: Dict[Id, BaseModelDVFSingular]

    def to_csv(
        self,
        filepath: Path,
        *,
        encoding: str = "utf-8",
        delimiter: str = ";",
        quote: str = '"',
    ) -> None:
        """
        Exporte au format csv dans le dossier path les éléments de la classe
        """
        with open(
            filepath, "w", encoding=encoding, delimiter=delimiter, newline=""
        ) as f:
            if len(self) == 0:
                logger.warning("Pas de données à exporter")
                return
            writer = csv.DictWriter(
                f,
                fieldnames=self[0].model_dump().keys(),
                delimiter=delimiter,
                quotechar=quote,
            )
            for elm in self:
                writer.writerow(elm.model_dump())

    def append(self, bm: BaseModel) -> None:
        if bm.key() not in self.keys():
            self[bm.key()] = bm
        else:
            self[bm.key()]._merge(bm)

    def keys(self):
        return self._values.keys()

    def __getitem__(self, key: Id) -> BaseModelDVFSingular:
        return self._values.values[key]

    def __setitem__(self, key: Id, value: Any):
        self._values[key] = value

    def __len__(self):
        return len(self._values)

    def __iter__(self):
        return self._values.values()
