package br.gov.educacao.sp.pecobservation.domain.entities

enum class PedagogicalCriterion(val value: String, val displayName: String, val emoji: String) {
    PLANEJAMENTO("planejamento", "Planejamento Curricular",  "📐"),
    DIDATICA    ("didatica",     "Clareza Didática",         "🎯"),
    ENGAJAMENTO ("engajamento",  "Engajamento",              "🙋"),
    AVALIACAO   ("avaliacao",    "Avaliação Formativa",      "📊"),
    GESTAO      ("gestao",       "Gestão do Tempo",          "⏱️");

    companion object {
        fun fromRaw(v: String) = entries.firstOrNull { it.value == v }
    }
}

data class BestPracticeCard(
    val id:             String,
    val title:          String,
    val criterion:      String,
    val subject:        String,
    val grade:          String,
    val excerpt:        String,
    val aiExplanation:  String,
    val rubricAlignment: List<String>,
    val tags:           List<String>,
    val status:         String,
    val hasAudio:       Boolean,
    val audioUrl:       String?,
    val hasVideo:       Boolean,
    val videoStatus:    String,   // pending | processing | ready | failed
    val videoDurationS: Int?,
    val createdAt:      String,
    val publishedAt:    String?,
) {
    val criterionEnum get() = PedagogicalCriterion.fromRaw(criterion)
}

data class PracticeDistribution(
    val id:       String,
    val card:     BestPracticeCard,
    val message:  String,
    val sentAt:   String,
    val viewedAt: String?,
)
