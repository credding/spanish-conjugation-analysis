CREATE TABLE freq_elements
(
    id                     INTEGER PRIMARY KEY,
    form                   TEXT    NOT NULL,
    lemma                  TEXT    NOT NULL,
    tag                    TEXT    NOT NULL,
    freq                   INTEGER NOT NULL,
    freq_norm_with_punc    REAL    NOT NULL,
    freq_norm_without_punc REAL    NOT NULL,
    UNIQUE (form, lemma, tag)
) STRICT;

CREATE INDEX ix_freq_elements_lemma ON freq_elements (lemma);
CREATE INDEX ix_freq_elements_freq ON freq_elements (freq);

CREATE TABLE freq_lemmas
(
    id                     INTEGER PRIMARY KEY,
    lemma                  TEXT    NOT NULL,
    class                  TEXT    NOT NULL,
    freq                   INTEGER NOT NULL,
    freq_norm_with_punc    REAL    NOT NULL,
    freq_norm_without_punc REAL    NOT NULL,
    UNIQUE (lemma, class)
) STRICT;

CREATE INDEX ix_freq_lemmas_freq ON freq_lemmas (freq);

CREATE TABLE freq_forms
(
    id        INTEGER PRIMARY KEY,
    form      TEXT    NOT NULL,
    freq      INTEGER NOT NULL,
    freq_norm REAL    NOT NULL,
    UNIQUE (form)
) STRICT;

CREATE INDEX ix_freq_forms_freq ON freq_forms (freq);

CREATE TABLE dp_lemmas
(
    id            INTEGER PRIMARY KEY,
    lemma         TEXT    NOT NULL,
    class         TEXT    NOT NULL,
    freq          INTEGER NOT NULL,
    freq_norm     REAL    NOT NULL,
    dp            REAL    NOT NULL,
    num_countries INTEGER NOT NULL,
    freq_adj      REAL AS (freq_norm * (1 - dp)),
    UNIQUE (lemma, class)
) STRICT;

CREATE INDEX ix_dp_lemmas_freq ON dp_lemmas (freq);
CREATE INDEX ix_dp_lemmas_freq_adj ON dp_lemmas (freq_adj);
