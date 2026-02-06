# 📋 Video Upload Dashboard - Setup Instructions

## ⚠️ IMPORTANTE: Configuração do Book ID

Antes de testar o upload de vídeos, você precisa:

### 1. Criar um livro no banco de dados

Execute o seguinte SQL no PostgreSQL:

```sql
-- Primeiro, obtenha o user_auth_id de um usuário existente
SELECT id FROM user_auth LIMIT 1;

-- Depois, crie um livro (substitua 'YOUR_USER_ID' pelo ID obtido acima)
INSERT INTO books (id, author_profile_id, title, author, status, created_at)
VALUES (
    gen_random_uuid(),
    'YOUR_USER_ID',
    'Meu Primeiro Livro',
    'Nome do Autor',
    'PENDING',
    NOW()
)
RETURNING id;
```

### 2. Copiar o UUID do livro criado

O comando acima retornará um UUID. Copie esse valor.

### 3. Atualizar o componente UploadDashboard.tsx

Abra o arquivo:
```
frontend/src/components/UploadDashboard.tsx
```

Na linha 23, substitua o valor de `BOOK_ID`:

```typescript
const BOOK_ID = 'cole-o-uuid-aqui'; // Substituir pelo UUID real do banco
```

---

## 🚀 Como rodar o frontend

1. **Instale as dependências** (se ainda não fez):
   ```bash
   cd frontend
   npm install
   ```

2. **Inicie o servidor de desenvolvimento**:
   ```bash
   npm start
   ```

3. **Acesse no navegador**:
   - Abra: `http://localhost:3000`
   - Você será redirecionado para `/login`

---

## 🧪 Testando o fluxo completo

### Passo 1: Login
1. Acesse `http://localhost:3000/login`
2. Faça login com credenciais válidas
3. Você será automaticamente redirecionado para `/dashboard`

### Passo 2: Upload de vídeos
1. Arraste vídeos para a área de upload OU clique para selecionar
2. Verifique que:
   - ✅ Apenas vídeos são aceitos (MP4, AVI, MOV, MKV, WebM)
   - ✅ Arquivos maiores que 2GB são rejeitados
   - ✅ Progress bars aparecem durante o upload
   - ✅ Até 3 uploads acontecem simultaneamente

### Passo 3: Verificar no backend
1. Acesse o banco de dados PostgreSQL
2. Execute:
   ```sql
   SELECT * FROM videos ORDER BY created_at DESC;
   ```
3. Confirme que os vídeos foram salvos com:
   - `storage_path` do Gemini
   - Metadados corretos (duration, filename, size)

---

## 🎨 Design

O dashboard segue o mesmo estilo visual do AuthPage:
- ✨ Gradiente dark (slate-900 → purple-900)
- 🔮 Glassmorphism (backdrop blur)
- 💜 Cores: Purple/Indigo
- 🎯 Ícones: Lucide React

---

## 🔧 Troubleshooting

### Backend não está rodando
```bash
cd backend
uvicorn main:app --reload
```

### Token JWT expirado
- Limpe o localStorage: `localStorage.clear()` no console do navegador
- Faça login novamente

### Erro 401 Unauthorized
- Verifique se o token está sendo enviado corretamente
- Confirme que o backend está aceitando o token

---

## 📝 Próximos passos (futuro)

- [ ] Permitir usuário criar livros diretamente na UI
- [ ] Seleção de livro antes do upload
- [ ] Preview de vídeo antes do upload
- [ ] Estimativa de tempo restante
- [ ] Cancelamento de upload individual
