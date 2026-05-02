# Instalar dependências
COPY package.json package-lock.json ./
RUN npm install

# Copiar o código e gerar a build de produção
COPY . .
RUN npm run build

# Estágio 2: Servir com Nginx
FROM nginx:alpine

# Copiar a build
COPY --from=build /app/build /usr/share/nginx/html

# Copiar config nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Porta do Render
EXPOSE 10000

CMD ["nginx", "-g", "daemon off;"]
