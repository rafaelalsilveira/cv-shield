import re


def normalize_text(text):
    # Substitui qualquer sequência de espaços em branco (incluindo quebras
    # de linha "\n" que o pypdf insere onde o PDF quebra a linha visualmente)
    # por um único espaço. Isso permite comparar frases que, no PDF original,
    # aparecem "cortadas" em duas linhas.
    return re.sub(r"\s+", " ", text)