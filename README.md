# Spanish Conjugation Analysis

The goal of this project is to generate a dataset that supports exploration and discovery of the Spanish language for
learners approaching Spanish as a second language. A detailed analysis of Spanish verb conjugation patterns and
irregularities is generated, a topic that often trips up Spanish language learners. As well as relationships between
verb forms and other non-verb vocabulary that sound alike.

Also present is a collection of [submodules](#submodules) for analyzing Spanish phonetics and for generating regular
Spanish verb conjugations.

## Quick start

### Dependencies

The project environment uses Python 3.14, and it is compatible with Python 3.11+.

This project uses the `uv` project manager to manage dependencies and the Python virtual environment.

https://docs.astral.sh/uv/

### Running

In the project root, with `uv` installed:

```shell
uv run python -m spanish_conjugation_analysis
```

On the first run, an SQLite database will be generated with Spanish language frequency data. This initialization will
not be performed on subsequent runs.

## Output Data

After running the analysis, the primary output artifact is generated
at: [artifacts/verb_data.json](artifacts/verb_data.json)

The output data contains two arrays: `lemmas`, and `elements`. `lemmas` is the collection of words analyzed, and
`elements` is the collection of individual forms/inflections of those words.

The export type definitions are defined
in [src/spanish_conjugation_analysis/export_model.py](src/spanish_conjugation_analysis/export_model.py). They are
described roughly below:

### Lemmas

Each lemma contains the properties:

- `lemma`: the base form of this word/lemma
- `partOfSpeech`: the part of speech of this lemma
    - e.g., _verbo_, _sustantivo_, etc.
- `dleUrl`: the URL to this word in the [Diccionario de la lengua española](https://dle.rae.es/) (DLE)
- `freqAdj`: the adjusted frequency score for this lemma (see [Language Sampling](#language-sampling))

Additionally, verbs have the following properties

- `models`: a list of model verbs for this verb
- `regularity`: a list of [regularity tags](#regularity-tags) for this verb
- `homonymy`: a list of [homonymy tags](#homonymy-tags) for this verb

### Elements

An element is identified by its `lemma`, `partOfSpeech`, and `form`. Verb form elements are additionally identified by
`tense`, `subject`, and `variant`.

Each element contains the following properties

- `lemma`: the lemma this element belongs to
- `partOfSpeech`: the part of speech of the lemma
- `form`: the orthographic form of this element
- `syllables`: syllable boundaries for this element
    - e.g., for _estaba_, `syllables` is `[0, 2, 4, 6]`, so the syllabification is _es-ta-ba_
- `stressPos`: the start index of the syllable where stress occurs
    - e.g., for _estaba_, `stressPos` is `2`, so the stress is on _ta_
- `homonymy`: a list of [homonymy tags](#homonymy-tags) for this element
- `heteronymousForms`, `sharedForms`, `homographs`, `homophones`, `heteronyms`, `paronyms`: lists of related elements
  that are homonyms with this element (see [Kinds of Homonymy](#kinds-of-homonymy))

Additionally, verb form elements have the following properties:

- `tense`: the tense indicated by this verb form
    - e.g., _presente_, _pretérito_, _futuro_, etc.
- `subject`: the subject indicated by the verb form
    - e.g., _yo_, _tú_, _el, ella_, etc.
- `subjectGroup`: the full list of subjects indicated by this verb form
- `variant`: the _ra/se_ variant of this verb form (applicable for subjunctive past tense)
- `preference`: when there are multiple correct forms for the same tense/subject, `preference` indicates the order they
  appear in the DLE
- `affixRange`: portion of the verb form that makes up the conjugated ending
    - e.g., for _estaba_, `affixRange` is `[3, 6]`, so the affix is `aba`
- `subjectRange`: portion of the verb form that encodes the subject
    - e.g., for _estaba_, `subjectRange` is `[5, 6]`, so the subject is encoded by the final `a`
- `regularity`: a list of [regularity tags](#regularity-tags) for this verb
- `regularSpelling`: if applicable, a relationship to the hypothetical regular spelling conjugation of this verb form
- `regularMorphology`: if applicable, a relationship to the hypothetical regular morphology conjugation of this verb
  form
- `regularConstruction`: if applicable, a relationship to the hypothetical regular construction conjugation of this verb
  form
- `irregularities`: a list of irregularities, describing what portions of this verb form are irregular and the kind of
  irregularity

### Regularity tags

Also see: [Conjugation Strategies](#conjugation-strategies)

- "verbo modelo": the Real Academia Española classifies this as a model verb
- "forma correcta": a correct verb form
- "forma incorrecta": an incorrect verb form
- "forma construida": a constructed verb form
- "morfología regular": morphologically regular
- "morfología irregular": morphologically irregular
- "ortografía regular": orthographically regular
- "ortografía irregular": orthographically irregular
- "cambio ortográfico regular": this verb form has a regular spelling change
- "construcción regular": regular construction
- "construcción irregular": irregular construction

### Homonymy tags

Also see: [Kinds of Homonymy](#kinds-of-homonymy)

- "forma heterónima": heteronymous form
- "forma compartida": shared form
- "homónimo": homonym
- "homógrafo": homograph
- "homófono": homophone
- "heterónimo": heteronym
- "parónimo": paronym

## Submodules

- **Spanish grammar** ([packages/spanish-grammar](packages/spanish-grammar))
    - Data types describing Spanish words, verbs, and verb forms
- **Spanish phonology analysis** ([packages/spanish-phonology](packages/spanish-phonology))
    - Tools for annotating Spanish words with phoneme, syllable, and stress position metadata
    - Calculate the graphic or phonetic differences between Spanish words
- **Spanish conjugation** ([packages/spanish-conjugation](packages/spanish-conjugation))
    - Generate regular spelling and regular morphology conjugations for Spanish verbs
    - Annotate endings of irregular Spanish verb forms

## Methodology

### Language Sampling

This analysis considers the top 5000 relevant words/lemmas of the Spanish Language, as measured by an adjusted frequency
score.

In addition to these top 5000 words, additional verbs are included in the sample set from the following sources:

- Verbs classified as model verbs by the [Diccionario de la lengua española](https://dle.rae.es/) (DLE)
- Verbs classified as model verbs by
  the [Diccionario panhispánico de dudas](https://www.rae.es/dpd/ayuda/modelos-de-conjugacion-verbal) (DPD)
- Verbs from [Lisardo's KOFI Method](https://www.asiteaboutnothing.net/w_ultimate_spanish_conjugation.php) for learning
  Spanish conjugation

The [Real Academia Española](https://www.rae.es/) publishes an open language frequency data set
called [CORPES](https://www.rae.es/corpes/). One of the published artifacts from this data set "Lemas documentados
ordenados por frecuencia creciente de la DP" contains a ranking of Spanish words with two relevant data points:

- Normalized Frequency: Number of occurrences per million words
- Deviation of Proportions (DP): Clustering of a word within the dataset
    - DP approaching 0 indicates a word is distributed evenly across a dataset
    - DP approaching 1 indicates the usage of a word is more localized within a dataset

Using normalized frequency alone to decide the top 5000 words does not necessarily yield a list that is representative
of the common use of a language. This is because, for example, some words that occur very frequently in a specialized
subject area may show a higher overall frequency in the dataset relative to their actual use in common language.

To account for this, normalized frequency, $freq_{norm}$, may be combined with
$DP$ as follows:

$$ freq_{adj} = freq_{norm}*(1-DP) $$

This adjusted frequency score is used to decide the top 5000 relevant words in the Spanish language for this analysis.

### Conjugation Strategies

To analyze conjugation regularity, the program generates hypothetical regular forms for every verb in the language
sample set. There are three strategies used to generate these regular forms: _regular spelling_, _regular morphology_,
and _regular construction_.

#### Regular Spelling / Regular Orthographic Conjugation

Regular spelling conjugation is the simplest way to conjugate a Spanish verb regularly. Take off the _-ar/er/ir_ ending
and paste on the appropriate regular subject/tense inflection.

The [Diccionario de la lengua española](https://dle.rae.es/) (DLE) classifies verbs as regular if they have regular
spelling. These include the model verbs _amar_ (to love), _temer_ (to fear), and _partir_ (to depart). If a verb form is
_spelled_ regularly, then it is _orthographically regular_.

#### Regular Morphology Conjugation

Regular morphology conjugation considers not only how a verb form is _spelled_, but also how it _sounds_. If a verb form
_sounds_ regular, then it is _morphologically regular_.

It is common to find verb forms that are _morphologically regular_, but _orthographically irregular_. The DLE classifies
such verbs as irregular. One example is the verb _leer_. The third-person plural preterite form of _leer_ is _leyeron_.
The _orthographically regular_ form of the verb would look like _leieron;_ however, Spanish spelling rules dictate that
this _e-/ie/_ phonetic pattern should be spelled with a _y_ instead of an _i_.

If a verb is _orthographically regular_, it is usually, but not always _morphologically regular_. An example of a
negative case is the verb _aislar_ (to isolate). The first-person singular present form of _aislar_ is _aíslo_. A
regular morphology for this form would sound like _ai-slo_, where _/ai/_ is a diphthong, a single syllable. But notice
the stress on the _í_; this changes the sound to _a-i-slo_, where _a_ and _i_ form two syllables. Even though this verb
form has a regular spelling and is _orthographically regular_, it _sounds_ irregular, so it is _morphologically
irregular_.

#### Regular Construction Conjugation

Some Spanish verb inflections can be derived from another inflection. For example, past and future subjunctive verb
forms are based on the third-person plural preterite form of a verb. If such an inflection is derived regularly, then it
is a _regular construction_.

As an example, the first-person singular subjunctive past form of _tener_ (to have) is _tuviera_. The hypothetical
regular form is _teniera_. This is an irregular form, but it is derived in a regular way from the irregular third-person
plural preterite form _tuvieron_, so it is a _regular construction_.

### Kinds of Homonymy

It is interesting to identify words within a language that sound similar to one another. In the context of this
analysis, such words are broadly referred to as homonyms, with the following subclassifications:

- **Heteronymous Forms:** Two forms of the _same verb_ are _heteronymous forms_ if they share the same spelling, but
  differ in stress. One example is the forms of _deber_ (must): _debe_, and _debé_.
- **Shared Forms:** Two forms of _different verbs_ are _shared forms_ if they share the same sound and spelling. For
  example, _fui_ is a shared form of _ser_ (to be) and of _ir_ (to go).
- **Homographs:** Two words are _homographs_ if they share the same spelling. For example, _como_ is both a form of
  _comer_ (to eat), and also functions as an adverb meaning "as" or "like".
- **Homophones:** Two words are _homophones_ if they sound the same but have different spellings. For example, _tuvo_, a
  form of _tener_ (to have), sounds the same as _tubo_, meaning "tube".
- **Heteronyms:** Two words are _heteronyms_ if they are spelled the same but sound different. For example, _esté_
  (stress on the second _é_) is a form of _estar_ (to be), and _este_ (stress on the first _e_) means "this".
- **Paronyms:** Two words are _paronyms_ if they share the same phonemes, but they are spelled differently and have
  different stress. For example, _soná_ (stress on _á_) is a form of _sonar_ (to dream), and _zona_ (stress on _o_)
  means "area".
