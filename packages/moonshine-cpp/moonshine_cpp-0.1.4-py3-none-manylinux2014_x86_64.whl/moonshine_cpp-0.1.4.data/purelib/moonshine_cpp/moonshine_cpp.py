import ctypes
import os
import platform
import tempfile
import urllib.request

ORT_VERSION = "1.22.1"

if platform.system() == "Darwin":
    OS = "macos"
else:
    OS = "linux"

if OS == "macos":
    ORT_LIB_NAME = f"libonnxruntime.{ORT_VERSION}.dylib"
    MOONSHINE_LIB_NAME = "libmoonshine.dylib"
else:
    ORT_LIB_NAME = f"libonnxruntime.so.{ORT_VERSION}"
    MOONSHINE_LIB_NAME = "libmoonshine.so"

ort_library_path = os.path.join(os.path.dirname(__file__), ORT_LIB_NAME)
ort_lib = ctypes.CDLL(ort_library_path)

moonshine_library_path = os.path.join(os.path.dirname(__file__), MOONSHINE_LIB_NAME)
moonshine_lib = ctypes.CDLL(moonshine_library_path)

MOONSHINE_MODEL_TYPE_TINY = 0
MOONSHINE_MODEL_TYPE_BASE = 1

moonshine_lib.moonshine_load_model.argtypes = (
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_int32,
)
moonshine_lib.moonshine_load_model.restype = ctypes.c_int

moonshine_lib.moonshine_transcribe.argtypes = (
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_float),
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_char_p),
)
moonshine_lib.moonshine_transcribe.restype = ctypes.c_int

moonshine_lib.moonshine_transcribe_wav.argtypes = (
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.POINTER(ctypes.c_char_p),
)
moonshine_lib.moonshine_transcribe_wav.restype = ctypes.c_int

moonshine_lib.moonshine_free_model.argtypes = (ctypes.c_int,)
moonshine_lib.moonshine_free_model.restype = None

moonshine_lib.moonshine_free_text.argtypes = (ctypes.c_char_p,)
moonshine_lib.moonshine_free_text.restype = None

SUPPORTED_LANGUAGE_INFO = {
    "en": {"type": "base", "url_dir": None}, 
    "es": {"type": "base", "url_dir": "https://huggingface.co/UsefulSensors/moonshine-es/resolve/main/onnx/merged/base/float/"}, 
    "ar": {"type": "tiny", "url_dir": "https://huggingface.co/UsefulSensors/moonshine/resolve/main/onnx/merged/tiny-ar/float/"}, 
    "ko": {"type": "base", "url_dir": "https://huggingface.co/UsefulSensors/moonshine/resolve/main/onnx/merged/tiny-ko/float/"},
    "zh": {"type": "tiny", "url_dir": "https://huggingface.co/UsefulSensors/moonshine/resolve/main/onnx/merged/tiny-zh/float/"}, 
    "ja": {"type": "tiny", "url_dir": "https://huggingface.co/UsefulSensors/moonshine/resolve/main/onnx/merged/tiny-ja/float/"}, 
    "vi": {"type": "base", "url_dir": "https://huggingface.co/UsefulSensors/moonshine/resolve/main/onnx/merged/tiny-vi/float/"}, 
    "uk": {"type": "tiny", "url_dir": "https://huggingface.co/UsefulSensors/moonshine/resolve/main/onnx/merged/tiny-uk/float/"},
}

def download_file(url: str, path: str, verbose: bool = False, force_download: bool = False):
    # With progress callback
    def download_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(downloaded * 100 / total_size, 100)
        if total_size < 1024:
            total_size_str = f"{total_size} bytes"
        elif total_size < 1024 * 1024:
            total_size_str = f"{total_size // 1024} KB"
        else:
            total_size_str = f"{total_size // (1024 * 1024)} MB"
        if verbose:
            print(f"Downloaded: {percent:.1f}% of {total_size_str}", end="\r")

    try:
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
            assert os.path.exists(os.path.dirname(path)), (
                f"Failed to create directory {os.path.dirname(path)}"
            )
        if not force_download and os.path.exists(path):
            if verbose:
                print(f"File '{path}' already exists, skipping download")
            return
        if verbose:
            print(f"Downloading file '{url}' to '{path}'")

        urllib.request.urlretrieve(
            url,
            path,
            reporthook=download_progress,
        )
    except Exception as e:
        print(f"Error downloading file {url} to {path}: {e}")
        raise e

