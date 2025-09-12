# Copyright 2024 CVS Health and/or one of its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import List, Union

import numpy as np
from rouge_score import rouge_scorer

from langfair.metrics.counterfactual.metrics.baseclass.metrics import Metric


class RougelSimilarity(Metric):
    def __init__(self, rouge_metric: str = "rougeL", how: str = "mean") -> None:
        """Compute variations of social group substitutions of language models. This class
        enables calculation of counterfactual ROUGE-L. For more information on this metric, refer to:
        https://arxiv.org/abs/2407.10853

        Parameters
        ----------
        rouge_metric : {'rougeL','rougeLsum'}, default='rougeL'
            Specifies which ROUGE metric to use. If sentence-wise assessment is preferred, select 'rougeLsum'.

        how : {'mean','pairwise'}
            Specifies whether to return the mean rougel similarity over all counterfactual pairs or a list containing rougel
            distance for each pair.
        """
        assert how in [
            "mean",
            "pairwise",
        ], "langfair: Only 'mean' and 'pairwise' are supported."
        assert how in [
            "mean",
            "pairwise",
        ], "langfair: Only 'mean' and 'pairwise' are supported."
        assert rouge_metric in [
            "rougeL",
            "rougeLsum",
        ], """langfair: Only 'rougeL' and 'rougeLsums' are supported."""
        self.name = "RougeL Similarity"
        self.how = how
        self.rouge_scorer = rouge_scorer.RougeScorer([rouge_metric], use_stemmer=True)
        self.rouge_metric = rouge_metric

    def evaluate(
        self, texts1: List[str], texts2: List[str]
    ) -> Union[float, List[float]]:
        """
        Returns mean Rouge-L score between two lists of generated outputs.

        Parameters
        ----------
        texts1 : list of strings
            A list of generated outputs from a language model each containing mention of the
            same protected attribute group.

        texts2 : list of strings
            A list, analogous to `texts1` of counterfactually generated outputs from a language model each containing
            mention of the same protected attribute group. The mentioned protected attribute group must be a different
            group within the same protected attribute as mentioned in `texts1`.

        Returns
        -------
        float
            Mean ROUGE-L score for provided lists of texts.
        """
        rouge_scores = [
            self.rouge_scorer.score(t1, t2)[self.rouge_metric].fmeasure
            for t1, t2 in zip(texts1, texts2)
        ]

        return np.mean(rouge_scores) if self.how == "mean" else rouge_scores
