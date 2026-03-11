import argparse
import csv
import json
import logging
import re
from pathlib import Path

import fitz
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from wordcloud import STOPWORDS, WordCloud


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def parse_args():
    parser = argparse.ArgumentParser(description="Analyze open-access papers with GROBID.")
    parser.add_argument("--papers-dir", default="papers", help="Directory containing PDF papers")
    parser.add_argument("--output-dir", default="results", help="Directory where outputs will be saved")
    parser.add_argument(
        "--grobid-url",
        default="http://localhost:8070/api/processFulltextDocument",
        help="GROBID fulltext processing endpoint"
    )
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds for GROBID requests")
    return parser.parse_args()


def ensure_directories(output_dir: Path) -> Path:
    tei_dir = output_dir / "tei"
    output_dir.mkdir(parents=True, exist_ok=True)
    tei_dir.mkdir(parents=True, exist_ok=True)
    return tei_dir


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_abstract(soup: BeautifulSoup) -> str:
    abstract = soup.find("abstract")
    if not abstract:
        return ""
    return clean_text(abstract.get_text(separator=" "))


def count_figures(soup: BeautifulSoup) -> int:
    total = 0
    for fig in soup.find_all("figure"):
        label = fig.find("label")
        head = fig.find("head")

        text_parts = []
        if label:
            text_parts.append(label.get_text(" ", strip=True))
        if head:
            text_parts.append(head.get_text(" ", strip=True))

        figure_text = clean_text(" ".join(text_parts))

        # Cuenta menciones explícitas tipo Figure 1 / Fig. 2
        matches = re.findall(r"\b(?:fig(?:ure)?\.?)\s*[A-Z]?\d+\b", figure_text, flags=re.IGNORECASE)
        if matches:
            total += len(matches)
            continue

        # Fallback razonable: xml:id tipo fig_*
        xml_id = fig.get("xml:id", "") or fig.get("id", "")
        if xml_id.startswith("fig_"):
            total += 1

    return total


def extract_links_from_tei(soup: BeautifulSoup) -> set[str]:
    links = set()

    for ref in soup.find_all("ref"):
        target = ref.get("target")
        if target and target.startswith(("http://", "https://")):
            links.add(target.rstrip(").,;]"))

    text = soup.get_text(" ")
    regex_links = re.findall(r"https?://[^\s<>\"]+", text)
    for link in regex_links:
        links.add(link.rstrip(").,;]"))

    return links


def extract_links_from_pdf(pdf_path: Path) -> set[str]:
    links = set()
    doc = fitz.open(pdf_path)

    try:
        for page in doc:
            for link in page.get_links():
                uri = link.get("uri")
                if uri and uri.startswith(("http://", "https://")):
                    links.add(uri.rstrip(").,;]"))
    finally:
        doc.close()

    return links


def extract_links(soup: BeautifulSoup, pdf_path: Path) -> list[str]:
    links = set()
    links.update(extract_links_from_tei(soup))
    links.update(extract_links_from_pdf(pdf_path))
    return sorted(links)


def save_tei(tei_dir: Path, filename: str, tei_xml: str) -> None:
    tei_path = tei_dir / f"{Path(filename).stem}.tei.xml"
    tei_path.write_text(tei_xml, encoding="utf-8")


def process_pdf(pdf_path: Path, grobid_url: str, timeout: int) -> str:
    with open(pdf_path, "rb") as f:
        files = {"input": (pdf_path.name, f, "application/pdf")}
        response = requests.post(grobid_url, files=files, timeout=timeout)
    response.raise_for_status()
    return response.text


def generate_keyword_cloud(abstracts: list[str], output_path: Path) -> None:
    text = " ".join(abstracts).lower().strip()
    if not text:
        logging.warning("No abstracts found. Keyword cloud will not be generated.")
        return

    custom_stopwords = set(STOPWORDS) | {
        "using", "based", "results", "study", "paper", "show", "shows",
        "approach", "method", "methods", "model", "models", "new"
    }

    wc = WordCloud(
        width=1200,
        height=600,
        background_color="white",
        stopwords=custom_stopwords,
        random_state=42
    ).generate(text)

    plt.figure(figsize=(12, 6))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    logging.info(f"Keyword cloud saved to {output_path}")


def generate_figures_chart(figures_count: dict[str, int], output_path: Path) -> None:
    if not figures_count:
        logging.warning("No figure counts available. Chart will not be generated.")
        return

    names = list(figures_count.keys())
    counts = list(figures_count.values())

    plt.figure(figsize=(12, 6))
    plt.bar(names, counts)
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.xlabel("Articles")
    plt.ylabel("Number of figures")
    plt.title("Number of figures per article")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    logging.info(f"Figures chart saved to {output_path}")


def save_figures_csv(figures_count: dict[str, int], output_path: Path) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["paper", "figure_count"])
        for paper, count in figures_count.items():
            writer.writerow([paper, count])
    logging.info(f"Figure counts CSV saved to {output_path}")


def save_links_json(links_per_paper: dict[str, list[str]], output_path: Path) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(links_per_paper, f, indent=2, ensure_ascii=False)
    logging.info(f"Links JSON saved to {output_path}")


def main():
    setup_logging()
    args = parse_args()

    papers_dir = Path(args.papers_dir)
    output_dir = Path(args.output_dir)
    tei_dir = ensure_directories(output_dir)

    if not papers_dir.exists():
        raise FileNotFoundError(f"Papers directory not found: {papers_dir}")

    pdf_files = sorted([p for p in papers_dir.iterdir() if p.suffix.lower() == ".pdf"])
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {papers_dir}")

    logging.info(f"Found {len(pdf_files)} PDF files.")

    abstracts = []
    figures_count = {}
    links_per_paper = {}
    failed_papers = []

    for pdf_path in pdf_files:
        logging.info(f"Processing {pdf_path.name}...")
        try:
            tei_xml = process_pdf(pdf_path, args.grobid_url, args.timeout)
            save_tei(tei_dir, pdf_path.name, tei_xml)

            soup = BeautifulSoup(tei_xml, "xml")

            abstract = extract_abstract(soup)
            if abstract:
                abstracts.append(abstract)

            figures_count[pdf_path.name] = count_figures(soup)
            links_per_paper[pdf_path.name] = extract_links(soup, pdf_path)

        except Exception as e:
            logging.error(f"Failed to process {pdf_path.name}: {e}")
            failed_papers.append(pdf_path.name)

    generate_keyword_cloud(abstracts, output_dir / "keyword_cloud.png")
    generate_figures_chart(figures_count, output_dir / "figures_chart.png")
    save_figures_csv(figures_count, output_dir / "figures_per_article.csv")
    save_links_json(links_per_paper, output_dir / "links_per_paper.json")

    summary = {
        "processed_papers": len(pdf_files) - len(failed_papers),
        "failed_papers": failed_papers,
        "total_papers": len(pdf_files)
    }

    with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logging.info("Analysis completed.")
    logging.info(f"Processed: {summary['processed_papers']}/{summary['total_papers']}")
    if failed_papers:
        logging.warning(f"Failed papers: {failed_papers}")


if __name__ == "__main__":
    main()
