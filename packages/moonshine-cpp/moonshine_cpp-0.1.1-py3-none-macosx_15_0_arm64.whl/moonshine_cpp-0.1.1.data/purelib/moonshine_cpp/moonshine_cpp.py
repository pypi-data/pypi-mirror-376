import ctypes
import os
import platform

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

moonshine_lib.moonshine_load_model.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p)
moonshine_lib.moonshine_load_model.restype = ctypes.c_int

moonshine_lib.moonshine_transcribe.argtypes = (ctypes.c_int, ctypes.POINTER(ctypes.c_float), ctypes.c_size_t, ctypes.POINTER(ctypes.c_char_p))
moonshine_lib.moonshine_transcribe.restype = ctypes.c_int

moonshine_lib.moonshine_transcribe_wav.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p))
moonshine_lib.moonshine_transcribe_wav.restype = ctypes.c_int

moonshine_lib.moonshine_free_model.argtypes = (ctypes.c_int,)
moonshine_lib.moonshine_free_model.restype = None

moonshine_lib.moonshine_free_text.argtypes = (ctypes.c_char_p,)
moonshine_lib.moonshine_free_text.restype = None

class MoonshineModel:
    model_handle: ctypes.c_int
    
    def __init__(self, py_encoder_model_path: str, py_decoder_model_path: str, py_tokenizer_path: str):
        encoder_utf8_bytes: bytes = py_encoder_model_path.encode('utf-8')
        c_encoder_model_path: ctypes.c_char_p = encoder_utf8_bytes

        decoder_utf8_bytes: bytes = py_decoder_model_path.encode('utf-8')
        c_decoder_model_path: ctypes.c_char_p = decoder_utf8_bytes

        tokenizer_utf8_bytes: bytes = py_tokenizer_path.encode('utf-8')
        c_tokenizer_path: ctypes.c_char_p = tokenizer_utf8_bytes

        self.model_handle = moonshine_lib.moonshine_load_model(
            c_encoder_model_path,
            c_decoder_model_path,
            c_tokenizer_path)

        if self.model_handle == -1:
            raise MemoryError(f"MoonshineModel({py_encoder_model_path}, {py_decoder_model_path}, {py_tokenizer_path}) failed")
    
    def __del__(self):
        if self.model_handle != -1:
            moonshine_lib.moonshine_free_model(self.model_handle)
            self.model_handle = -1
    
    def transcribe(self, py_audio_data: ctypes.Array[ctypes.c_float]):
        if self.model_handle == -1:
            raise Exception("Moonshine model is invalid")
        c_text: ctypes.c_char_p = ctypes.c_char_p(0)
        c_audio_data: ctypes.c_float_p = ctypes.c_float_p(py_audio_data)
        c_audio_data_size: ctypes.c_size_t = len(py_audio_data)
        error: ctypes.c_int = moonshine_lib.moonshine_transcribe(
            self.model_handle, c_audio_data, c_audio_data_size, ctypes.byref(c_text))
        if error != 0:
            raise Exception(f"Moonshine transcribe failed with error code {error}")
        py_text = c_text.decode('utf-8')
        moonshine_lib.moonshine_free_text(c_text)
        return py_text


    def transcribe_wav(self, py_wav_path: str):
        if self.model_handle == -1:
            raise Exception("Moonshine model is invalid")
        wav_utf8_bytes: bytes = py_wav_path.encode('utf-8')
        c_wav_path: ctypes.c_char_p = wav_utf8_bytes

        c_text: ctypes.c_char_p = ctypes.c_char_p(0)
        error: ctypes.c_int = moonshine_lib.moonshine_transcribe_wav(
            self.model_handle, c_wav_path, ctypes.byref(c_text))
        if error != 0:
            raise Exception(f"Moonshine transcribe wav failed with error code {error}")
        py_text = c_text.value.decode('utf-8')
        moonshine_lib.moonshine_free_text(c_text)
        return py_text

