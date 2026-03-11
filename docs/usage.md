# Usage

## Running with virtual environment

```bash
python main.py --papers-dir papers --output-dir results --grobid-url http://localhost:8070/api/processFulltextDocument
```

## Running with Docker

```bash
docker-compose up
```

## Output files

| File | Description |
|------|-------------|
| `results/keyword_cloud.png` | Keyword cloud from all abstracts |
| `results/figures_chart.png` | Bar chart of figures per paper |
| `results/figures_per_article.csv` | Raw figure counts |
| `results/links_per_paper.json` | All URLs found per paper |
| `results/summary.json` | Summary of all results |
