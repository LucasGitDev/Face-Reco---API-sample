# Importando as bibliotecas necessárias
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pysondb import db

from flask_uploads import UploadSet, configure_uploads, IMAGES
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import cv2
import os
import numpy as np
from PIL import Image
import io

# Criando a aplicação Flask
app = Flask(__name__)

# Configurando o JWT
app.config["JWT_SECRET_KEY"] = "secret" # Você deve usar uma chave secreta mais segura na prática
jwt = JWTManager(app)

# Configurando o Flask-Uploads
photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = 'uploads'
configure_uploads(app, photos)

# Criando o banco de dados pysonDB
db_path = os.path.join(os.path.dirname(__file__), "users.json")
db_users = db.getDb(db_path)


db_photos_path = os.path.join(os.path.dirname(__file__), "photos.json")
db_photos = db.getDb(db_photos_path)



diretorio_treinamento = os.path.join(os.path.dirname(__file__), "uploads")

"""
    [Modelo de dados]
"""

# Criando o modelo User
class User:
    # O construtor recebe os atributos do usuário: id, nome, email e senha
    def __init__(self, id, name, email, password, photos=[]):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.photos = photos
    
    # O método to_dict converte o objeto User em um dicionário
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "photos": self.photos
        }
    
    # O método from_dict cria um objeto User a partir de um dicionário
    @staticmethod
    def from_dict(data):
        return User(
            data.get("id"),
            data.get("name"),
            data.get("email"),
            data.get("password"),
            data.get("photos")
        )
    
    # O método save salva o usuário no banco de dados
    def save(self):
        db_users.add(self.to_dict())
    
    # O método update atualiza os dados do usuário no banco de dados
    def update(self):
        db_users.update({"id": self.id}, self.to_dict())
    
    def add_photo(self, photo: int):
        self.photos.append(photo)
        self.update()

    # O método delete remove o usuário do banco de dados
    def delete(self):
        db_users.deleteById(self.id)
    
    # O método find_by_id busca um usuário pelo seu id no banco de dados e retorna um objeto User ou None se não encontrar
    @staticmethod
    def find_by_id(id):
        data = db_users.getByQuery({"id": id})
        if data:
            return User.from_dict(data[0])
        else:
            return None
    
    # O método find_by_email busca um usuário pelo seu email no banco de dados e retorna um objeto User ou None se não encontrar
    @staticmethod
    def find_by_email(email):
        data = db_users.getByQuery({"email": email})
        if data:
            return User.from_dict(data[0])
        else:
            return None


class Photo:

    def __init__(self, id, path, user_id):
        self.id = id
        self.path = path
        self.user_id = user_id
    
    def to_dict(self):
        return {
            "id": self.id,
            "path": self.path,
            "user_id": self.user_id
        }
    
    @staticmethod
    def from_dict(data):
        return Photo(
            data.get("id"),
            data.get("path"),
            data.get("user_id")
        )
    
    def save(self):
        db_photos.add(self.to_dict())
    
    def update(self):
        db_photos.update({"id": self.id}, self.to_dict())
    
    def delete(self):
        db_photos.deleteById(self.id)
    

    def get_new_file_name(self):
        return str(self.id)[:5]+str(self.id)[-3:]
    

    @staticmethod
    def find_by_id(id):
        data = db_photos.getByQuery({"id": id})
        if data:
            return Photo.from_dict(data[0])
        else:
            return None

    @staticmethod
    def find_by_user_id(user_id):
        data = db_photos.getByQuery({"user_id": user_id})
        if data:
            return [Photo.from_dict(photo) for photo in data]
        else:
            return None
        
    @staticmethod
    def find_by_path(path):
        data = db_photos.getByQuery({"path": path})
        if data:
            return Photo.from_dict(data[0])
        else:
            return None
    
    @staticmethod
    def find_by_partial_path(path):
        data = db_photos.reSearch("path", '.*'+path+'.*')
        if data:
            return [Photo.from_dict(photo) for photo in data]
        else:
            return None

    @staticmethod
    def find_by_user_id_and_path(user_id, path):
        data = db_photos.getByQuery({"user_id": user_id, "path": path})
        if data:
            return Photo.from_dict(data[0])
        else:
            return None
    
"""
    [Utils]
"""

def carregar_imagens_treinamento(diretorio):
    imagens = []
    ids = []
    for nome in os.listdir(diretorio):
        if nome.endswith('.jpg') or nome.endswith('.png'):
            caminho = os.path.join(diretorio, nome)
            imagem_pil = Image.open(caminho).convert('L')
            imagem_np = np.array(imagem_pil, 'uint8')
            ids.append(int(nome.split('.')[0]))
            imagens.append(imagem_np)
    return imagens, ids

def adicionar_pessoa(diretorio_treinamento, nome, foto):
    if not os.path.exists(diretorio_treinamento):
        os.makedirs(diretorio_treinamento)
    
    caminho_destino = os.path.join(diretorio_treinamento, f'{nome}.jpg')
    
    foto.save(caminho_destino)
    print(f'Foto de {nome} adicionada com sucesso!')

