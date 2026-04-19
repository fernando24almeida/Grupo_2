…or create a new repository on the command line
echo "# Grupo_2" >> README1.md
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/fernando24almeida/Grupo_2.git
git push -u origin main


…or push an existing repository from the command line
git remote add origin https://github.com/fernando24almeida/Grupo_2.git
git branch -M main
git push -u origin main


O repositório frontend está dentro do projeto principal como um repositório
  separado (submódulo). Se quiseres enviar tudo para o mesmo sítio no GitHub,
  recomendo apagar a pasta .git de dentro de frontend.

  Diz-me se preferes:
   1. Tudo num único repositório no GitHub (mais simples).
   2. Repositórios separados (um para o backend/root e outro para o
  1. Limpar as configurações atuais e preparar os ficheiros:
  Executa estes comandos no terminal da pasta raiz (urgencias_hospitalares):

   1 # 1. Remove a pasta .git do frontend (isso não apaga os teus ficheiros,
     apenas o controlo de versões separado)
   2 Remove-Item -Recurse -Force "frontend\.git"
   3
   4 # 2. Limpa o que estava preparado para ser enviado
   5 git rm -r --cached .
   6
   7 # 3. Adiciona tudo de novo (agora respeitando o .gitignore que criei)
   8 git add .

  2. Configurar o GitHub e Fazer o Primeiro Commit:

  Depois disso, precisas de criar um repositório no GitHub (ex:
  urgencias-hospitalares) e seguir estes passos:

    1 # 1. Cria o primeiro commit
    2 git commit -m "Primeira versao do projeto"
    3
    4 # 2. Muda o nome da branch para 'main' (padrao do GitHub)
    5 git branch -M main
    6
    7 # 3. Adiciona o endereço do teu repositório (substitui pelo teu URL do
      GitHub)
    8 git remote add origin
      https://github.com/fernando24almeida/Grupo_2.git
    9
   10 # 4. Envia os ficheiros
   11 git push -u origin main