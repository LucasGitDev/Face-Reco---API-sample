# Face Reco Sample

### Como rodar o projeto (pipenv)

1. Instale o pipenv
2. Instale as dependências do projeto
3. Rode o projeto

```bash
pip install pipenv
pipenv install
pipenv run python main.py
```

### O que é e como funciona

O projeto consiste em um sistema de reconhecimento facial, que utiliza a biblioteca OpenCV para analisar imagens
que foram enviadas através da API rest, e então, caso a imagem seja de uma pessoa cadastrada no sistema, o sistema
retorna o nome da pessoa, caso contrário, retorna uma mensagem de erro.

### Como utilizar

Para utilizar o sistema, é necessário enviar uma imagem para a API.

Uma ferramenta que pode ser utilizada para o consumo da API é o Insomnia. Usando o Insomnia, faça a importação do arquivo `Insomnia_2023-08-14.json` que está na raiz do projeto.

Após importar o arquivo, cadastre usuários e realize o login com o usuário que receberá uma nova foto.
Utilize a rota de adição de imagem para enviar uma imagem para o sistema, e então, utilize a rota de reconhecimento facial para verificar se a imagem enviada é de um usuário cadastrado no sistema.


### Problemas conhecidos

- O seguinte erro na primeira execução do projeto:

```bash
Traceback (most recent call last):
  File "/home/user/Face Reco Sample/api/main.py", line 6, in <module>
    from flask_uploads import UploadSet, configure_uploads, IMAGES
  File "/home/user/.local/share/virtualenvs/api-VnkAG_RD/lib/python3.10/site-packages/flask_uploads.py", line 26, in <module>
    from werkzeug import secure_filename, FileStorage
ImportError: cannot import name 'secure_filename' from 'werkzeug' (/home/user/.local/share/virtualenvs/api-VnkAG_RD/lib/python3.10/site-packages/werkzeug/__init__.py)
```

Para resolver esse problema, siga as instruções no link abaixo:

https://stackoverflow.com/questions/61628503/flask-uploads-importerror-cannot-import-name-secure-filename