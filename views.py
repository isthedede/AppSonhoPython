from flask import render_template, redirect, url_for, request, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from app import app, db, login_manager
from models import Usuario, Sonho, Categoria, Importacao
from werkzeug.security import generate_password_hash, check_password_hash
import json
import io
import zipfile
import requests

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        username = request.form['username']
        senha = request.form['senha']
        if Usuario.query.filter_by(username=username).first():
            flash('Usuário já existe!')
            return redirect(url_for('cadastro'))
        usuario = Usuario(
            nome=nome,
            username=username,
            senha=generate_password_hash(senha)
        )
        db.session.add(usuario)
        db.session.commit()
        flash('Cadastro realizado! Faça login.')
        return redirect(url_for('login'))
    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['password']
        usuario = Usuario.query.filter_by(username=username).first()
        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            return redirect(url_for('menu'))
        else:
            flash('Usuário ou senha inválidos!')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/menu')
@login_required
def menu():
    return render_template('menu.html')

@app.route('/sonhos')
@login_required
def listar_sonhos():
    sonhos = Sonho.query.filter_by(usuario_id=current_user.id).all()
    return render_template('sonhos.html', sonhos=sonhos)

@app.route('/sonhos/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_sonho():
    categorias = Categoria.query.all()
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        data = request.form['data']
        status = request.form['status']
        categoria_id = request.form.get('categoria_id')
        sonho = Sonho(
            titulo=titulo,
            descricao=descricao,
            data=data,
            status=status,
            usuario_id=current_user.id,
            categoria_id=categoria_id if categoria_id else None
        )
        db.session.add(sonho)
        db.session.commit()
        flash('Sonho adicionado!')
        return redirect(url_for('listar_sonhos'))
    return render_template('adicionar_sonho.html', categorias=categorias)

@app.route('/sonhos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_sonho(id):
    sonho = Sonho.query.get_or_404(id)
    if sonho.usuario_id != current_user.id:
        flash('Acesso negado!')
        return redirect(url_for('listar_sonhos'))
    categorias = Categoria.query.all()
    if request.method == 'POST':
        sonho.titulo = request.form['titulo']
        sonho.descricao = request.form['descricao']
        sonho.data = request.form['data']
        sonho.status = request.form['status']
        sonho.categoria_id = request.form.get('categoria_id')
        db.session.commit()
        flash('Sonho atualizado!')
        return redirect(url_for('listar_sonhos'))
    return render_template('editar_sonho.html', sonho=sonho, categorias=categorias)

@app.route('/sonhos/deletar/<int:id>', methods=['POST'])
@login_required
def deletar_sonho(id):
    sonho = Sonho.query.get_or_404(id)
    if sonho.usuario_id != current_user.id:
        flash('Acesso negado!')
        return redirect(url_for('listar_sonhos'))
    db.session.delete(sonho)
    db.session.commit()
    flash('Sonho deletado!')
    return redirect(url_for('listar_sonhos'))

@app.route('/categorias')
@login_required
def listar_categorias():
    categorias = Categoria.query.all()
    return render_template('categorias.html', categorias=categorias)

@app.route('/categorias/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_categoria():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        categoria = Categoria(nome=nome, descricao=descricao)
        db.session.add(categoria)
        db.session.commit()
        flash('Categoria adicionada!')
        return redirect(url_for('listar_categorias'))
    return render_template('adicionar_categoria.html')

@app.route('/categorias/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    if request.method == 'POST':
        categoria.nome = request.form['nome']
        categoria.descricao = request.form['descricao']
        db.session.commit()
        flash('Categoria atualizada!')
        return redirect(url_for('listar_categorias'))
    return render_template('editar_categoria.html', categoria=categoria)

@app.route('/categorias/deletar/<int:id>', methods=['POST'])
@login_required
def deletar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    db.session.delete(categoria)
    db.session.commit()
    flash('Categoria deletada!')
    return redirect(url_for('listar_categorias'))

@app.route('/exportar')
@login_required
def exportar():
    usuarios = Usuario.query.all()
    sonhos = Sonho.query.all()
    categorias = Categoria.query.all()
    data = {
        'usuarios': [
            {'id': u.id, 'nome': u.nome, 'username': u.username} for u in usuarios
        ],
        'sonhos': [
            {'id': s.id, 'titulo': s.titulo, 'descricao': s.descricao, 'data': s.data, 'status': s.status, 'usuario_id': s.usuario_id, 'categoria_id': s.categoria_id} for s in sonhos
        ],
        'categorias': [
            {'id': c.id, 'nome': c.nome, 'descricao': c.descricao} for c in categorias
        ]
    }
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('dados.json', json_bytes)
    mem_zip.seek(0)
    return send_file(mem_zip, mimetype='application/zip', as_attachment=True, download_name='dados_sonhos.zip')

@app.route('/importar', methods=['GET', 'POST'])
@login_required
def importar():
    dados_importados = None
    resumo = None
    if request.method == 'POST':
        url = request.form['url']
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                mem_zip = io.BytesIO(resp.content)
                with zipfile.ZipFile(mem_zip) as zf:
                    with zf.open('dados.json') as f:
                        conteudo = f.read().decode('utf-8')
                        imp = Importacao(conteudo=conteudo)
                        db.session.add(imp)
                        db.session.commit()
                        dados = json.loads(conteudo)
                        resumo = {'usuarios': 0, 'categorias': 0, 'sonhos': 0}
                        # Importar usuários
                        for u in dados.get('usuarios', []):
                            if not Usuario.query.filter_by(username=u['username']).first():
                                usuario = Usuario(nome=u['nome'], username=u['username'], senha=generate_password_hash('importado'))
                                db.session.add(usuario)
                                resumo['usuarios'] += 1
                        # Importar categorias
                        for c in dados.get('categorias', []):
                            if not Categoria.query.filter_by(nome=c['nome']).first():
                                categoria = Categoria(nome=c['nome'], descricao=c['descricao'])
                                db.session.add(categoria)
                                resumo['categorias'] += 1
                        db.session.commit()
                        # Importar sonhos (após commit para garantir IDs)
                        for s in dados.get('sonhos', []):
                            usuario = Usuario.query.filter_by(username=s['usuario_id']).first() if isinstance(s['usuario_id'], str) else Usuario.query.get(s['usuario_id'])
                            categoria = Categoria.query.get(s['categoria_id']) if s['categoria_id'] else None
                            if usuario:
                                sonho = Sonho(
                                    titulo=s['titulo'],
                                    descricao=s['descricao'],
                                    data=s['data'],
                                    status=s['status'],
                                    usuario_id=usuario.id,
                                    categoria_id=categoria.id if categoria else None
                                )
                                db.session.add(sonho)
                                resumo['sonhos'] += 1
                        db.session.commit()
                        dados_importados = dados
                        flash(f"Dados importados com sucesso! Usuários: {resumo['usuarios']}, Categorias: {resumo['categorias']}, Sonhos: {resumo['sonhos']}")
            else:
                flash('Erro ao baixar arquivo!')
        except Exception as e:
            flash(f'Erro: {e}')
    return render_template('importar.html', dados=dados_importados, resumo=resumo)

@app.route('/importados')
@login_required
def ver_importados():
    importacoes = Importacao.query.order_by(Importacao.id.desc()).all()
    return render_template('importados.html', importacoes=importacoes) 