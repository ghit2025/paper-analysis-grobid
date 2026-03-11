from bs4 import BeautifulSoup

def extract_links(soup):
    links = set()
    for ref in soup.find_all("ref"):
        target = ref.get("target")
        if target and target.startswith(("http://", "https://")):
            links.add(target.rstrip(").,;]"))
    return sorted(links)

def count_figures(soup):
    return len(soup.find_all("figure"))

def extract_abstract(soup):
    abstract = soup.find("abstract")
    if not abstract: return ""
    return " ".join(abstract.get_text(separator=" ").split())

def test_extract_links():
    xml = """
    <TEI><body>
      <p>See <ref target="https://example.org">this link</ref>.</p>
      <p>See <ref target="https://doi.org/10.1000/xyz">doi</ref>.</p>
    </body></TEI>
    """
    soup = BeautifulSoup(xml, "xml")
    links = extract_links(soup)
    assert "https://example.org" in links
    assert "https://doi.org/10.1000/xyz" in links

def test_count_figures():
    xml = "<TEI><figure></figure><figure></figure><figure></figure></TEI>"
    soup = BeautifulSoup(xml, "xml")
    assert count_figures(soup) == 3

def test_extract_abstract():
    xml = "<TEI><abstract>This is a test abstract.</abstract></TEI>"
    soup = BeautifulSoup(xml, "xml")
    assert extract_abstract(soup) == "This is a test abstract."
