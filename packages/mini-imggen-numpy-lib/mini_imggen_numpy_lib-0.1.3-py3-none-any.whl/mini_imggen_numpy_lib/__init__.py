"""
mini_imggen_numpy_lib
--------------------
Librairie Python pour génération d'images et de texte avec NumPy (sans dépendances ML lourdes).

Exports principaux:
- TextVocab
- ARBigramText, Config
- Images: build_dataset, load_and_preprocess_image, image_to_tokens, tokens_to_image,
          train_model, generate_image_from_model
- Texte : load_text_dataset, train_text_model, generate_text_from_model
- UI (optionnelle): launch_gradio_image_demo, launch_gradio_text_demo
"""

# Importe tout depuis le module principal
from .mini_imggen_numpy_lib import (
    # core / utils
    TOKEN_VOCAB_SIZE, set_seed, tokenize_text,
    # image pipeline
    load_and_preprocess_image, image_to_tokens, tokens_to_image,
    # text vocab + model
    TextVocab, ARBigramText, Config,
    # training / inference
    build_dataset, train_model, generate_image_from_model,
    load_text_dataset, train_text_model, generate_text_from_model,
)

# Helpers Gradio (définis dans mini_imggen_numpy_lib.py)
from .mini_imggen_numpy_lib import (
    launch_gradio_image_demo,
    launch_gradio_text_demo,
)

__all__ = [
    'TOKEN_VOCAB_SIZE', 'set_seed', 'tokenize_text',
    'TextVocab', 'load_and_preprocess_image', 'image_to_tokens', 'tokens_to_image',
    'ARBigramText', 'Config', 'build_dataset', 'train_model', 'generate_image_from_model',
    'load_text_dataset', 'train_text_model', 'generate_text_from_model',
    'launch_gradio_image_demo', 'launch_gradio_text_demo',
]