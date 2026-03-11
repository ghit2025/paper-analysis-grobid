# Installation

## Option A: Python virtual environment

```bash
python3 -m venv env
source env/bin/activate        # Windows: env\Scripts\activate
pip install -r requirements.txt
```

## Option B: Docker (recommended)

Make sure Docker is installed, then:

```bash
# Start GROBID and the analysis container together
docker-compose up
```

Results will appear in the `results/` folder.
