# css-farmers

## Farmers and Biogas Plant Collective Dynamics: an Agent Based Model


We develop an Agent-Based Model (ABM) using Mesa to simulate farmers' decisions about building biogas plants in Switzerland.

Contributors: Alina Akopian, Ross Roessler, Sandrine Werner


## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

To run the sensitivity analysis:

```bash
# Note you'll have to uncomment the parameter(s) you want to analyze.
python batch_analysis.py
```

### Interactive Visualization

Run the interactive web-based visualization server:

```bash
solara run server.py
```

Then open your browser to http://localhost:8765 to see the model in action.

## Final Presentation

Here in the main directory as 'presentation.pptx'.

Slides also available as a PDF, 'presentation-slides.pdf'.