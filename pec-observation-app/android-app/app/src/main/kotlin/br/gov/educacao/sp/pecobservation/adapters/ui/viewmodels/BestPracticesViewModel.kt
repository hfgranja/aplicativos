package br.gov.educacao.sp.pecobservation.adapters.ui.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import br.gov.educacao.sp.pecobservation.domain.entities.BestPracticeCard
import br.gov.educacao.sp.pecobservation.domain.entities.PracticeDistribution
import br.gov.educacao.sp.pecobservation.ports.NetworkClientPort
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class BestPracticesViewModel @Inject constructor(
    private val network: NetworkClientPort,
) : ViewModel() {

    private val _cards         = MutableStateFlow<List<BestPracticeCard>>(emptyList())
    val cards: StateFlow<List<BestPracticeCard>> = _cards.asStateFlow()

    private val _distributions = MutableStateFlow<List<PracticeDistribution>>(emptyList())
    val distributions: StateFlow<List<PracticeDistribution>> = _distributions.asStateFlow()

    private val _isLoading     = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    var errorMessage: String? = null
        private set

    fun loadLibrary(status: String = "published") {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                val raw = network.get("/api/v1/best-practices?status=$status")
                _cards.value = parseCards(raw)
            } catch (e: Exception) {
                errorMessage = e.message
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun publish(cardId: String, title: String) {
        viewModelScope.launch {
            try {
                network.post("/api/v1/best-practices/$cardId/publish", mapOf("title" to title))
                loadLibrary("draft")
            } catch (e: Exception) { errorMessage = e.message }
        }
    }

    fun distribute(cardId: String, teacherIds: List<String>, message: String) {
        viewModelScope.launch {
            try {
                network.post(
                    "/api/v1/best-practices/$cardId/distribute",
                    mapOf("teacher_ids" to teacherIds, "message" to message),
                )
            } catch (e: Exception) { errorMessage = e.message }
        }
    }

    fun archive(cardId: String) {
        viewModelScope.launch {
            try {
                network.get("/api/v1/best-practices/$cardId") // placeholder — should be DELETE
                _cards.value = _cards.value.filter { it.id != cardId }
            } catch (e: Exception) { errorMessage = e.message }
        }
    }

    suspend fun fetchVideoUrl(cardId: String): String? = try {
        val raw = network.get("/api/v1/best-practices/$cardId/video-url")
        raw["url"] as? String
    } catch (e: Exception) {
        errorMessage = e.message
        null
    }

    @Suppress("UNCHECKED_CAST")
    private fun parseCards(raw: Map<String, Any>): List<BestPracticeCard> =
        (raw["items"] as? List<Map<String, Any>> ?: emptyList()).map { m ->
            BestPracticeCard(
                id             = m["id"]             as? String ?: "",
                title          = m["title"]          as? String ?: "",
                criterion      = m["criterion"]      as? String ?: "",
                subject        = m["subject"]        as? String ?: "",
                grade          = m["grade"]          as? String ?: "",
                excerpt        = m["excerpt"]        as? String ?: "",
                aiExplanation  = m["ai_explanation"] as? String ?: "",
                rubricAlignment = m["rubric_alignment"] as? List<String> ?: emptyList(),
                tags           = m["tags"]           as? List<String> ?: emptyList(),
                status         = m["status"]         as? String ?: "",
                hasAudio       = m["has_audio"]      as? Boolean ?: false,
                audioUrl       = m["audio_url"]      as? String,
                hasVideo       = m["has_video"]      as? Boolean ?: false,
                videoStatus    = m["video_status"]   as? String ?: "pending",
                videoDurationS = (m["video_duration_s"] as? Number)?.toInt(),
                createdAt      = m["created_at"]     as? String ?: "",
                publishedAt    = m["published_at"]   as? String,
            )
        }
}
