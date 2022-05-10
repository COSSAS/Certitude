<div align="center">
<a href="https://gitlab.com/cossas/certitude/-/tree/master"><img src="docs/CERTITUDE-logo.jpeg" height="100px" />

![Website](https://img.shields.io/badge/website-cossas--project.org-orange)
![Commits](https://gitlab.com/cossas/certitude/-/jobs/artifacts/master/raw/commits.svg?job=create_badge_svg)
![Pipeline status](https://gitlab.com/cossas/certitude/badges/master/pipeline.svg)
![Version](https://gitlab.com/cossas/certitude/-/jobs/artifacts/master/raw/version.svg?job=create_badge_svg)
![License: MPL2.0](https://gitlab.com/cossas/certitude/-/jobs/artifacts/master/raw/license.svg?job=create_badge_svg)
![Code-style](https://gitlab.com/cossas/certitude/-/jobs/artifacts/master/raw/code-style.svg?job=create_badge_svg)
</div></a>

<hr style="border:2px solid gray"> </hr>
<div align="center">
Certitude is a Python package to perform supervised malicious URL classification using a joint set of lexicographic and certificate features.
</div>
<hr style="border:2px solid gray"> </hr>

_All COSSAS projects are hosted on [GitLab](https://gitlab.com/cossas/dgad/) with a push mirror to GitHub. For issues/contributions check [CONTRIBUTING.md](CONTRIBUTING.md)_ 

## <img src="https://github.githubassets.com/images/icons/emoji/unicode/1f6a9.png" height="30px"> Getting Started

Certitude requires `whois`, which may not be available on some systems, and is thus distributed as a docker image.
If `whois` is available it can also be installed as a python package, see the development section below.

```bash
# pull image from registry
docker pull registry.gitlab.com/cossas/certitude:latest

# print help
docker run -it registry.gitlab.com/cossas/certitude:latest

# example perform training from data in local directory
docker run -it -v $(pwd)/tests/data:/data registry.gitlab.com/cossas/certitude:latest --train /data/newmodel -d /data/testset_labeled.csv

# example performing classification of a url with the trained model
docker run -it -v $(pwd)/tests/data:/data registry.gitlab.com/cossas/certitude:latest --model /data/newmodel --url https://www.tno.nl

```

## <img src="https://github.githubassets.com/images/icons/emoji/unicode/1f527.png" height="30px"> Development

To start developing this package, follow these steps:

- Start WSL
- `git clone` this project, ensuring you do that in the WSL filesystem. Run `cd` to
ensure you're in the WSL home directory
- `cd` into the just cloned directory
- Run `code .` to start VS Code
- In a VS Code terminal, run `poetry install`, `poetry shell` and finally
`poetry run pre-commit install`

### Code flow
Checkout the code flow [here](docs/cli-flow.png)

### Demo & Test

To see some useful commands and to test the code you can check the makefile:

```bash
make demo
```

## <img src="https://github.githubassets.com/images/icons/emoji/unicode/26a1.png" height="30px"> Contributing

Contributions to CERTITUDE are highly appreciated and more than welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for more information about our contributions process. 

## <img src="https://github.githubassets.com/images/icons/emoji/unicode/1f4dc.png" height="30px"> Maintainance status

This project has been developed until TRL4 and is currently not actively maintained.
We envision the following steps to raise the TRL from 4 to 6:
- Technical trials in security pipelines of small to midsized companies.
- Retraining of the default model using company security data.
- Validating the accuracy of the packages' classification method in relevant circumstances.
- Improving the package on shortcomings for the needs of a small to midsized company.
