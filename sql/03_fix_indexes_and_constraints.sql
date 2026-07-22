-- =====================================================================
-- Fix: Index manquants sur les colonnes de cle etrangere
-- Fix: Contrainte UNIQUE sur siret pour eviter les doublons clients
-- =====================================================================

CREATE INDEX IF NOT EXISTS idx_ligne_pole ON mdm.ref_ligne(pole_code);
CREATE INDEX IF NOT EXISTS idx_client_site ON mdm.ref_client(site_code);
CREATE INDEX IF NOT EXISTS idx_contrat_client ON mdm.ref_contrat(client_code);
CREATE INDEX IF NOT EXISTS idx_contrat_ligne ON mdm.ref_contrat(ligne_code);
CREATE INDEX IF NOT EXISTS idx_contrat_site ON mdm.ref_contrat(site_code);
CREATE INDEX IF NOT EXISTS idx_plan_comptable_nature ON mdm.ref_plan_comptable(nature_code);

ALTER TABLE mdm.ref_client
    ADD CONSTRAINT uq_ref_client_siret UNIQUE (siret);
