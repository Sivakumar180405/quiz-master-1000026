from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, login_user, logout_user, current_user
from models.models import User, Subject, Chapter, Quiz, Question, Score, db as database
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        pw = request.form.get('password')

        admin = User.query.filter_by(email=email, is_admin=True).first()

        if admin and admin.password == pw: 
            login_user(admin)
            return redirect(url_for('main.admin_db'))

    return render_template('admin_login.html')

@main.route('/admin/dashboard')
def admin_db():
    subjects = Subject.query.all()
    return render_template('admin_db.html', subjects=subjects)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        new_user = User(email=email, password=password, full_name=name)
        database.session.add(new_user)
        database.session.commit()
        return redirect(url_for('main.login'))
    return render_template('register.html')

@main.route('/admin/subject_create', methods=['GET', 'POST'])
def subject_create():
    if request.method == 'POST':
        sub_name = request.form.get('name')
        sub_description = request.form.get('description')

        new_subject = Subject(name=sub_name, description=sub_description)
        database.session.add(new_subject)
        database.session.commit()
        return redirect(url_for('main.admin_db'))

    return render_template('subject_create.html')

@main.route('/admin/subject_delete/<int:subject_id>')
@login_required
def subject_delete(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    for chapter in subject.chapters:
        database.session.delete(chapter)

    database.session.delete(subject)
    database.session.commit()

    return redirect(url_for('main.admin_db'))

@main.route('/subject_search', methods=['GET'])
@login_required
def subject_search():
    query = request.args.get('query', '').strip()
    subjects = []

    if query:
        subjects = Subject.query.filter(Subject.name.ilike(f"%{query}%")).all()

    return render_template('subject_search.html', subjects=subjects, query=query)

@main.route('/admin/chapter_create/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def chapter_create(subject_id):
    if request.method == 'POST':
        chap_name = request.form.get('name')

        new_chapter = Chapter(name=chap_name, subject_id=subject_id)
        database.session.add(new_chapter)
        database.session.commit()

        return redirect(url_for('main.admin_db'))

    return render_template('chapter_create.html', subject_id=subject_id)

@main.route('/admin/chapter_delete/<int:chapter_id>')
@login_required
def chapter_delete(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)

    for quiz in chapter.quizzes:
        database.session.delete(quiz)

    database.session.delete(chapter)
    database.session.commit()

    return redirect(url_for('main.admin_db'))

@main.route('/chapter_search', methods=['GET'])
@login_required
def chapter_search():
    query = request.args.get('query', '').strip()
    chapters = []

    if query:
        chapters = Chapter.query.filter(Chapter.name.ilike(f"%{query}%")).all()

    return render_template('chapter_search.html', chapters=chapters, query=query)

@main.route('/admin/quiz_create/<int:chapter_id>', methods=['GET', 'POST'])
@login_required
def quiz_create(chapter_id):
    if request.method == 'POST':
        quiz_name = request.form.get('quiz_name')
        date_of_quiz = request.form.get('date_of_quiz')

        date_of_quiz = datetime.strptime(date_of_quiz, "%Y-%m-%d").date()

        duration = request.form.get('duration')

        new_quiz = Quiz(name=quiz_name, chapter_id=chapter_id, date_of_quiz=date_of_quiz, duration=duration)
        database.session.add(new_quiz)
        database.session.commit()

        return redirect(url_for('main.admin_db'))

    return render_template('quiz_create.html', chapter_id=chapter_id)

@main.route('/admin/quiz_delete/<int:quiz_id>')
@login_required
def quiz_delete(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    for question in quiz.questions:
        database.session.delete(question)

    database.session.delete(quiz)
    database.session.commit()

    return redirect(url_for('main.admin_db'))

@main.route('/quiz_search', methods=['GET'])
@login_required
def quiz_search():
    query = request.args.get('query', '').strip()
    quizzes = []

    if query:
        quizzes = Quiz.query.filter(Quiz.name.ilike(f"%{query}%")).all()
    print(current_user.is_admin)
    
    return render_template('quiz_search.html', quizzes=quizzes, query=query)

@main.route('/admin/add_question/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if request.method == 'POST':
        question = request.form.get('question_text')
        option1 = request.form.get('option1')
        option2 = request.form.get('option2')
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        correct_option = request.form.get('correct_option')
        action = request.form.get('action')

        new_question = Question(
            quiz_id=quiz.id,
            question_text=question,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=int(correct_option)  
        )
        database.session.add(new_question)
        database.session.commit()

        if action == "add_another":
            return redirect(url_for('main.add_question', quiz_id=quiz_id))
        else:
            return redirect(url_for('main.admin_db'))

    return render_template('add_question.html', quiz_id=quiz_id)

@main.route('/admin/all_results')
@login_required
def all_results():
    if not current_user.is_admin:
        return redirect(url_for('main.admin_db'))
    
    search = request.args.get('query', '').strip() 
    scores = database.session.query(Score.score, Score.timestamp, User.full_name.label("user_name"),User.email.label("user_email"), Quiz.name.label("quiz_name")).join(User, Score.user_id == User.id).join(Quiz, Score.quiz_id == Quiz.id)

    if search:
        scores = scores.filter((User.full_name.ilike(f"%{search}%")))

    results = scores.all() 

    return render_template('all_results.html', scores=results)
    
@main.route('/admin/score_chart')
@login_required
def score_chart():
    if not current_user.is_admin:
        return redirect(url_for('main.admin_dashboard'))

    scores = database.session.query(User.full_name, Score.score, Quiz.name, Chapter.name).join(User).join(Quiz).join(Chapter).all()

    if not scores:
        return "No scores available"

    usernames = [f"{score[0]} ({score[3]}:{score[2]})" for score in scores] 
    scores_data = [score[1] for score in scores]  

    plt.figure(figsize=(10, 6))
    plt.bar(usernames, scores_data, color='green')
    plt.xlabel("Users and Quizzes")
    plt.ylabel("Scores")
    plt.title("All Quiz Scores")
    plt.xticks(rotation=30, ha='right')

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches="tight")
    img.seek(0)
    graph = base64.b64encode(img.getvalue()).decode()

    return render_template('score_chart.html', graph=graph)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('name')
        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('main.db'))
    return render_template('login.html')

@main.route('/dashboard')
@login_required
def db():
    subjects = Subject.query.all()
    return render_template('db.html', subjects=subjects)

@main.route('/start_quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    if request.method == 'POST':
        score = 0
        for question in questions:
            user_answer = request.form.get(f'question_{question.id}')
            if user_answer and int(user_answer) == question.correct_option:
                score += 4
            else:
                score -= 1

        submission_date = datetime.now()

        final_score = Score(quiz_id=quiz_id, user_id=current_user.id, score=score, timestamp=submission_date)
        database.session.add(final_score)
        database.session.commit()

        return redirect(url_for('main.results'))

    return render_template('start_quiz.html', quiz=quiz, questions=questions)

@main.route('/results')
@login_required
def results():
    scores = Score.query.filter_by(user_id=current_user.id).join(Quiz).add_columns(Score.score, Quiz.name.label("quiz_name"), Score.timestamp).all()

    quiz_names = [score.quiz_name for score in scores]
    quiz_scores = [score.score for score in scores]

    plt.figure(figsize=(8, 4))
    plt.bar(quiz_names, quiz_scores, color='black')
    plt.xlabel('Quiz Name')
    plt.ylabel('Score')
    plt.title('Your Quiz Scores')
    plt.xticks(rotation=45)

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches="tight")
    img.seek(0)
    chart = base64.b64encode(img.getvalue()).decode()

    return render_template('results.html', scores=scores, chart=chart)

@main.route('/user_quiz_search', methods=['GET'])
@login_required
def user_quiz_search():
    query = request.args.get('query', '').strip()
    quizzes = []

    if query:
        quizzes = Quiz.query.filter(Quiz.name.ilike(f"%{query}%")).join(Chapter).all()
    # print([quiz.chapter.name for quiz in quizzes])
    
    return render_template('user_quiz_search.html', quizzes=quizzes, query=query)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))