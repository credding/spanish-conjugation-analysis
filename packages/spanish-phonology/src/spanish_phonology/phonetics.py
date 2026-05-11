VOWELS = "aáeéiíoóuúü"
STRESSED_VOWELS = "áéíóú"
STRONG_VOWELS = "aáeéíoóú"
WEAK_VOWELS = "iuü"
HARD_VOWELS = "aáoóuúü"
SOFT_VOWELS = "eéií"

TX_ADD_STRESS = str.maketrans("aeiou", "áéíóú")
TX_REMOVE_STRESS = str.maketrans("áéíóú", "aeiou")
TX_REMOVE_DIACRITICS = str.maketrans("áéíóúü", "aeiouu")
