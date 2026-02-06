# 🚀 Feature: Frontend Video Upload Dashboard

Este branch implementa a interface visual completa para o sistema de upload de vídeos do Lectria.

## 📦 O que foi implementado

### 1. Novo Dashboard de Upload (`UploadDashboard.tsx`)
- **Drag-and-Drop**: Área interativa para arrastar vídeos.
- **Upload Paralelo**: Suporte para múltiplos uploads simultâneos (fila inteligente).
- **Progress Bars**: Feedback visual em tempo real do progresso.
- **Validação**: Verificação de tipos de arquivo (MP4, MKV, etc.) e tamanho máximo (2GB).
- **Design Moderno**: Estilo "Glassmorphism" com gradientes, seguindo a identidade visual da AuthPage.

### 2. Sistema de Rotas (`react-router-dom v6`)
- **Rotas Protegidas**: O dashboard só é acessível após login.
- **Redirecionamento**: Login bem-sucedido redireciona automaticamente para `/dashboard`.
- **Rota Default**: `/` redireciona para `/login`.

### 3. Autenticação Integrada
- Recuperação automática do Token JWT do `localStorage`.
- Bloqueio de acesso não autorizado (`ProtectedRoute.tsx`).

---

## 🛠️ Como rodar

1. **Instalar novas dependências**:
   ```bash
   cd frontend
   npm install
   ```

2. **Iniciar o frontend**:
   ```bash
   npm start
   ```

3. **Acessar**: `http://localhost:3000`

---

## ⚠️ Configuração Importante (BOOK_ID)

Para facilitar a visualização e testes da interface sem necessidade de configurar o banco de dados manualmente a cada execução, o código está configurado com um **UUID TEMPORÁRIO**.

**Arquivo**: `frontend/src/components/UploadDashboard.tsx`
```typescript
// TEMPORARY: UUID fake apenas para VISUALIZAR o dashboard
const BOOK_ID = '00000000-0000-0000-0000-000000000000';
```

> **Nota**: Com este ID, os uploads falharão (erro 404/403 do backend), mas **toda a interface visual funcionará**. Para funcionamento em produção, este ID deve ser substituído pelo UUID de um livro real criado no banco de dados.

---

## 📂 Arquivos Criados/Modificados

- `frontend/src/components/UploadDashboard.tsx` (Novo)
- `frontend/src/components/ProtectedRoute.tsx` (Novo)
- `frontend/src/App.tsx` (Modificado com rotas)
- `frontend/src/App.test.tsx` (Corrigido para v6)
- `frontend/package.json` (Dependência react-router-dom)

---

## ✅ Próximos Passos (Checklist)

- [ ] Criar livro real no banco de dados PostgreSQL.
- [ ] Atualizar `BOOK_ID` no código ou implementar seletor de livros na UI.
- [ ] Implementar visualização dos vídeos após upload.
