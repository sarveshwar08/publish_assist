import time
from abc import ABC, abstractmethod
from tempfile import mkdtemp


from publish_assist.domain.documents import NoSQLBaseDocument

class BaseCrawler(ABC):
    model: type[NoSQLBaseDocument]
    dataset_id: str

    @abstractmethod
    def extract(self, link: str, dataset_id: str, **kwargs) -> None: ...
