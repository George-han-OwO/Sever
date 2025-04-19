from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

# 初始化 Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

# 初始化 LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 数据库模型

# 用户模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    emeralds = db.Column(db.Integer, default=100)
    last_signin = db.Column(db.Date, default=datetime.utcnow)
    inventory = db.relationship('Item', backref='owner', lazy=True)

# 物品模型
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rarity = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# 创建数据库表
with app.app_context():
    db.create_all()

# 登录管理
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 首页
@app.route('/')
def home():
    return render_template('index.html')

# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('登录失败，检查用户名和密码！', 'danger')
    return render_template('login.html')

# 注册页面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('用户名已存在！', 'danger')
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功！请登录。', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# 用户仪表盘
@app.route('/dashboard')
@login_required
def dashboard():
    user_items = Item.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', emeralds=current_user.emeralds, items=user_items)

# 每日签到
@app.route('/signin', methods=['POST'])
@login_required
def signin():
    today = datetime.utcnow().date()
    if current_user.last_signin != today:
        current_user.last_signin = today
        current_user.emeralds += 100  # 每日签到增加100绿宝石
        db.session.commit()
        flash('签到成功，获得100绿宝石！', 'success')
    else:
        flash('今天已经签到过了！', 'info')
    return redirect(url_for('dashboard'))

# 出售物品
@app.route('/sell_item/<int:item_id>', methods=['POST'])
@login_required
def sell_item(item_id):
    item = Item.query.get(item_id)
    if item and item.user_id == current_user.id:
        current_user.emeralds += item.value
        db.session.delete(item)
        db.session.commit()
        flash(f'{item.name} 已出售，获得 {item.value} 绿宝石！', 'success')
    return redirect(url_for('dashboard'))

# 退出登录
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
