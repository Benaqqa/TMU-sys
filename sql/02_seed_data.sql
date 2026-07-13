
-- =====================================================================
-- SEED DATA — matches TMU reference document exactly
-- =====================================================================

INSERT INTO mdm.ref_pole (pole_code, pole_libelle, responsable, genere_ca_externe) VALUES
('1','Distribution','DC Distribution', TRUE),
('2','Developpement Durable','DC Dev. Durable', TRUE),
('3','Commercial','DC Commercial', FALSE),
('4','Support','DAF', FALSE);

INSERT INTO mdm.ref_ligne (ligne_code, ligne_libelle, pole_code) VALUES
('01','Distribution Eau & Electricite','1'),
('02','Maintenance Multi-Techniques','2'),
('03','Assainissement Liquide','1'),
('04','Collecte de Dechets','2'),
('05','Valorisation Dechets (Centre de Tri)','2'),
('06','Facilities Management','2'),
('07','Advisory & Conseil','2'),
('08','Energy Management','2'),
('09','Decarbonation','2'),
('10','Efficacite Energetique','2'),
('11','Nettoyage Sites Industriels','2'),
('12','Sourcing & Pilotage EnR','2'),
('13','Digital & Data Services','2'),
('00','Fonctions Transverses / Hors Ligne','4');

INSERT INTO mdm.ref_site (site_code, site_libelle, adresse) VALUES
('POR','Port Tanger Med','Zone Portuaire, Tanger Med'),
('TAC','Site TAC','Tanger'),
('SAT','Site SATT (Centre de Tri)','Casablanca'),
('SIE','Siege','Casablanca, Maroc');

INSERT INTO mdm.ref_nature (nature_code, nature_libelle, type_nature) VALUES
('ENERG','Achats energie (ONEE/SRM/EnR)','CHARGE'),
('MARCH','Achats de marchandises','CHARGE'),
('FOURN','Fournitures / pieces','CHARGE'),
('SSTRA','Sous-traitance','CHARGE'),
('PERS','Personnel direct','CHARGE'),
('AMORT','Amortissements','CHARGE'),
('FINAN','Frais financiers','CHARGE'),
('CA_EXT','CA externe','PRODUIT'),
('CA_INT','Refacturation interne / CA cross-sell','PRODUIT');

INSERT INTO mdm.ref_client (client_code, raison_sociale, secteur, site_code, source_system) VALUES
('CLI-0001','Client X Industries','Industrie','TAC','CRM'),
('CLI-0002','Client Y Logistics','Logistique','POR','SAP');

INSERT INTO mdm.ref_contrat (contrat_code, client_code, ligne_code, site_code, date_debut, date_fin, montant_budget, statut) VALUES
('CTR042','CLI-0001','02','TAC','2026-01-01','2026-12-31', 480000.00, 'ACTIF'),
('CTR018','CLI-0002','06','POR','2026-03-01','2027-02-28', 220000.00, 'ACTIF');

INSERT INTO mdm.ref_plan_comptable (compte_general, libelle_compte, nature_code) VALUES
('601100','Achats ONEE HT','ENERG'),
('602200','Achats fournitures maintenance','FOURN'),
('604100','Sous-traitance technique','SSTRA'),
('641100','Salaires personnel technique','PERS'),
('681100','Dotations amortissements','AMORT'),
('706100','Ventes prestations services','CA_EXT');
