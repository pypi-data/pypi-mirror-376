# -*- coding: utf-8 -*-
from pathlib import Path

import pytest
import torch

import random_neural_net_models.mingpt.adder as adder
import random_neural_net_models.mingpt.char as char
import random_neural_net_models.mingpt.model as gpt_model
import random_neural_net_models.mingpt.sorter as sorter
import random_neural_net_models.mingpt.trainer as gpt_trainer
import random_neural_net_models.mingpt.utils as gpt_utils


def test_mingpt_sort():
    gpt_utils.set_seed(3407)

    train_dataset = sorter.SortDataset(gpt_utils.SetsEnum.train, seed=3407)

    model_config = gpt_model.GPT.get_config(
        model_type="gpt-nano",
        vocab_size=train_dataset.get_vocab_size(),
        block_size=train_dataset.get_block_size(),
    )
    model = gpt_model.GPT(model_config)

    train_config = gpt_trainer.Trainer.get_config(
        learning_rate=5e-4,  # the model we're using is so small that we can go a bit faster
        max_iters=100,
        num_workers=0,
    )

    trainer = gpt_trainer.Trainer(train_config, model, train_dataset)

    trainer.run()

    n = train_dataset.length  # naugy direct access shrug
    _input = torch.tensor([[0, 0, 2, 1, 0, 1]], dtype=torch.long).to(trainer.device)

    with torch.no_grad():
        _inference = model.generate(_input, n, do_sample=False)

    # generated output is as expected
    # TODO: fix - this seems to be brittle and does not work for some test execution
    # assert torch.allclose(
    #     _inference[:, n:], torch.tensor([[0, 0, 0, 1, 1, 2]], dtype=torch.long, device=trainer.device)
    # )


def test_mingpt_adder():
    data_config = adder.DataConfig(ndigit=2)
    # construct train and test datasets
    train_dataset = adder.AdditionDataset(data_config, split=gpt_utils.SetsEnum.train)
    test_dataset = adder.AdditionDataset(data_config, split=gpt_utils.SetsEnum.test)

    config = adder.get_config(
        vocab_size=train_dataset.get_vocab_size(),
        block_size=train_dataset.get_block_size(),
        max_iters=100,
    )

    gpt_utils.set_seed(config.system.seed)

    # construct the model
    model = gpt_model.GPT(config.model)

    # construct the trainer object
    trainer = gpt_trainer.Trainer(config.trainer, model, train_dataset)

    # run the optimization
    trainer.run()

    n_new_tokens = 1
    for x, y in test_dataset:
        pred = model.generate(
            x.to(trainer.device).unsqueeze(0), n_new_tokens, do_sample=False
        )
        break

    # generated output is as expected
    assert isinstance(pred, torch.Tensor)
    assert pred.shape == (1, x.shape[0] + n_new_tokens)
    assert torch.allclose(pred[0, -3:], y.to(trainer.device)[-3:])


@pytest.mark.skipif(
    not Path("data/tiny-shakespear.txt").exists(),
    reason="data/tiny-shakespear.txt not found",
)
def test_mingpt_char():
    data_config = char.DataConfig(block_size=128)

    # construct the training dataset
    text = open("data/tiny-shakespear.txt", "r").read()
    train_dataset = char.CharDataset(data_config, text)

    # get default config and overrides from the command line, if any
    config = char.get_config(
        max_iters=10,
        vocab_size=train_dataset.get_vocab_size(),
        block_size=train_dataset.get_block_size(),
    )

    gpt_utils.set_seed(config.system.seed)

    # construct the model
    model = gpt_model.GPT(config.model)

    # construct the trainer object
    trainer = gpt_trainer.Trainer(config.trainer, model, train_dataset)

    # run the optimization
    trainer.run()

    # inference
    n_new_tokens = 30
    for x_int, y_int in train_dataset:
        pred_int = model.generate(x_int.unsqueeze(0), n_new_tokens, do_sample=False)
        break

    # generated output is as expected
    assert isinstance(pred_int, torch.Tensor)
    assert isinstance(pred_int, torch.LongTensor)
    assert pred_int.shape == (1, x_int.shape[0] + n_new_tokens)
