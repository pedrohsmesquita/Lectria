# 🚀 Sistema de Gerenciamento de Livros e Upload de Vídeos

## 📋 Visão Geral

Sistema completo para criação de livros e upload de vídeos educacionais com persistência de fila usando IndexedDB.

## ✨ Funcionalidades Implementadas

### Backend (FastAPI)

#### Endpoints de Livros
- **GET /books** - Lista todos os livros do usuário autenticado
- **POST /books** - Cria um novo livro
- **GET /books/{book_id}** - Obtém detalhes de um livro específico com lista de vídeos

#### Segurança
- ✅ Autenticação JWT obrigatória
- ✅ Validação de ownership (usuário só acessa seus próprios livros)
- ✅ Preenchimento automático do autor com nome do usuário

### Frontend (React + TypeScript)

#### Fluxo de Navegação
```
Login → Dashboard de Livros → Upload de Vídeos
```

#### Componentes

1. **BooksDashboard** (`/dashboard`)
   - Lista todos os livros do usuário em grid de cards
   - Botão destacado "Criar Novo Livro"
   - Cada card mostra: título, autor, status, quantidade de vídeos, data de criação
   - Botão "Adicionar Vídeos" em cada livro

2. **CreateBookModal**
   - Modal para criar novo livro
   - Validação de título não vazio
   - Feedback visual de loading e erros

3. **UploadDashboard** (`/upload/:bookId`)
   - Recebe bookId via URL params
   - Mostra informações do livro no topo
   - Drag-and-drop para upload de vídeos
   - **Fila sequencial**: 1 upload por vez (mudado de 3 paralelos)
   - **Persistência com IndexedDB**: Uploads não são perdidos ao fechar o navegador
   - Modal de retomada ao reabrir com uploads pendentes
   - Botão "Voltar para Meus Livros"

4. **ResumePendingUploadsModal**
   - Aparece ao reabrir o site com uploads pendentes
   - Opções: Continuar ou Descartar

#### Persistência de Fila (IndexedDB)

- **Biblioteca**: `idb` v8.0.0
- **Funcionalidades**:
  - Salva arquivos de vídeo completos no navegador
  - Recupera fila ao reabrir o site
  - Remove vídeos concluídos automaticamente
  - Suporta arquivos grandes (GB)

---

## 🛠️ Como Rodar

### 1. Reconstruir containers Docker

```powershell
docker-compose down
docker-compose up --build
```

> **Importante**: O `--build` é necessário para instalar a nova dependência `idb`.

### 2. Testar Backend

```powershell
cd backend
python test_book_endpoints.py
```

Este script testa:
- ✅ Autenticação
- ✅ Criação de livros
- ✅ Listagem de livros
- ✅ Detalhes de livros
- ✅ Validação de dados
- ✅ Segurança (JWT)

### 3. Acessar Frontend

1. Abra: `http://localhost:3000`
2. Faça login
3. Você será redirecionado para `/dashboard` (lista de livros)
4. Crie um novo livro
5. Clique em "Adicionar Vídeos"
6. Faça upload de vídeos

---

## 🎯 Fluxo Completo de Uso

### Primeira Vez

1. **Login** → Redireciona para `/dashboard`
2. **Dashboard vazio** → Clique em "Criar Novo Livro"
3. **Modal** → Digite o título do livro
4. **Livro criado** → Aparece no dashboard
5. **Clique em "Adicionar Vídeos"** → Vai para `/upload/{bookId}`
6. **Upload** → Arraste vídeos ou clique para selecionar
7. **Fila** → Vídeos são enviados um por vez, na ordem

### Retomando Uploads

1. **Fechar navegador** durante upload
2. **Reabrir site** → Modal pergunta: "Continuar uploads pendentes?"
3. **Clicar em "Continuar"** → Uploads retomam automaticamente
4. **Ou "Descartar"** → Limpa a fila

---

