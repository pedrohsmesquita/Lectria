# Frontend Dockerfile - React with Hot Reload
FROM node:18-alpine

# Definir diretório de trabalho
WORKDIR /app

# Copiar package.json e package-lock.json
COPY package*.json ./

# Instalar dependências
RUN npm install

# Copiar código da aplicação
COPY . .

# Expor porta do servidor de desenvolvimento
EXPOSE 3000

# Comando para iniciar o servidor de desenvolvimento com Hot Reload
CMD ["npm", "start"]