def validar_rosto(diretorio_treinamento, foto):
    reconhecimento = cv2.face.LBPHFaceRecognizer_create()
    imagens_treinamento, ids_treinamento = carregar_imagens_treinamento(diretorio_treinamento)

    reconhecimento.train(imagens_treinamento, np.array(ids_treinamento))
    imagens_treinamento, ids_treinamento = carregar_imagens_treinamento(diretorio_treinamento)

    print(f'OS TREINAMENTOS: {ids_treinamento}')
    detector_rosto = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    img_pil = Image.open(foto)
    img_np = np.array(img_pil, 'uint8')
    cinza = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
    
    faces = detector_rosto.detectMultiScale(cinza, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    reconhecido = False
    id_previstos = []

    for (x, y, w, h) in faces:
        rosto_capturado = cinza[y:y+h, x:x+w]
        id_previsto, confianca = reconhecimento.predict(rosto_capturado)

        if confianca < 100: 
            reconhecido = True
            id_previstos.append(id_previsto)

    return reconhecido, id_previstos

def preprocess_image(image):
    # Converta a imagem para tons de cinza
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Aplique equalização de histograma para melhorar o contraste
    equalized_image = cv2.equalizeHist(gray_image)


    return equalized_image

"""
    [Rotas]
"""

# Criando a rota de cadastro de usuário
@app.route("/register", methods=["POST"])
def register():
    # Recebendo os dados do usuário no formato JSON
    data = request.get_json()
    
    # Validando se os dados estão completos e se o email já não está cadastrado
    if not data or not data.get("name") or not data.get("email") or not data.get("password"):
        return jsonify({"message": "Dados inválidos"}), 400
    
    if User.find_by_email(data.get("email")):
        return jsonify({"message": "Email já cadastrado"}), 409
    
    # Criando um objeto User com os dados recebidos e gerando um id aleatório usando a função get_id
    user = User(0, data.get("name"), data.get("email"), data.get("password")) # Usando a função get_id em vez do método getId
    
    # Salvando o usuário no banco de dados
    user.save()
    # Retornando uma resposta com os dados do usuário e um status 201 (Created)
    return jsonify({"message": "Usuário cadastrado com sucesso"}), 201

# Criando a rota de login de usuário
@app.route("/login", methods=["POST"])
def login():
    # Recebendo os dados do usuário no formato JSON
    data = request.get_json()
    
    # Validando se os dados estão completos e se o email e a senha estão corretos
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"message": "Dados inválidos"}), 400
    
    user = User.find_by_email(data.get("email"))
    
    if not user or user.password != data.get("password"):
        return jsonify({"message": "Email ou senha incorretos"}), 401
    
    # Gerando um token de acesso para o usuário usando o JWT
    access_token = create_access_token(identity=user.id)
    
    # Retornando uma resposta com o token de acesso e um status 200 (OK)
    return jsonify({"access_token": access_token}), 200

# Criando a rota /me que retorna as informações do usuário autenticado
@app.route("/me", methods=["GET"])
@jwt_required() # Essa função decoradora exige que o usuário envie um token de acesso válido no cabeçalho Authorization
def me():
    # Obtendo o id do usuário a partir do token de acesso
    user_id = get_jwt_identity()
    
    # Buscando o usuário pelo seu id no banco de dados
    user = User.find_by_id(user_id)
    
    # remover senha do objeto user
    user.password = None
    # Retornando uma resposta com os dados do usuário e um status 200 (OK)
    return jsonify(user.to_dict()), 200


@app.route("/add-photo", methods=["POST"])
@jwt_required()
def add_photo():
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({"message": "Usuário não encontrado"}), 404
    
    foto = request.files.get('foto')

    photo = Photo(0, '', user_id)
    photo.save()

    photo = Photo.find_by_user_id_and_path(user_id, photo.path)
    
    if foto and foto.filename.endswith(('.jpg', '.png')):
        primeiros_5_digitos = photo.get_new_file_name()
        path = f'{diretorio_treinamento}/{primeiros_5_digitos}.{foto.filename.split(".")[-1]}'
        updated_photo = Photo(photo.id, path, user_id)
        updated_photo.update()
        user.add_photo(updated_photo.id)


        # Carregue a imagem usando OpenCV
        img_pil = Image.open(foto)
        img_np = np.array(img_pil, 'uint8')

        # Realize o pré-processamento da imagem
        processed_img = preprocess_image(img_np)

        # Crie um objeto BytesIO a partir dos bytes da imagem processada
        processed_img_io = io.BytesIO()
        processed_img_pil = Image.fromarray(processed_img)  # Converta para um objeto de imagem
        processed_img_pil.save(processed_img_io, format='JPEG')  # Salve a imagem no objeto BytesIO
        
        # Crie um objeto FileStorage a partir do objeto BytesIO
        processed_img_io.seek(0)  # Reinicie o ponteiro do BytesIO para o início
        processed_img_file = FileStorage(stream=processed_img_io,
                                         filename=foto.filename,
                                         content_type='image/jpeg')  # Ajuste o tipo de conteúdo conforme necessário
     
        # Adicione a imagem pré-processada
        adicionar_pessoa(diretorio_treinamento, primeiros_5_digitos, processed_img_file)
        
        return jsonify({'message': f'Foto de {user.name} adicionada com sucesso!'}), 201
    
    return jsonify({'message': 'Foto inválida'}), 400


@app.route('/validate', methods=['POST'])
@jwt_required()
def validar_rosto_endpoint():

    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({"message": "Usuário não encontrado"}), 404
    
    foto = request.files.get('foto')
    
    if foto and foto.filename.endswith(('.jpg', '.png')):
        reconhecido, file_name = validar_rosto(diretorio_treinamento, foto)

        if not reconhecido:
            return jsonify({'message': 'Pessoa não reconhecida.'}), 200

        print(f'ID RECO {file_name}')
        photo = Photo.find_by_partial_path(str(file_name[0]))
        user_id_founded = photo[0].user_id
        
        user = User.find_by_id(user_id_founded)

        return jsonify({'message': f'Pessoa reconhecida. {user.name}'}), 200
    else:
        return jsonify({'error': 'Arquivo inválido'}), 400

# Iniciando a aplicação Flask
if __name__ == "__main__":
    app.run(debug=True)
