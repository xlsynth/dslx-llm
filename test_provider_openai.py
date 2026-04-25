# SPDX-License-Identifier: Apache-2.0

import provider_openai


def test_gpt_55_is_builtin_model_choice():
    assert 'gpt-5.5' in provider_openai.MODEL_CHOICES


def test_gpt_55_reasoning_effort_choices():
    expected = ('none', 'low', 'medium', 'high', 'xhigh')
    assert provider_openai.get_reasoning_effort_choices('gpt-5.5') == expected
    assert provider_openai.get_reasoning_effort_choices('openai/gpt-5.5') == expected
