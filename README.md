# Towards Fair Roads - Manifesto for Fair Traffic Engineering

This repository contains the code and data for the computational case studies in:

> Kevin Riehl, Anastasios Kouvelas, and Michail A. Makridis, "Towards Fair Roads - Manifesto for Fair Traffic Engineering", Sustainability 2026, 18, 7068. https://doi.org/10.3390/su18147068

The paper proposes a mode-agnostic distributive fairness framework for traffic engineering and demonstrates it with case studies on signalized intersection management and static road pricing.

## Case Studies

- `CaseStudy_SIM/` contains the synthetic signalized-intersection-management analysis, including scripts for convexity, dendrogram, and fairness-efficiency trade-off figures.
- `CaseStudy_InterMode/` contains the intermodal signalized-intersection case study with SUMO network and demand files, max-pressure simulation code, optimization over mode weights, and generated log files.
- `CaseStudy_CongestionPricing/` contains the static road-pricing case study, including travel-time distributions, value-of-time data, market-model and pricing analyses, fairness-pricing scripts, and a SUMO route-simulation subfolder.

Precomputed logs and data tables are included so that many analysis and figure scripts can be run without rerunning the full SUMO simulations.

## Installation

The scripts are plain Python research scripts and use relative paths. Run them from the folder in which they are located.

Create a Python environment and install the main Python dependencies:

```bash
pip install numpy pandas matplotlib scipy seaborn openpyxl
```

Simulation scripts also require SUMO and TraCI:

1. Install SUMO: https://eclipse.dev/sumo/
2. Set `SUMO_HOME` to your SUMO installation.
3. Update hard-coded `sumo.exe` paths in the SUMO scripts where needed. Several scripts currently point to a local SUMO 1.19.0 installation path.

## Running the Analysis

Run figure-generation scripts from their case-study directories, for example:

```bash
cd CaseStudy_SIM
python FAIR_1_Convexity.py
python FAIR_2_Dendrogram.py
python FAIR_3_Tradefoff.py
```

```bash
cd CaseStudy_CongestionPricing
python Nfigure1_TravelTimeDist.py
python Nfigure2_SplitsEquilibria.py
python Nfigure3_MarketModel.py
python Nfigure4_Pricing.py
python Nfigure5_FairnessPricing.py
```

```bash
cd CaseStudy_InterMode
python Figure_D_Delay_Distributions_Modes.py
```

To rerun SUMO-based simulations, first verify the SUMO binary path and then run the relevant simulation scripts from their own directories:

```bash
cd CaseStudy_InterMode
python MaxPressure_Simulation.py
python Weight_Optimizer.py
```

```bash
cd CaseStudy_CongestionPricing/MapSimulation
python 1_RunSimulation.py
python 2_RunSimulation_FullDistribution.py
python 3_ParseResults.py
```

Some scripts display figures with `matplotlib.pyplot.show()`. Add `plt.savefig(...)` locally if you want to export figures directly.

## Notes

- Relative paths are used throughout the scripts, so the current working directory matters.
- Some generated files are written into local `logs/` folders or route-specific text files.
- Rerunning optimization or simulation scripts may overwrite or append to existing outputs; keep a copy of reference results if needed.

## Citation

If you use this repository, please cite:

```bibtex
@article{riehl2026fairroads,
  title = {Towards Fair Roads - Manifesto for Fair Traffic Engineering},
  author = {Riehl, Kevin and Kouvelas, Anastasios and Makridis, Michail A.},
  journal = {Sustainability},
  volume = {18},
  number = {14},
  pages = {7068},
  year = {2026},
  doi = {10.3390/su18147068},
  url = {https://doi.org/10.3390/su18147068}
}
```
