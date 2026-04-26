package br.gov.educacao.sp.pecobservation.ports

interface NetworkClientPort {
    suspend fun post(path: String, body: Map<String, Any>): Map<String, Any>
    suspend fun get(path: String): Map<String, Any>
    suspend fun patch(path: String, body: Map<String, Any>): Map<String, Any>
    suspend fun putBinary(url: String, filePath: String, contentType: String = "audio/mp4")
}