## 📂 Arquivos Criados/Modificados

### Backend
- ✅ `backend/schemas/book_schemas.py` (novo)
- ✅ `backend/routes/book_routes.py` (novo)
- ✅ `backend/main.py` (modificado - adicionado book_router)
- ✅ `backend/test_book_endpoints.py` (novo)

### Frontend
- ✅ `frontend/src/components/BooksDashboard.tsx` (novo)
- ✅ `frontend/src/components/CreateBookModal.tsx` (novo)
- ✅ `frontend/src/components/ResumePendingUploadsModal.tsx` (novo)
- ✅ `frontend/src/utils/uploadQueue.ts` (novo)
- ✅ `frontend/src/components/UploadDashboard.tsx` (refatorado)
- ✅ `frontend/src/App.tsx` (modificado - novas rotas)
- ✅ `frontend/package.json` (adicionado `idb`)

---

## 🔧 Mudanças Importantes

### Upload Sequencial
- **Antes**: 3 uploads paralelos simultâneos
- **Depois**: 1 upload por vez (sequencial)
- **Motivo**: Melhor controle e confiabilidade

### Persistência
- **Antes**: Fila perdida ao fechar navegador
- **Depois**: Fila salva no IndexedDB, retomada automática

### Fluxo de Navegação
- **Antes**: Login → Upload direto (com BOOK_ID fake)
- **Depois**: Login → Dashboard de Livros → Upload por livro

---

## ⚠️ Notas Técnicas

### IndexedDB
- Armazena objetos `File` completos
- Limite de armazenamento: Depende do navegador (geralmente GB)
- Dados persistem até serem explicitamente removidos

### Validações
- Título do livro: Não pode estar vazio
- Vídeos: MP4, AVI, MOV, MKV, WebM
- Tamanho máximo: 2GB por vídeo
- Ownership: Usuário só acessa seus próprios livros

---

## 🐛 Troubleshooting

### Erro "Module not found: idb"
```powershell
docker-compose down
docker-compose up --build
```

### Uploads não retomam
- Verifique se o navegador permite IndexedDB
- Limpe o cache se necessário: `Ctrl+Shift+Delete`

### Erro 403 ao acessar livro
- O livro não pertence ao usuário autenticado
- Faça login com o usuário correto

---

## 📊 Estrutura do Banco de Dados

### Tabela `books`
- `id` (UUID) - Primary Key
- `author_profile_id` (UUID) - Foreign Key para user_auth
- `title` (String) - Título do livro
- `author` (String) - Nome do autor (preenchido automaticamente)
- `status` (String) - PENDING, PROCESSING, COMPLETED
- `created_at` (DateTime) - Data de criação

### Tabela `videos`
- `id` (UUID) - Primary Key
- `book_id` (UUID) - Foreign Key para books
- `storage_path` (String) - Caminho no Gemini File API
- `duration` (Float) - Duração em segundos
- `filename` (String) - Nome do arquivo
- `created_at` (DateTime) - Data de criação

---

## 🎨 Design

- **Estilo**: Glassmorphism com gradientes dark
- **Cores**: Purple/Indigo com slate
- **Ícones**: Lucide React
- **Consistência**: Todos os componentes seguem o mesmo padrão visual

---

## ✅ Checklist de Testes

- [ ] Login funciona
- [ ] Dashboard lista livros corretamente
- [ ] Criar novo livro funciona
- [ ] Modal de criação valida título vazio
- [ ] Clicar em "Adicionar Vídeos" redireciona corretamente
- [ ] Upload de vídeo funciona
- [ ] Progress bar atualiza corretamente
- [ ] Uploads acontecem 1 por vez (sequencial)
- [ ] Fechar navegador durante upload
- [ ] Reabrir mostra modal de retomada
- [ ] Continuar retoma uploads
- [ ] Descartar limpa a fila
- [ ] Botão "Voltar" funciona
- [ ] Logout funciona
