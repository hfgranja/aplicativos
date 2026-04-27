-- PEC Observation App — Database initialization
-- One database per microservice for full schema isolation

CREATE DATABASE pec_identity;
CREATE DATABASE pec_school;
CREATE DATABASE pec_observation;
CREATE DATABASE pec_audio;
CREATE DATABASE pec_transcription;
CREATE DATABASE pec_ai_feedback;
CREATE DATABASE pec_feedback;
CREATE DATABASE pec_pdf;
CREATE DATABASE pec_audit;
CREATE DATABASE pec_consent;
CREATE DATABASE pec_knowledge;
CREATE DATABASE pec_best_practices;
CREATE DATABASE pec_learning;
CREATE DATABASE pec_evaluator;

-- Enable pgvector extension in pec_learning (used by MS-013)
\c pec_learning
CREATE EXTENSION IF NOT EXISTS vector;
