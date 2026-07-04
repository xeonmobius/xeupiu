import os

from google.cloud import translate
from xeupiu.config import CONFIG

import openai
import deepl
import ctranslate2
import sentencepiece as spm
from huggingface_hub import snapshot_download

from xeupiu.constants import format_translated_text
from xeupiu.database import Database

OPENING_QUOTES = ["「", "『", "【", "（", "［", "《", "〈", "〔", "｛", "〖", "〘", "〚", "〝"]
CLOSING_QUOTES = ["」", "』", "】", "）", "］", "》", "〉", "〕", "｝", "〗", "〙", "〛", "〞"]

SUGOI_MODEL_REPO = "entai2965/sugoi-v4-ja-en-ctranslate2"
SUGOI_MODEL_DIR = os.path.join("data", "models", "sugoi-v4-ja-en")

openai.organization = CONFIG["translation"]["openai"]["organization"]
openai.api_key = CONFIG["translation"]["openai"]["api_key"]

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CONFIG["translation"]["google_cloud"]["credential_path"]

class Translator():
    def __init__(self):
        self.backend = CONFIG["translation"]["backend"]
        self.deepl_model = None
        self.sugoi_translator = None
        self.sugoi_sp_ja = None
        self.sugoi_sp_en = None

    def translate_openai(self, desc):
        completion = openai.ChatCompletion.create(
            model="gpt-4-0125-preview",
            messages=[
                {"role": "system",
                 "content": "A chat between an user and an artificial intelligence assistant, "
                            "specialized in translation from japanese to english."},
                {"role": "user", "content": desc},
            ]
        )
        print(f"Tokens used: {completion.usage.total_tokens}")
        return completion.choices[0].message['content']

    def translate_google_cloud(self, text, project_id="xeupiu"):
        client = translate.TranslationServiceClient()
        location = "global"
        parent = f"projects/{project_id}/locations/{location}"

        response = client.translate_text(
            request={
                "parent": parent,
                "contents": [text],
                "mime_type": "text/plain",
                "source_language_code": "ja",
                "target_language_code": "en-US",
            }
        )

        return response.translations[0].translated_text

    def translate_deepl(self, text):
        if CONFIG["translation"]["deepl"]["api_key"] == "" or CONFIG["translation"]["deepl"]["api_key"] is None:
            # raise Exception("DeepL API key is not set.")
            print("WARNING: DeepL API key is not set. Returning japanese text.")
            return text

        if self.deepl_model is None:
            self.deepl_model = deepl.Translator(auth_key=CONFIG["translation"]["deepl"]["api_key"])

        return self.deepl_model.translate_text(text, source_lang="JA", target_lang=CONFIG["translation"]["lang"]).text

    def _ensure_sugoi_loaded(self):
        if self.sugoi_translator is not None:
            return

        if not os.path.isdir(SUGOI_MODEL_DIR) or not os.listdir(SUGOI_MODEL_DIR):
            print(f"Sugoi model not found at '{SUGOI_MODEL_DIR}'. Downloading from HuggingFace (~1.5GB, one-time)...")
            os.makedirs(SUGOI_MODEL_DIR, exist_ok=True)
            snapshot_download(repo_id=SUGOI_MODEL_REPO, local_dir=SUGOI_MODEL_DIR)
            print("Sugoi model download complete.")

        device = CONFIG["translation"]["sugoi"]["device"]
        self.sugoi_translator = ctranslate2.Translator(SUGOI_MODEL_DIR, device=device)

        spm_dir = os.path.join(SUGOI_MODEL_DIR, "spm")
        self.sugoi_sp_ja = spm.SentencePieceProcessor(os.path.join(spm_dir, "spm.ja.nopretok.model"))
        self.sugoi_sp_en = spm.SentencePieceProcessor(os.path.join(spm_dir, "spm.en.nopretok.model"))
        print(f"Sugoi model loaded (device={device}).")

    def translate_sugoi(self, text):
        self._ensure_sugoi_loaded()

        beam_size = CONFIG["translation"]["sugoi"]["beam_size"]
        tokenized = [self.sugoi_sp_ja.encode(text, out_type=str)]
        results = self.sugoi_translator.translate_batch(source=tokenized, beam_size=beam_size)
        translated = self.sugoi_sp_en.decode(results[0].hypotheses[0]).replace('<unk>', '')

        return translated

    def translate(self, text, backend=None):
        if not text:
            return ""

        text_to_translate = text
        if text[0] in OPENING_QUOTES and text[-1] not in CLOSING_QUOTES:
            text_to_translate = text[1:] # Remove opening quote

        text_to_translate, date_jp = Database.generalize_date(text_to_translate)

        if not backend:
            backend = CONFIG["translation"]["backend"]

        if backend == "google_cloud":
            translated_text = self.translate_google_cloud(text_to_translate)
        elif backend == "openai":
            translated_text = self.translate_openai(text_to_translate)
        elif backend == "deepl":
            translated_text = self.translate_deepl(text_to_translate)
        elif backend == "sugoi":
            translated_text = self.translate_sugoi(text_to_translate)
        elif backend == "none":
            translated_text = text
        else:
            raise Exception(f"Unknown backend: {backend}")

        translated_text = format_translated_text(text, translated_text)

        return translated_text

    @staticmethod
    def should_translate_text(text):
        if text == "":
            return False
        if len(text) == 1:
            return False
        return True

if __name__ == "__main__":
    txt_jp = "伊集院って、あの金持ちのか．．．。嫌なクラスになっちまったなぁ。"
    tt = Translator()

    print(f"Google Cloud:")
    txt_en = tt.translate_google_cloud(txt_jp, "xeupiu")
    print(txt_en)

    print(f"OpenAI:")
    txt_en = tt.translate_openai(txt_jp)
    print(txt_en)

    print(f"DeepL:")
    txt_en = tt.translate_deepl(txt_jp)
    print(txt_en)

    print(f"Sugoi:")
    txt_en = tt.translate_sugoi(txt_jp)
    print(txt_en)