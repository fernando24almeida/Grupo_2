# Estágio 1: Build da aplicação React
FROM node:18-alpine AS build

WORKDIR /app

# Instalar dependências
COPY package.json package-lock.json ./
RUN npm install

# Copiar o código e gerar a build de produção
COPY . .
RUN npm run build

# Estágio 2: Servir com Nginx
FROM nginx:alpine

# Copiar a build para o diretório do Nginx
COPY --from=build /app/build /usr/share/nginx/html

# Copiar a configuração personalizada do Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expor a porta 80
EXPOSE 10000

CMD ["nginx", "-g", "daemon off;"]
