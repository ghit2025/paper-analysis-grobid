from bs4 import BeautifulSoup
from pathlib import Path
from unittest.mock import patch

from main import extract_abstract, count_figures, extract_links_from_tei, extract_links


def test_extract_abstract():
    xml = "<TEI><abstract>This is a test abstract.</abstract></TEI>"
    soup = BeautifulSoup(xml, "xml")
    assert extract_abstract(soup) == "This is a test abstract."


def test_count_figures_counts_explicit_figure_mentions():
    xml = """
    <TEI>
      <figure xml:id="fig_0"><label>1</label><head>FIG. 1.</head></figure>
      <figure><head>Algorithm 1</head></figure>
      <figure><head>Figure 3. Figure 4.</head></figure>
    </TEI>
    """
    soup = BeautifulSoup(xml, "xml")
    assert count_figures(soup) == 3


def test_extract_links_from_tei():
    xml = """
    <TEI><body>
      <p>See <ref target="https://example.org">this link</ref>.</p>
      <p>See <ref target="https://doi.org/10.1000/xyz">doi</ref>.</p>
    </body></TEI>
    """
    soup = BeautifulSoup(xml, "xml")
    links = extract_links_from_tei(soup)
    assert "https://example.org" in links
    assert "https://doi.org/10.1000/xyz" in links


@patch("main.extract_links_from_pdf")
def test_extract_links_combines_tei_and_pdf(mock_pdf_links):
    mock_pdf_links.return_value = {"https://pdf-link.example"}
    xml = """
    <TEI><body>
      <p><ref target="https://tei-link.example">link</ref></p>
    </body></TEI>
    """
    soup = BeautifulSoup(xml, "xml")
    links = extract_links(soup, Path("dummy.pdf"))
    assert "https://tei-link.example" in links
    assert "https://pdf-link.example" in links