class MoonshineModel:
    model_handle: ctypes.c_int

    model_dir_path: str = None


    def __init__(
        self,
        py_encoder_model_path: str = None,
        py_decoder_model_path: str = None,
        py_tokenizer_path: str = None,
        model_dir_url: str = None,
        model_dir_url_suffix: str = "",
        model_dir_path: str = None,
        verbose: bool = False,
        onnx_suffix: str = "ort",
        language: str = "en",
        model_type: str = "base",
        force_download: bool = False,
        suppress_copyright_notice: bool = False,
    ):
        if (
            py_encoder_model_path is None
            and py_decoder_model_path is None
            and py_tokenizer_path is None
            and model_dir_url is None
            and model_dir_path is None
        ):
            if language == "en":
                # These are included in the Python package.
                model_dir_path = os.path.join(
                    os.path.dirname(__file__), f"models/base-en/"
                )
            else:
                # If we just have the language argument, download the models from HuggingFace.
                assert language in SUPPORTED_LANGUAGE_INFO, (
                    f"language {language} is not supported"
                )
                if not suppress_copyright_notice:
                    print("Using non-commercial models from Moonshine AI. For commercial use, see https://moonshine.ai/license. Use MoonshineModel(suppress_copyright_notice=True) to suppress this notice.")
                language_info = SUPPORTED_LANGUAGE_INFO[language]
                model_dir_url = language_info["url_dir"]
                model_type = language_info["type"]
                if model_dir_url_suffix == "":
                    model_dir_url_suffix = "?download=true"

        if model_dir_url is not None:
            assert model_dir_url.startswith("http://") or model_dir_url.startswith(
                "https://"
            ), "model_dir_url must be a valid URL"
            assert model_dir_url.endswith("/"), "model_dir_url must end with a slash"
            assert py_encoder_model_path is None, (
                "py_encoder_model_path cannot be used with model_dir_url"
            )
            assert py_decoder_model_path is None, (
                "py_decoder_model_path cannot be used with model_dir_url"
            )
            assert py_tokenizer_path is None, (
                "py_tokenizer_path cannot be used with model_dir_url"
            )
            if model_dir_path is None:
                # Models are downloaded and cached in the user's home directory by default.
                self.model_dir_path = os.path.join(
                    os.path.expanduser("~"), "moonshine-models", f"{language}-{model_type}"
                )
            else:
                self.model_dir_path = model_dir_path
            py_encoder_model_path = os.path.join(
                self.model_dir_path, "encoder_model." + onnx_suffix
            )
            py_decoder_model_path = os.path.join(
                self.model_dir_path, "decoder_model_merged." + onnx_suffix
            )
            py_tokenizer_path = os.path.join(self.model_dir_path, "tokenizer.bin")
            download_file(
                model_dir_url + "encoder_model." + onnx_suffix + model_dir_url_suffix,
                py_encoder_model_path,
                verbose,
                force_download,
            )
            download_file(
                model_dir_url + "decoder_model_merged." + onnx_suffix + model_dir_url_suffix,
                py_decoder_model_path,
                verbose,
                force_download,
            )
            download_file(model_dir_url + "tokenizer.bin" + model_dir_url_suffix, py_tokenizer_path, verbose, force_download)
        elif model_dir_path is not None:
            assert py_encoder_model_path is None, (
                "py_encoder_model_path cannot be used with model_dir_path"
            )
            assert py_decoder_model_path is None, (
                "py_decoder_model_path cannot be used with model_dir_path"
            )
            assert py_tokenizer_path is None, (
                "py_tokenizer_path cannot be used with model_dir_path"
            )
            self.model_dir_path = model_dir_path
            py_encoder_model_path = os.path.join(
                self.model_dir_path, "encoder_model." + onnx_suffix
            )
            py_decoder_model_path = os.path.join(
                self.model_dir_path, "decoder_model_merged." + onnx_suffix
            )
            py_tokenizer_path = os.path.join(self.model_dir_path, "tokenizer.bin")

        assert os.path.exists(py_encoder_model_path), (
            f"py_encoder_model_path {py_encoder_model_path} does not exist"
        )
        assert os.path.exists(py_decoder_model_path), (
            f"py_decoder_model_path {py_decoder_model_path} does not exist"
        )
        assert os.path.exists(py_tokenizer_path), (
            f"py_tokenizer_path {py_tokenizer_path} does not exist"
        )

        assert os.path.exists(py_encoder_model_path), (
            f"py_encoder_model_path {py_encoder_model_path} does not exist"
        )
        assert os.path.exists(py_decoder_model_path), (
            f"py_decoder_model_path {py_decoder_model_path} does not exist"
        )
        assert os.path.exists(py_tokenizer_path), (
            f"py_tokenizer_path {py_tokenizer_path} does not exist"
        )

        self.model_dir_path = os.path.dirname(py_encoder_model_path)

        encoder_utf8_bytes: bytes = py_encoder_model_path.encode("utf-8")
        c_encoder_model_path: ctypes.c_char_p = encoder_utf8_bytes

        decoder_utf8_bytes: bytes = py_decoder_model_path.encode("utf-8")
        c_decoder_model_path: ctypes.c_char_p = decoder_utf8_bytes

        tokenizer_utf8_bytes: bytes = py_tokenizer_path.encode("utf-8")
        c_tokenizer_path: ctypes.c_char_p = tokenizer_utf8_bytes

        assert model_type in ["base", "tiny"], "model_type_str must be 'base' or 'tiny'"
        model_type_int: ctypes.c_int32 = MOONSHINE_MODEL_TYPE_BASE if model_type == "base" else MOONSHINE_MODEL_TYPE_TINY

        self.model_handle = moonshine_lib.moonshine_load_model(
            c_encoder_model_path, c_decoder_model_path, c_tokenizer_path, model_type_int
        )

        if self.model_handle == -1:
            raise MemoryError(
                f"MoonshineModel({py_encoder_model_path}, {py_decoder_model_path}, {py_tokenizer_path}) failed"
            )

    def __del__(self):
        if "model_handle" in self.__dict__ and self.model_handle != -1:
            moonshine_lib.moonshine_free_model(self.model_handle)
            self.model_handle = -1

    def transcribe(self, py_audio_data: ctypes.Array[ctypes.c_float]):
        if self.model_handle == -1:
            raise Exception("Moonshine model is invalid")
        c_text: ctypes.c_char_p = ctypes.c_char_p(0)
        c_audio_data: ctypes.c_float_p = ctypes.c_float_p(py_audio_data)
        c_audio_data_size: ctypes.c_size_t = len(py_audio_data)
        error: ctypes.c_int = moonshine_lib.moonshine_transcribe(
            self.model_handle, c_audio_data, c_audio_data_size, ctypes.byref(c_text)
        )
        if error != 0:
            raise Exception(f"Moonshine transcribe failed with error code {error}")
        py_text = c_text.decode("utf-8")
        moonshine_lib.moonshine_free_text(c_text)
        return py_text

    def transcribe_wav(self, py_wav_path: str):
        if self.model_handle == -1:
            raise Exception("Moonshine model is invalid")
        wav_utf8_bytes: bytes = py_wav_path.encode("utf-8")
        c_wav_path: ctypes.c_char_p = wav_utf8_bytes

        c_text: ctypes.c_char_p = ctypes.c_char_p(0)
        error: ctypes.c_int = moonshine_lib.moonshine_transcribe_wav(
            self.model_handle, c_wav_path, ctypes.byref(c_text)
        )
        if error != 0:
            raise Exception(f"Moonshine transcribe wav failed with error code {error}")
        py_text = c_text.value.decode("utf-8")
        moonshine_lib.moonshine_free_text(c_text)
        return py_text