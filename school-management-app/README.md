# Gestão Escolar

Aplicativo web para a equipe gestora (direção, vice-direção, coordenação) de uma escola estadual gerenciar o dia a dia: alunos e matrículas, professores e atribuição de aulas, frequência, notas, ocorrências disciplinares e comunicados internos.

Pensado para uso local, por uma única escola, pela equipe gestora (não inclui acesso de professores ou de pais/responsáveis nesta versão).

## Funcionalidades

- **Login** da equipe gestora (diretor, vice-diretor, coordenador, secretaria)
- **Alunos**: cadastro, edição, status (ativo/transferido/evadido), dados de responsável, vínculo com turma
- **Turmas**: cadastro por série/turno/ano letivo
- **Professores**: cadastro e atribuição de disciplinas a turmas
- **Frequência**: lançamento de presença/falta por turma e data, com justificativa
- **Notas**: lançamento de notas por aluno, disciplina e bimestre
- **Ocorrências**: registro de ocorrências disciplinares, elogios, saúde etc., com providência tomada e aviso ao responsável
- **Comunicados**: avisos gerais ou para uma turma específica
- **Painel**: visão geral com totais, frequência do dia e atividades recentes

## Stack

- **Backend**: Python + FastAPI + SQLAlchemy + SQLite, autenticação por JWT
- **Frontend**: React + Vite + React Router

## Como rodar

### Backend (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed.py                    # cria usuário admin e dados de exemplo
uvicorn main:app --reload
```

A API sobe em `http://localhost:8000`. Documentação interativa em `http://localhost:8000/docs`.

O comando `seed.py` cria o login inicial:
- **E-mail**: `diretoria@escola.sp.gov.br`
- **Senha**: `mudar123`

> Troque essa senha (ou crie um novo usuário via `POST /api/auth/register`) antes de usar em produção.

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Acesse **http://localhost:5173**. Em desenvolvimento, o Vite faz proxy de `/api` para `http://localhost:8000`.

## Estrutura

```
school-management-app/
├── backend/
│   ├── main.py           # app FastAPI, registra os routers
│   ├── database.py       # engine/sessão SQLite
│   ├── models.py         # modelos SQLAlchemy
│   ├── schemas.py        # schemas Pydantic
│   ├── auth.py           # hashing de senha e JWT
│   ├── seed.py           # cria usuário admin + dados de exemplo
│   └── routers/          # endpoints por módulo
└── frontend/
    └── src/
        ├── pages/         # uma página por módulo
        ├── components/    # Layout (navegação) e Modal
        ├── api.js         # cliente HTTP com token
        └── AuthContext.jsx
```

## Próximos passos sugeridos

- Exportar boletim/relatório de frequência em PDF
- Acesso de professores para lançar frequência e notas das próprias aulas
- Portal para pais/responsáveis (exige cuidado adicional com LGPD)
- Hospedagem remota multiusuário, se a escola precisar de acesso fora da rede local
