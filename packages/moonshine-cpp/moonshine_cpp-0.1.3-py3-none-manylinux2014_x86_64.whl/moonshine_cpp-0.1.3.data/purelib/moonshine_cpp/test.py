import argparse
import moonshine_cpp
import os

def test():
    """
    Test the Moonshine module.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--wav_path", type=str, default=os.path.join(os.path.dirname(moonshine_cpp.__file__), "test-data/beckett.wav"))
    parser.add_argument("--language", type=str, default="en")
    parser.add_argument("--model_dir_url", type=str, default=None)
    parser.add_argument("--model_dir_url_suffix", type=str, default="")
    parser.add_argument("--model_dir_path", type=str, default=None)
    parser.add_argument("--verbose", default=False, action="store_true")
    parser.add_argument("--onnx_suffix", type=str, default="ort")
    parser.add_argument("--model_type", type=str, default="base", choices=["base", "tiny"])
    parser.add_argument("--force_download", default=False, action="store_true")
    args = parser.parse_args()

    wav_path = args.wav_path
    del args.wav_path

    model = moonshine_cpp.MoonshineModel(**vars(args))
    text = model.transcribe_wav(wav_path)
    print(text)

if __name__ == "__main__":
    test()