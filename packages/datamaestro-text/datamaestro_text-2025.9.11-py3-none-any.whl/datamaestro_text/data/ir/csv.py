from functools import cached_property
from pathlib import Path
from typing import Iterator, Tuple, Type

from experimaestro import Param, Option, Constant, Meta
from datamaestro.definitions import argument
from datamaestro.record import Record, RecordType
import datamaestro_text.data.ir as ir
from datamaestro_text.data.ir.base import IDItem, SimpleTextItem
from datamaestro_text.interfaces.plaintext import read_tsv


@argument("path", type=Path)
@argument("separator", type=str, default="\t", ignored=True)
class AdhocRunWithText(ir.AdhocRun):
    "(qid, doc.id, query, passage)"
    pass


@argument("path", type=Path)
@argument("separator", type=str, default="\t", ignored=True)
class Topics(ir.Topics):
    "Pairs of query id - query using a separator"

    def iter(self):
        return (
            Record(IDItem(qid), SimpleTextItem(title))
            for qid, title in read_tsv(self.path)
        )

    @cached_property
    def topic_recordtype(self) -> RecordType:
        """The class for topics"""
        return RecordType(IDItem, SimpleTextItem)


class Documents(ir.Documents):
    "One line per document, format pid<SEP>text"

    path: Param[Path]
    separator: Meta[str] = "\t"

    pass
