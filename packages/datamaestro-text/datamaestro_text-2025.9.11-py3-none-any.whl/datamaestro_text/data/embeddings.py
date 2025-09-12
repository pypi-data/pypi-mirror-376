from experimaestro import Meta
from datamaestro.data import Base, File
from datamaestro.definitions import datatags
import numpy as np
from typing import Tuple, List


@datatags("word embeddings")
class WordEmbeddings(Base):
    """Generic word embeddings"""

    def load(self) -> Tuple[List[str], np.matrix]:
        """Load the word embeddings

        Returns:
            The word dictionary and the matrix
        """
        raise NotImplementedError()


class WordEmbeddingsText(WordEmbeddings, File):
    """Word embeddings as a text word / values"""
    encoding: Meta[str] = "utf-8"

    def load(self):
        words = []
        vectors = []
        dimension = None
        with self.path.open("rt", encoding=self.encoding) as fp:
            for ix, line in enumerate(fp):
                word, *values = line.split(" ")
                vectors.append([float(x) for x in values])
                if dimension is None:
                    dimension = len(values)
                else:
                    assert dimension == len(values)
                words.append(word)
        return words, np.matrix(vectors)
