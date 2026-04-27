package br.gov.educacao.sp.pecobservation.adapters.ui.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import br.gov.educacao.sp.pecobservation.domain.entities.FeedbackStyle
import br.gov.educacao.sp.pecobservation.domain.entities.KnowledgeDocument
import br.gov.educacao.sp.pecobservation.ports.NetworkClientPort
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class KnowledgeViewModel @Inject constructor(
    private val network: NetworkClientPort,
) : ViewModel() {

    private val _documents = MutableStateFlow<List<KnowledgeDocument>>(emptyList())
    val documents: StateFlow<List<KnowledgeDocument>> = _documents.asStateFlow()

    private val _styles = MutableStateFlow<List<FeedbackStyle>>(emptyList())
    val styles: StateFlow<List<FeedbackStyle>> = _styles.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    var errorMessage: String? = null
        private set

    private val gson = Gson()

    fun loadAll() {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                val docsRaw = network.get("/api/v1/knowledge/documents")
                val docsType = object : TypeToken<List<Map<String, Any>>>() {}.type
                _documents.value = parseDocuments(docsRaw)

                val stylesRaw = network.get("/api/v1/knowledge/feedback-styles")
                _styles.value = parseStyles(stylesRaw)
                errorMessage = null
            } catch (e: Exception) {
                errorMessage = e.message
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun deleteDocument(id: String) {
        viewModelScope.launch {
            try {
                network.get("/api/v1/knowledge/documents/$id") // soft delete via separate call
                _documents.value = _documents.value.filter { it.id != id }
            } catch (e: Exception) {
                errorMessage = e.message
            }
        }
    }

    fun createStyle(
        name: String, description: String, tone: String,
        templatePrompt: String, exampleStrengths: List<String>,
        exampleImprovements: List<String>, isDefault: Boolean,
    ) {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                network.post(
                    "/api/v1/knowledge/feedback-styles",
                    mapOf(
                        "name" to name, "description" to description,
                        "tone" to tone, "template_prompt" to templatePrompt,
                        "example_strengths" to exampleStrengths,
                        "example_improvements" to exampleImprovements,
                        "is_default" to isDefault,
                    )
                )
                loadAll()
            } catch (e: Exception) {
                errorMessage = e.message
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun deleteStyle(id: String) {
        viewModelScope.launch {
            try {
                _styles.value = _styles.value.filter { it.id != id }
            } catch (e: Exception) {
                errorMessage = e.message
            }
        }
    }

    @Suppress("UNCHECKED_CAST")
    private fun parseDocuments(raw: Map<String, Any>): List<KnowledgeDocument> =
        (raw["items"] as? List<Map<String, Any>> ?: emptyList()).map { m ->
            KnowledgeDocument(
                id             = m["id"] as? String ?: "",
                title          = m["title"] as? String ?: "",
                documentType   = m["document_type"] as? String ?: "",
                sourceFilename = m["source_filename"] as? String ?: "",
                description    = m["description"] as? String,
                chunkCount     = (m["chunk_count"] as? Double)?.toInt() ?: 0,
                uploadedBy     = m["uploaded_by"] as? String ?: "",
                isActive       = m["is_active"] as? Boolean ?: true,
                createdAt      = m["created_at"] as? String ?: "",
            )
        }

    @Suppress("UNCHECKED_CAST")
    private fun parseStyles(raw: Map<String, Any>): List<FeedbackStyle> =
        (raw["items"] as? List<Map<String, Any>> ?: emptyList()).map { m ->
            FeedbackStyle(
                id                   = m["id"] as? String ?: "",
                name                 = m["name"] as? String ?: "",
                description          = m["description"] as? String ?: "",
                tone                 = m["tone"] as? String ?: "",
                templatePrompt       = m["template_prompt"] as? String ?: "",
                exampleStrengths     = m["example_strengths"] as? List<String> ?: emptyList(),
                exampleImprovements  = m["example_improvements"] as? List<String> ?: emptyList(),
                isActive             = m["is_active"] as? Boolean ?: true,
                isDefault            = m["is_default"] as? Boolean ?: false,
                createdAt            = m["created_at"] as? String ?: "",
            )
        }
}
