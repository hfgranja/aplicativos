package br.gov.educacao.sp.pecobservation.domain.entities

import java.util.UUID

data class FeedbackItem(
    val title: String,
    val description: String,
)

data class Feedback(
    val id: UUID = UUID.randomUUID(),
    val observationId: UUID,
    val strengths: List<FeedbackItem> = emptyList(),
    val improvements: List<FeedbackItem> = emptyList(),
    val actionItems: List<String> = emptyList(),
    val overallRating: String = "",
    val isApproved: Boolean = false,
)
