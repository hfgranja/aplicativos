package br.gov.educacao.sp.pecobservation.domain.errors

sealed class DomainError(message: String) : Exception(message) {
    class ValidationError(field: String, reason: String) : DomainError("$field: $reason")
    class NotFound(entity: String, id: String) : DomainError("$entity $id not found")
    class InvalidStatusTransition(from: String, to: String) : DomainError("Cannot transition from $from to $to")
}

sealed class RecordingError(message: String) : Exception(message) {
    class PermissionDenied : RecordingError("Microphone permission denied")
    class AlreadyRecording : RecordingError("Recording already in progress")
    class NotRecording : RecordingError("No active recording")
    class HardwareError(cause: String) : RecordingError("Hardware error: $cause")
}

sealed class NetworkError(message: String) : Exception(message) {
    class Unauthorized : NetworkError("Unauthorized — please log in again")
    class NotFound(path: String) : NetworkError("Not found: $path")
    class ServerError(code: Int, body: String) : NetworkError("Server error $code: $body")
    class NoConnection : NetworkError("No network connection")
}
