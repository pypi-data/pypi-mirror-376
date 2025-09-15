# sk-serve

![deploy on pypi](https://github.com/alexliap/sk_serve/actions/workflows/publish_package.yaml/badge.svg)
![PyPI Version](https://img.shields.io/pypi/v/simple-serve?label=pypi%20package)
![Downloads](https://static.pepy.tech/badge/simple-serve)

Deployment of a Scikit-Learn pipeline with a single endpoint. Validation of input data is also supported with pydantic.

### Usage

See the [Examples](https://github.com/alexliap/sk_serve/tree/master/examples) section of the repository.

### Installation

The package exists on PyPI (with a different name though) so you can install it directly to your environment by running the command

```terminal
pip install simple-serve
```

### Dependencies

* pydantic
* fastapi
* pandas
* scikit-learn
* loguru

Additional packages for development:

* pyright
* pre-commit

### Development

If you want to contribute you fork the repository and clone it on your machine

```terminal
git clone https://github.com/alexliap/sk_serve.git
```

And after you create you environment (either venv or conda) and activate it then run this command

```terminal
pip install -e ".[dev]"
```

That way not only the required dependencies are installed but also the development ones.

Also this makes it so that when you import the code to test it, you can do it like any other module but containing the changes you made locally.

Before you decide to commit, run the following command to reformat code in order to be in the acceptable style.

```terminal
pre-commit install
pre-commit run --all-files
```
