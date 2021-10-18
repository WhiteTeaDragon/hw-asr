from typing import List, Tuple
from speechbrain.utils.data_utils import download_file
from pyctcdecode import build_ctcdecoder

import torch
import kenlm
import shutil
import os

from hw_asr.text_encoder.char_text_encoder import CharTextEncoder
from hw_asr.utils import ROOT_PATH


class CTCCharTextEncoder(CharTextEncoder):
    EMPTY_TOK = "^"

    def __init__(self, alphabet: List[str]):
        super().__init__(alphabet)
        self.ind2char = {
            0: self.EMPTY_TOK
        }
        for text in alphabet:
            self.ind2char[max(self.ind2char.keys()) + 1] = text
        self.char2ind = {v: k for k, v in self.ind2char.items()}
        self.arch_path = None
        data_dir = ROOT_PATH / "lm_model"
        data_dir.mkdir(exist_ok=True, parents=True)
        self._data_dir = data_dir

    def ctc_decode(self, inds: List[int]) -> str:
        ans = []
        for i in range(len(inds)):
            curr_token = self.ind2char[inds[i]]
            if len(ans) == 0 or curr_token != ans[-1]:
                ans.append(curr_token)
        ans_final = []
        for i in range(len(ans)):
            if ans[i] != self.EMPTY_TOK:
                ans_final.append(ans[i])
        return ''.join(ans_final)

    def ctc_beam_search(self, probs: torch.tensor, alpha=0.5, beta=1,
                        beam_size: int = 100, device=None) -> \
            List[Tuple[str, float]]:
        """
        Performs beam search and returns a list of pairs (hypothesis,
        hypothesis probability).
        """
        assert len(probs.shape) == 2
        char_length, voc_size = probs.shape
        assert voc_size == len(self.ind2char)
        if self.arch_path is None:
            self.arch_path = self._data_dir / "4gram_big.arpa.gz"
            print(f"Loading kenlm")
            download_file("https://kaldi-asr.org/models/5/4gram_big.arpa.gz",
                          self.arch_path)
            shutil.unpack_archive(self.arch_path, self._data_dir)
            for fpath in (self._data_dir / "LM_model").iterdir():
                shutil.move(str(fpath), str(self._data_dir / fpath.name))
            os.remove(str(self.arch_path))
            shutil.rmtree(str(self._data_dir / "LM_model"))
        model = kenlm.Model(self.arch_path)
        decoder = build_ctcdecoder(list(self.char2ind.keys()), model,
            alpha=alpha,  # tuned on a val set
            beta=beta,  # tuned on a val set
        )
        hypos = decoder.decode_beams(probs, beam_size)
        for i in range(len(hypos)):
            hypos[i] = (hypos[0], hypos[-1])
        return sorted(hypos, key=lambda x: x[1], reverse=True)
