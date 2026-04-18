CREATE TABLE IF NOT EXISTS leads (
    id            BIGSERIAL PRIMARY KEY,
    naam          VARCHAR(200)  NOT NULL,
    email         VARCHAR(254)  NOT NULL,
    bedrijf       VARCHAR(200),
    dienst        VARCHAR(100),
    bericht       TEXT          NOT NULL,
    status        VARCHAR(50)   NOT NULL DEFAULT 'nieuw',
    aangemaakt_op TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
