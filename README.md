<div align="center">

# MusGU+: Toward a Musician-Centered Evaluation Framework and Discovery Tool for Generative Music AI

**Laura Ibáñez-Martínez**<sup>1</sup>, **Roser Batlle-Roca**<sup>1</sup>, **Xavier Serra**<sup>1</sup>, **Martín Rocamora**<sup>1</sup>

<sup>1</sup>Music Technology Group, Universitat Pompeu Fabra, Barcelona

**MusGU+ (Music-Generative Usable+ AI)** is a musician-centered evaluation framework designed to assess how generative music models can be *adapted*, *used*, and *controlled* in real-world creative contexts.

🔍 Explore the **[MusGU+ discovery tool](https://lauraibnz.github.io/MusGU-plus/)**

[![License: MIT](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22281934.svg)](https://doi.org/10.5281/zenodo.22281934)

</div>

---

## The MusGU+ Framework

MusGU+ evaluates generative music models along three complementary dimensions, each framed around a core practical question:

- **Adaptability** — *Can I realistically adapt this model to my own data?*
- **Usability** — *Can I access, run, and integrate this model into my music-making workflow?*
- **Controllability** — *Can I guide the model in musically meaningful and interpretable ways?*

Each dimension comprises multiple criteria (e.g., hardware requirements, interface availability, conditioning inputs, control parameters) and is evaluated on a three-level scale reflecting the degree of support provided: **fully**, **partially**, **not**.

📖 Read the **[detailed evaluation criteria](https://lauraibnz.github.io/MusGU-plus/framework)**.


## A Discovery Tool for Musicians

MusGU+ is designed as an interactive discovery tool rather than a definitive leaderboard. It allows musicians to explore, filter, and compare generative music models based on specific criteria and tags, highlighting differences in adaptability, usability, and controllability. This supports early-stage exploration and informed selection of models that best fit different creative practices and workflow needs.

## Contributing

If you would like to help expand or refine MusGU+, there are two main ways to contribute:

- **Suggest a new model**. The simplest option is to open an issue using the **[Suggest a New Model](https://github.com/lauraibnz/MusGU-plus/issues/new?template=suggest-a-new-model.md)** template. A brief explanation and any relevant links are enough; maintainers will take care of the detailed evaluation. More experienced contributors can instead create a new branch, add a YAML evaluation in **[`projects/`](projects)** following **[`projects/_template.yaml`](projects/_template.yaml)**, and submit a pull request.
- **Propose changes to an existing evaluation**. If you think a current model entry should be updated, corrected, or expanded, you can open an issue or submit a pull request with supporting evidence.


## Citation

The paper *MusGU+: Toward a Musician-Centered Evaluation Framework and Discovery Tool for Generative Music AI* was accepted at the **7th Conference on AI Music Creativity (AIMC 2026)**. If our work is relevant to you, please cite it as follows:

```bibtex
@InProceedings{ibanezmartinez2026musgu,
  author    = {Ibáñez-Martínez, Laura and Batlle-Roca, Roser and Serra, Xavier and Rocamora, Martín},
  title     = {MusGU+: Toward a Musician-Centered Evaluation Framework and Discovery Tool for Generative Music AI},
  booktitle = {Proceedings of the 7th Conference on AI Music Creativity (AIMC 2026)},
  year      = {2026},
  month     = sep,
  publisher = {AIMC},
  doi       = {10.5281/zenodo.22281934},
  url       = {https://doi.org/10.5281/zenodo.22281934}
}
```

## Relationship to MusGO

MusGU+ builds on the **[MusGO framework](https://roserbatlleroca.github.io/MusGO_framework/)** (Music-Generative Open AI), adopting its composite and graded evaluation approach while shifting the emphasis from openness toward practical suitability for musicians. While MusGO focuses on openness and responsible research practices, MusGU+ focuses on whether generative music systems can be adapted, used, and controlled in real-world creative contexts. The two frameworks provide complementary perspectives on generative music AI.
