import sqlite3
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    abort,
)

app = Flask(__name__)

DATABASE = Path(__file__).resolve().parent / "blog.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)

        # 第一次執行且資料表為空時，加入三篇範例文章
        count = conn.execute(
            "SELECT COUNT(*) FROM posts"
        ).fetchone()[0]

        if count == 0:
            conn.executemany(
                """
                INSERT INTO posts (title, author, content)
                VALUES (?, ?, ?)
                """,
                [
                    (
                        "我的第一篇文章",
                        "小明",
                        "歡迎來到我的 Flask 部落格！"
                    ),
                    (
                        "學習 Flask 的心得",
                        "小華",
                        "今天學會使用 templates 呈現網頁。"
                    ),
                    (
                        "Python 學習筆記",
                        "小美",
                        "使用 SQLite 儲存部落格文章。"
                    ),
                ],
            )


def get_post(post_id):
    with get_db() as conn:
        post = conn.execute(
            "SELECT * FROM posts WHERE id = ?",
            (post_id,),
        ).fetchone()

    if post is None:
        abort(404)

    return post


@app.route("/")
def index():
    with get_db() as conn:
        posts = conn.execute(
            "SELECT * FROM posts ORDER BY id DESC"
        ).fetchall()

    return render_template("index.html", posts=posts)


@app.route("/post/<int:post_id>")
def post_detail(post_id):
    post = get_post(post_id)
    return render_template("post.html", post=post)


@app.route("/create", methods=["GET", "POST"])
def create_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        content = request.form.get("content", "").strip()

        if not title or not author or not content:
            return render_template(
                "create.html",
                error="標題、作者、內容都必須填寫。",
                title=title,
                author=author,
                content=content,
            ), 400

        with get_db() as conn:
            cursor = conn.execute(
                """
                INSERT INTO posts (title, author, content)
                VALUES (?, ?, ?)
                """,
                (title, author, content),
            )
            post_id = cursor.lastrowid

        return redirect(url_for("post_detail", post_id=post_id))

    return render_template(
        "create.html",
        title="",
        author="",
        content="",
    )


@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    post = get_post(post_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        content = request.form.get("content", "").strip()

        if not title or not author or not content:
            return render_template(
                "edit.html",
                post=post,
                error="標題、作者、內容都必須填寫。",
                title=title,
                author=author,
                content=content,
            ), 400

        with get_db() as conn:
            conn.execute(
                """
                UPDATE posts
                SET title = ?, author = ?, content = ?
                WHERE id = ?
                """,
                (title, author, content, post_id),
            )

        return redirect(url_for("post_detail", post_id=post_id))

    return render_template(
        "edit.html",
        post=post,
        title=post["title"],
        author=post["author"],
        content=post["content"],
    )


@app.route("/delete/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    get_post(post_id)

    with get_db() as conn:
        conn.execute(
            "DELETE FROM posts WHERE id = ?",
            (post_id,),
        )

    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(error):
    return "找不到指定的文章。", 404


init_db()


if __name__ == "__main__":
    app.run(debug=True)