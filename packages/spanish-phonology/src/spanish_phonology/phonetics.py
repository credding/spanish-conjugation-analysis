VOWELS = "aáeéiíoóuúü"
STRESSED_VOWELS = "áéíóú"
STRONG_VOWELS = "aáeéíoóú"
WEAK_VOWELS = "iuü"
HARD_VOWELS = "aáoóuúü"
SOFT_VOWELS = "eéií"

TRANSLATE_ADD_STRESS = str.maketrans("aeiou", "áéíóú")
TRANSLATE_REMOVE_STRESS = str.maketrans("áéíóú", "aeiou")
TRANSLATE_REMOVE_DIACRITICS = str.maketrans("áéíóúü", "aeiouu")
