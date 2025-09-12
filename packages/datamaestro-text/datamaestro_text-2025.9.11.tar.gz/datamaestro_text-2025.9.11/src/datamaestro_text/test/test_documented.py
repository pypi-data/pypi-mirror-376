from pathlib import Path
from experimaestro.tools.documentation import DocumentationAnalyzer


def test_documented():
    """Test if every configuration is documented"""
    doc_path = Path(__file__).parents[3] / "docs" / "source" / "index.rst"
    analyzer = DocumentationAnalyzer(
        doc_path, set(["datamaestro_text"]), set(["datamaestro_text.test"])
    )

    analyzer.analyze()
    analyzer.report()
    analyzer.assert_valid_documentation()
