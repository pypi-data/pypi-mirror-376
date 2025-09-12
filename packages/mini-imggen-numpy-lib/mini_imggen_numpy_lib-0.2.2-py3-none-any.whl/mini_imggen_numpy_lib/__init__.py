# mini_imggen_numpy_lib/__init__.py

"""
mini_imggen_numpy_lib
--------------------
Librairie Python pour génération d'images et texte avec Numpy, sans interface graphique.
"""

from .mini_imggen_numpy_lib import (
    launch_gradio,
    TOKEN_VOCAB_SIZE,
    set_seed,
    TextVocab,
    Config,
    ARBigramText,
    build_dataset,
    load_and_preprocess_image,
    image_to_tokens,
    tokens_to_image,
    train_model,
    generate_image_from_model,
    load_text_dataset,
    train_text_model,
    generate_text_from_model,
)

__all__ = [
    'launch_gradio',           # <<< ajoute ça aussi
    'TOKEN_VOCAB_SIZE',
    'set_seed',
    'TextVocab',
    'Config',
    'ARBigramText',
    'build_dataset',
    'load_and_preprocess_image',
    'image_to_tokens',
    'tokens_to_image',
    'train_model',
    'generate_image_from_model',
    'load_text_dataset',
    'train_text_model',
    'generate_text_from_model',
]