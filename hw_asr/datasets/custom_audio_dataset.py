import logging
from pathlib import Path

import torchaudio

from hw_asr.base.base_dataset import BaseDataset
from hw_asr.text_encoder.ctc_char_text_encoder import CTCCharTextEncoder
from hw_asr.utils.parse_config import ConfigParser

logger = logging.getLogger(__name__)


class CustomAudioDataset(BaseDataset):
    def __init__(self, data, *args, **kwargs):
        index = data
        for entry in data:
            assert "path" in entry
            assert Path(entry["path"]).exists()
            entry["path"] = str(Path(entry["path"]).absolute().resolve())
            entry["text"] = entry.get("text", "")
            t_info = torchaudio.info(entry["path"], encoding="mp3")
            entry["audio_len"] = t_info.num_frames / t_info.sample_rate

        super().__init__(index, *args, **kwargs)


if __name__ == "__main__":
    text_encoder = CTCCharTextEncoder.get_simple_alphabet()
    config_parser = ConfigParser.get_default_configs()

    data = [
        {
            "path": "data/datasets/mini_librispeech/LibriSpeech"
                    "/dev-clean-2/84/121550/84-121550-0000.flac",
            "text": "BUT WITH FULL RAVISHMENT THE HOURS OF PRIME SINGING "
                    "RECEIVED THEY IN THE MIDST OF LEAVES THAT EVER BORE A "
                    "BURDEN TO THEIR RHYMES "
        },
        {
            "path": "data/datasets/mini_librispeech/LibriSpeech/"
                    "dev-clean-2/84/121550/84-121550-0001.flac",
        }
    ]

    ds = CustomAudioDataset(data, text_encoder=text_encoder,
                            config_parser=config_parser)
    print("[0]")
    print(ds[0])
    print("[1]")
    print(ds[1])
