package br.gov.educacao.sp.pecobservation.domain.entities

import java.time.Instant

enum class DocumentType(val displayName: String) {
    SEDUC_POLICY("Política SEDUC"),
    CURRICULUM_GUIDE("Guia Curricular"),
    EVALUATION_RUBRIC("Rubrica de Avaliação"),
    FEEDBACK_EXAMPLE("Exemplo de Feedback"),
    OTHER("Outro");

    companion object {
        fun fromRaw(raw: String) = entries.firstOrNull { it.name.lowercase() == raw } ?: OTHER
    }
}

data class KnowledgeDocument(
    val id: String,
    val title: String,
    val documentType: String,
    val sourceFilename: String,
    val description: String?,
    val chunkCount: Int,
    val uploadedBy: String,
    val isActive: Boolean,
    val createdAt: String,
) {
    val documentTypeDisplay: String
        get() = DocumentType.fromRaw(documentType).displayName
}

enum class StyleTone(val displayName: String) {
    FORMAL("Formal"),
    CONSTRUCTIVE("Construtivo"),
    DIRECT("Direto"),
    SUPPORTIVE("Acolhedor");
}

data class FeedbackStyle(
    val id: String,
    val name: String,
    val description: String,
    val tone: String,
    val templatePrompt: String,
    val exampleStrengths: List<String>,
    val exampleImprovements: List<String>,
    val isActive: Boolean,
    val isDefault: Boolean,
    val createdAt: String,
) {
    val toneDisplay: String
        get() = StyleTone.entries.firstOrNull { it.name.lowercase() == tone }?.displayName ?: tone
}
