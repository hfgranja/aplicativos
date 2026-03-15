# PEC – Sistema de Feedback de Aulas

Aplicativo web local para o Professor Especialista em Currículo (PEC) da Secretaria da Educação do Estado de São Paulo.

## Funcionalidades

- **Ficha de observação completa** com 5 seções e 24 critérios (baseado na ficha oficial PEC)
- **Upload de aulas gravadas** (MP4, MP3, WAV)
- **Transcrição automática** com faster-whisper (Whisper local)
- **Feedback gerado por LLM** (Ollama llama3.2) com aprendizado contínuo do histórico
- **Roteiro de devolutiva em CNV** (Comunicação Não-Violenta)
- **Histórico** de observações por professor
- **Evolução temporal** com gráficos de linha por seção
- **Comparativo** entre duas observações (radar + barras)

## Pré-requisitos

1. **Python ≥ 3.10** + pip
2. **Node.js ≥ 18** + npm
3. **Ollama** – `ollama serve` + `ollama pull llama3.2`
4. **FFmpeg** (para transcrição de áudio/vídeo)

## Como rodar

### Backend (FastAPI)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```

Acesse: **http://localhost:5173**

## Estrutura

```
teacher-feedback/
├── backend/           # Python FastAPI + SQLite
│   ├── main.py
│   ├── models.py      # ORM schema
│   ├── routers/       # API endpoints
│   └── services/      # LLM, analytics, transcrição
└── frontend/          # React + Vite
    └── src/
        ├── pages/     # Páginas principais
        ├── components/ # Componentes UI
        ├── hooks/     # State management
        └── api/       # Client HTTP
```
