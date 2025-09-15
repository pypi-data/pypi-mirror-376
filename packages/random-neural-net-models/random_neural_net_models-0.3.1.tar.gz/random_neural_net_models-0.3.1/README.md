# random neural nets

> Implementations of a random selection of artificial neural net based models and methods.

[![Tests](https://github.com/eschmidt42/random-neural-net-models/actions/workflows/test.yml/badge.svg)](https://github.com/eschmidt42/random-neural-net-models/actions/workflows/test.yml)
[![codecov](https://codecov.io/github/eschmidt42/random-neural-net-models/graph/badge.svg?token=43GQH6AU2U)](https://codecov.io/github/eschmidt42/random-neural-net-models)

## Python version

Development is done using [`uv`](https://docs.astral.sh/uv/getting-started/installation/), pinning the python version to the one in the file `.python-version`.

## Installation (on Linux)

```shell
pip install random-neural-net-models
```

or

```shell
uv add random-neural-net-models
```

For package development / notebooks shenanigans:

```shell
git clone https://github.com/eschmidt42/random-neural-net-models.git
cd random-neural-net-models
make install-dev-env
```


## Usage

See jupyter notebooks in [`nbs/`](https://github.com/eschmidt42/random-neural-net-models/tree/main/nbs) for:
* fastai style learner with tensordict: `learner-example.ipynb`
* perceptron: `perceptron.ipynb`
* backpropagation: `backpropagation_rumelhart1986.ipynb`
* convolution: `convolution_lecun1990.ipynb`
* cnn autoencoder:
    * mnist: `cnn_autoencoder_fastai2022.ipynb`
    * fashion mnist: `cnn_autoencoder_fastai2022_fashion.ipynb`
* variational autoencoder:
    * dense: `dense_variational_autoencoder_fastai2022.ipynb`
    * cnn+dense: `cnn_variational_autoencoder_fastai2022.ipynb`
* optimizers: `stochastic_optimization_methods.ipynb`
* resnet: `resnet_fastai2022.ipynb`
* unet:
    * `unet_fastai2022.ipynb`
    * `unet-isbi2012`
* diffusion (unet + noise):
  * `diffusion_fastai2022.ipynb`
  * `diffusion_fastai2022_learner.ipynb`
  * `diffusion_fastai2022_learner_with_attention.ipynb`
* [mingpt](https://github.com/karpathy/minGPT):
    * `mingpt_sort.ipynb`
    * `mingpt_char.ipynb`
    * `mingpt_adder.ipynb`
* transformer: `language-model.ipynb`
* tokenization: `tokenization.ipynb`
* tabular:
  * `tabular-fastai-classification.ipynb`
  * `tabular-fastai-classification-with-missingness.ipynb`
  * `tabular-fastai-classification-with-missingness-and-categories.ipynb`
  * `tabular-fastai-regression.ipynb`
  * `tabular-fastai-regression-with-missingness.ipynb`
  * `tabular-fastai-regression-with-missingness-and-categories.ipynb`
  * `tabular-variational-auto-encoder.ipynb`
  * `reusing-vae-for-classification.ipynb`
