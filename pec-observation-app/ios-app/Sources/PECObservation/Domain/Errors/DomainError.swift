import Foundation

public enum DomainError: LocalizedError {
    case notFound(String)
    case validationFailed(String)
    case invalidStatusTransition(from: String, to: String)
    case permissionDenied
    case alreadyExists(String)

    public var errorDescription: String? {
        switch self {
        case .notFound(let entity):
            return "\(entity) não encontrado(a)"
        case .validationFailed(let reason):
            return "Validação falhou: \(reason)"
        case .invalidStatusTransition(let from, let to):
            return "Transição inválida: \(from) → \(to)"
        case .permissionDenied:
            return "Permissão negada"
        case .alreadyExists(let entity):
            return "\(entity) já existe"
        }
    }
}

public enum RecordingError: LocalizedError {
    case permissionDenied
    case alreadyRecording
    case notRecording
    case fileCreationFailed
    case checksumFailed

    public var errorDescription: String? {
        switch self {
        case .permissionDenied:
            return "Permissão de microfone negada. Acesse Ajustes para habilitar."
        case .alreadyRecording:
            return "Já há uma gravação em andamento"
        case .notRecording:
            return "Nenhuma gravação ativa"
        case .fileCreationFailed:
            return "Falha ao criar arquivo de áudio"
        case .checksumFailed:
            return "Falha ao calcular checksum do arquivo"
        }
    }
}

public enum NetworkError: LocalizedError {
    case unauthorized
    case serverError(Int)
    case noConnection
    case decodingFailed(String)
    case timeout

    public var errorDescription: String? {
        switch self {
        case .unauthorized:
            return "Sessão expirada. Faça login novamente."
        case .serverError(let code):
            return "Erro no servidor (\(code))"
        case .noConnection:
            return "Sem conexão com a internet"
        case .decodingFailed(let detail):
            return "Falha ao processar resposta: \(detail)"
        case .timeout:
            return "Tempo de conexão esgotado"
        }
    }
}
