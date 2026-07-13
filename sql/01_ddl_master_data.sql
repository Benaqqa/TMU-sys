
-- =====================================================================
-- TMU MASTER DATA LAYER — Reference Tables (REF_*)
-- Analytical code structure: P.LL.S.CCCCCC (Pole.Ligne.Site.Contrat)
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS mdm;

-- 1. REF_POLE — 4 strategic poles
CREATE TABLE mdm.ref_pole (
    pole_code       CHAR(1) PRIMARY KEY CHECK (pole_code IN ('1','2','3','4')),
    pole_libelle    VARCHAR(50) NOT NULL,
    responsable     VARCHAR(100),
    genere_ca_externe BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT now(),
    updated_at      TIMESTAMP DEFAULT now()
);

-- 2. REF_LIGNE — 13 activity lines, each attached to one pole
CREATE TABLE mdm.ref_ligne (
    ligne_code      CHAR(2) PRIMARY KEY,           -- '01' .. '13', '00' = transverse
    ligne_libelle   VARCHAR(100) NOT NULL,
    pole_code       CHAR(1) NOT NULL REFERENCES mdm.ref_pole(pole_code),
    created_at      TIMESTAMP DEFAULT now(),
    updated_at      TIMESTAMP DEFAULT now()
);

-- 3. REF_SITE — geographic locations
CREATE TABLE mdm.ref_site (
    site_code       CHAR(3) PRIMARY KEY,           -- POR / TAC / SAT / SIE
    site_libelle    VARCHAR(100) NOT NULL,
    adresse         VARCHAR(255),
    created_at      TIMESTAMP DEFAULT now(),
    updated_at      TIMESTAMP DEFAULT now()
);

-- 4. REF_CLIENT — B2B clients (golden record, sourced CRM/SAP)
CREATE TABLE mdm.ref_client (
    client_code     VARCHAR(20) PRIMARY KEY,
    raison_sociale  VARCHAR(150) NOT NULL,
    siret           VARCHAR(20),
    secteur         VARCHAR(80),
    site_code       CHAR(3) REFERENCES mdm.ref_site(site_code),
    source_system   VARCHAR(20) DEFAULT 'CRM',     -- CRM | SAP
    created_at      TIMESTAMP DEFAULT now(),
    updated_at      TIMESTAMP DEFAULT now()
);

-- 5. REF_NATURE — cost/revenue nature typology (axis A6)
CREATE TABLE mdm.ref_nature (
    nature_code     VARCHAR(10) PRIMARY KEY,
    nature_libelle  VARCHAR(100) NOT NULL,
    type_nature     VARCHAR(20) CHECK (type_nature IN ('PRODUIT','CHARGE')),
    created_at      TIMESTAMP DEFAULT now()
);

-- 6. REF_CONTRAT — individual service contracts (axis A4)
CREATE TABLE mdm.ref_contrat (
    contrat_code    VARCHAR(6) PRIMARY KEY,         -- 6 chars, e.g. 'CTR042'
    client_code     VARCHAR(20) NOT NULL REFERENCES mdm.ref_client(client_code),
    ligne_code      CHAR(2) NOT NULL REFERENCES mdm.ref_ligne(ligne_code),
    site_code       CHAR(3) NOT NULL REFERENCES mdm.ref_site(site_code),
    date_debut      DATE NOT NULL,
    date_fin        DATE,
    montant_budget  NUMERIC(14,2),
    statut          VARCHAR(20) DEFAULT 'ACTIF',
    created_at      TIMESTAMP DEFAULT now(),
    updated_at      TIMESTAMP DEFAULT now()
);

-- 7. REF_PLAN_COMPTABLE — mapping general ledger accounts <-> analytical codes
CREATE TABLE mdm.ref_plan_comptable (
    compte_general  VARCHAR(20) PRIMARY KEY,        -- Oracle GL account
    libelle_compte  VARCHAR(150),
    nature_code     VARCHAR(10) REFERENCES mdm.ref_nature(nature_code),
    created_at      TIMESTAMP DEFAULT now()
);

-- =====================================================================
-- ANALYTICAL CODE GENERATOR: P.LL.S.CCCCCC (12 useful chars)
-- =====================================================================
CREATE OR REPLACE FUNCTION mdm.build_analytical_code(
    p_pole   CHAR(1),
    p_ligne  CHAR(2),
    p_site   CHAR(3),
    p_contrat VARCHAR(6) DEFAULT NULL
) RETURNS VARCHAR(20) AS $$
BEGIN
    RETURN p_pole || '.' || p_ligne || '.' || p_site || '.' ||
           COALESCE(p_contrat, '000000');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Trigger to keep updated_at fresh (example for ref_contrat)
CREATE OR REPLACE FUNCTION mdm.set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_contrat_updated
BEFORE UPDATE ON mdm.ref_contrat
FOR EACH ROW EXECUTE FUNCTION mdm.set_updated_at();
