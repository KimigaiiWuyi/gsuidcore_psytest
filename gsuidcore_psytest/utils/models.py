from typing import Dict, List

from msgspec import Struct


class Answer(Struct):
    detail: str
    point: int
    to: str
    key: List[str]
    extra: str


class Question(Struct):
    question: str
    image: str
    answer: List[Answer]


class Result(Struct):
    title: str
    image: str
    detail: str
    point_down: int
    point_up: int
    need_key: List[str]


class TestData(Struct):
    questions: Dict[str, Question]
    results: Dict[str, Result]
