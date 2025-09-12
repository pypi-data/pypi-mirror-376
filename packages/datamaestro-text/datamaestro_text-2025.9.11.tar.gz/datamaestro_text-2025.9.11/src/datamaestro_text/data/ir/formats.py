from functools import cached_property
from typing import ClassVar, Tuple, List
from attrs import define
from datamaestro.record import record_type
from ir_datasets.datasets.wapo import WapoDocMedia
from .base import TextItem, SimpleTextItem, IDItem
from ir_datasets.datasets.cord19 import Cord19FullTextSection


@define
class DocumentWithTitle(TextItem):
    """Web document with title and body"""

    body: str

    title: str

    @cached_property
    def text(self):
        return f"{self.title} {self.body}"


@define
class CordDocument(DocumentWithTitle):
    url: str
    pubmed_id: str


@define
class CordFullTextDocument(TextItem):
    title: str
    doi: str
    date: str
    abstract: str
    body: Tuple[Cord19FullTextSection, ...]

    @cached_property
    def text(self):
        return self.abstract


@define
class MsMarcoDocument(TextItem):
    url: str
    title: str
    body: str

    @cached_property
    def text(self):
        return self.body


@define
class NFCorpusDocument(TextItem):
    url: str
    title: str
    abstract: str

    @cached_property
    def text(self):
        return f"{self.title} {self.abstract}"


@define
class TitleDocument(TextItem):
    body: str
    title: str

    @cached_property
    def text(self):
        return f"{self.title} {self.body}"


@define
class TitleUrlDocument(TitleDocument):
    url: str


@define
class TrecParsedDocument(TextItem):
    title: str
    body: str
    marked_up_doc: bytes

    @cached_property
    def text(self):
        return f"{self.title} {self.body}"


@define
class WapoDocument(TextItem):
    url: str
    title: str
    author: str
    published_date: int
    kicker: str
    body: str
    body_paras_html: Tuple[str, ...]
    body_media: Tuple[WapoDocMedia, ...]

    @cached_property
    def text(self):
        return f"{self.title} {self.body_paras_html}"


@define
class TweetDoc(TextItem):
    text: str
    user_id: str
    created_at: str
    lang: str
    reply_doc_id: str
    retweet_doc_id: str
    source: bytes
    source_content_type: str


@define
class OrConvQADocument(TextItem):
    title: str
    body: str
    aid: str
    bid: int

    @cached_property
    def text(self):
        return f"{self.title} {self.body}"


@define
class DprW100Doc(TextItem):
    text: str
    title: str


@define
class MsMarcoV2Passage(TextItem):
    text: str
    spans: Tuple[Tuple[int, int], ...]
    msmarco_document_id: str


@define
class Touche2020(TextItem):
    text: str
    title: str
    stance: str
    url: str


@define
class SciDocs(TextItem):
    text: str
    title: str
    authors: List[str]
    year: int
    cited_by: List[str]
    references: List[str]


@define
class UrlTopic(TextItem):
    text: str
    url: str


@define
class NFCorpusTopic(TextItem):
    text: str
    all: str


@define
class TrecMb13Query(TextItem):
    query: str
    time: str
    tweet_time: str

    def get_text(self):
        return f"{self.query}"


@define
class TrecMb14Query(TextItem):
    query: str
    time: str
    tweet_time: str
    description: str

    def get_text(self):
        return f"{self.query}"


@define
class SciDocsTopic(TextItem):
    text: str
    authors: List[str]
    year: int
    cited_by: List[str]
    references: List[str]


@define()
class TrecTopic(SimpleTextItem):
    description: str
    narrative: str


TrecTopicRecord = record_type(IDItem, TrecTopic)


@define
class DprW100Query(TextItem):
    text: str
    answers: Tuple[str]


@define
class TrecBackgroundLinkingQuery(IDItem):
    query_id: str
    doc_id: str
    url: str

    def get_text(self):
        raise NotImplementedError()
