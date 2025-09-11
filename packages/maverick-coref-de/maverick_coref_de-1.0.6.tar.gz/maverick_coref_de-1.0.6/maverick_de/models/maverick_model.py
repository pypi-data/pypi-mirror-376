import torch
import numpy as np
import pathlib

from transformers import AutoTokenizer

from maverick_de.models.pl_modules import BasePLModule
from maverick_de.common.util import *
from maverick_de.common.constants import *
from maverick_de.models import *

from transformers.utils.hub import cached_file as hf_cached_file

torch.set_float32_matmul_precision('medium')
torch.set_num_threads(1)

class Maverick:
    # put the pip package online
    def __init__(self, hf_name_or_path="fynnos/maverick-mes-de10", device="cuda"):
        self.device = device
        model_path = self.__get_model_path__(hf_name_or_path)
        self.model = torch.load(model_path, weights_only=False, map_location=device)
        self.tokenizer = AutoTokenizer.from_pretrained(hf_name_or_path, use_fast=True, add_prefix_space=True)

    def __get_model_path__(self, hf_name_or_path):
        try:
            path = hf_cached_file(hf_name_or_path, "model.pth")
        except:
            path = hf_name_or_path
        return path

    def __sample_type__(self, sample):
        if isinstance(sample, str):
            result = "text"
        if isinstance(sample, list):
            result = "word_tokenized"
            if len(sample) != 0 and isinstance(sample[0], list):
                result = "sentence_tokenized"
        return result

    def preprocess(self, sample):
        type = self.__sample_type__(sample)
        char_offsets = None
        if type == "text":
            nlp = download_load_spacy()
            char_offsets = []
            sentences = []
            off = 0
            s = sent_tokenize(sample)
            for sent, sentence in zip(nlp.pipe(s), s):
                char_offsets.append([(off + tok.idx, off + tok.idx + len(tok.text) - 1) for tok in sent])
                sentences.append([tok.text for tok in sent])
                off += len(sentence) + 1
            char_offsets = flatten(char_offsets)
            tokens = flatten(sentences)
            eos_len = [len(value) for value in sentences]
            eos = [sum(eos_len[0 : (i[0] + 1)]) for i in enumerate(eos_len)]
        elif type == "word_tokenized":
            nlp = download_load_spacy()
            tokens = sample
            eos = [idx + 1 for idx, tok in enumerate(tokens) if tok == "."]
            if len(eos) == 0 or eos[-1] != len(tokens):
                eos.append(len(tokens))
        elif type == "sentence_tokenized":
            sentences = sample
            tokens = flatten(sentences)
            eos_len = [len(value) for value in sentences]
            eos = [sum(eos_len[0 : (i[0] + 1)]) for i in enumerate(eos_len)]
        return tokens, eos, char_offsets

    # takes length of sequence (int) and eos_indices ([])
    # returns len x len zeros matrix with 1 in pos (start, all possible ends)
    def eos_mask(self, input_ids_len, eos_indices):
        mask = np.zeros((input_ids_len, input_ids_len))
        prec = 0
        for eos_idx in eos_indices:
            for i in range(prec, eos_idx + 1):
                for j in range(prec, eos_idx + 1):
                    mask[i][j] = 1
            prec = eos_idx
        mask = np.triu(mask)
        return mask

    @torch.no_grad()
    def predict(self, sample, singletons=False, add_gold_clusters=None, predefined_mentions=None):
        tokens, eos_indices, char_offsets = self.preprocess(sample)  # [[w1,w2,w3...], []]
        tokenized = self.tokenize(tokens, eos_indices, predefined_mentions, add_gold_clusters)

        output = self.model(
            stage="test",
            input_ids=torch.tensor(tokenized["input_ids"]).unsqueeze(0).to(self.device),
            attention_mask=torch.tensor(tokenized["attention_mask"]).unsqueeze(0).to(self.device),
            eos_mask=torch.tensor(tokenized["eos_mask"]).unsqueeze(0).to(self.device),
            tokens=[tokenized["tokens"]],
            subtoken_map=[tokenized["subtoken_map"]],
            new_token_map=[tokenized["new_token_map"]],
            singletons=singletons,
            add=tokenized["added"],
            gold_mentions=(
                None
                if tokenized["gold_mentions"] == None
                else torch.tensor(
                    self.create_mention_matrix(
                        len(tokenized["input_ids"]),
                        tokenized["gold_mentions"],
                    )
                )
                .unsqueeze(0)
                .to(self.device)
            ),
        )

        clusters_predicted = original_token_offsets(
            clusters=output["pred_dict"]["clusters"],
            subtoken_map=tokenized["subtoken_map"],
            new_token_map=tokenized["new_token_map"],
        )
        result = {}
        result["tokens"] = tokens
        result["clusters_token_offsets"] = clusters_predicted
        result["clusters_char_offsets"] = None
        result["clusters_token_text"] = [
            [" ".join(tokens[span[0] : span[1] + 1]) for span in cluster] for cluster in clusters_predicted
        ]
        result["clusters_char_text"] = None
        if char_offsets != None:
            result["clusters_char_offsets"] = [
                [(char_offsets[span[0]][0], char_offsets[span[1]][1]) for span in cluster] for cluster in clusters_predicted
            ]

        return result

    def create_mention_matrix(self, input_ids_len, mentions):
        matrix = np.zeros((input_ids_len, input_ids_len))
        for start_bpe_idx, end_bpe_idx in mentions:
            matrix[start_bpe_idx][end_bpe_idx] = 1
        return matrix

    def tokenize(self, tokens, eos_indices, gold_mentions=None, add_gold_clusters=None):
        token_to_new_token_map = []  # len() = len(tokens), contains indices of original sequence to new sequence
        new_token_map = []  # len() = len(new_tokens), contains indices of new sequence
        new_tokens = []  # contains new tokens
        for idx, token, in enumerate(tokens):
            token_to_new_token_map.append(len(new_tokens))
            new_token_map.append(idx)
            new_tokens.append(token)

        encoded_text = self.tokenizer(new_tokens, add_special_tokens=True, is_split_into_words=True)
        if gold_mentions != None:
            gold_mentions = [
                (
                    encoded_text.word_to_tokens(token_to_new_token_map[start]).start,
                    encoded_text.word_to_tokens(token_to_new_token_map[end]).end - 1,
                )
                for start, end in gold_mentions
            ]

        addedd = None
        if add_gold_clusters != None:
            addedd = [
                [
                    (
                        encoded_text.word_to_tokens(token_to_new_token_map[start]).start,
                        encoded_text.word_to_tokens(token_to_new_token_map[end]).end - 1,
                    )
                    for start, end in cluster
                ]
                for cluster in add_gold_clusters
            ]

        eos_indices = [
            encoded_text.word_to_tokens(token_to_new_token_map[eos - 1]).start
            for eos in eos_indices
            if encoded_text.word_to_tokens(token_to_new_token_map[eos - 1]) != None
        ]
        output = {
            "tokens": tokens,
            "input_ids": encoded_text["input_ids"],
            "attention_mask": encoded_text["attention_mask"],
            "subtoken_map": encoded_text.word_ids(),
            "new_token_map": new_token_map,
            "eos_mask": self.eos_mask(len(encoded_text["input_ids"]), eos_indices),
            "gold_mentions": gold_mentions,
            "added": addedd,
        }
        return output
