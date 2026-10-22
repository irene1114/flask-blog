import sqlite3
from datetime import date
from pathlib import Path

from flask import (
    Flask,
    abort,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

app = Flask(__name__)

DATABASE = Path(__file__).resolve().parent / "homework.db"


# 建立資料庫連線，同一次請求共用同一個連線
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row

    return g.db


# 請求結束後關閉連線
@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


# 初始化資料表
def init_db():
    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course TEXT NOT NULL,
            task TEXT NOT NULL,
            deadline TEXT NOT NULL
        )
    """)

    db.commit()


# 取得指定作業，找不到時回傳 404
def get_assignment(assignment_id):
    assignment = get_db().execute(
        "SELECT * FROM assignments WHERE id = ?",
        (assignment_id,),
    ).fetchone()

    if assignment is None:
        abort(404)

    return assignment


# 讀取表單並檢查輸入內容
def validate_form():
    values = {
        "course": request.form.get("course", "").strip(),
        "task": request.form.get("task", "").strip(),
        "deadline": request.form.get("deadline", "").strip(),
    }

    if not all(values.values()):
        return values, "課程名稱、作業名稱及截止日期都必須填寫。"

    if len(values["course"]) > 100:
        return values, "課程名稱最多只能輸入 100 個字。"

    if len(values["task"]) > 200:
        return values, "作業名稱最多只能輸入 200 個字。"

    try:
        # 統一儲存為 YYYY-MM-DD，確保日期排序正確
        parsed_date = date.fromisoformat(values["deadline"])
        values["deadline"] = parsed_date.isoformat()
    except ValueError:
        return values, "請輸入有效的截止日期。"

    return values, None


# 首頁：依截止日期由早到晚排序
@app.route("/")
def index():
    assignments = get_db().execute("""
        SELECT *
        FROM assignments
        ORDER BY deadline ASC, id ASC
    """).fetchall()

    return render_template(
        "index.html",
        assignments=assignments,
    )


# 新增作業
@app.route("/create", methods=["GET", "POST"])
def create_assignment():
    values = {
        "course": "",
        "task": "",
        "deadline": "",
    }

    if request.method == "POST":
        values, error = validate_form()

        if error:
            return render_template(
                "form.html",
                page_title="新增作業",
                values=values,
                error=error,
            ), 400

        db = get_db()

        db.execute("""
            INSERT INTO assignments (course, task, deadline)
            VALUES (?, ?, ?)
        """, (
            values["course"],
            values["task"],
            values["deadline"],
        ))

        db.commit()

        return redirect(url_for("index"))

    return render_template(
        "form.html",
        page_title="新增作業",
        values=values,
        error=None,
    )


# 編輯作業
@app.route("/edit/<int:assignment_id>", methods=["GET", "POST"])
def edit_assignment(assignment_id):
    assignment = get_assignment(assignment_id)

    values = {
        "course": assignment["course"],
        "task": assignment["task"],
        "deadline": assignment["deadline"],
    }

    if request.method == "POST":
        values, error = validate_form()

        if error:
            return render_template(
                "form.html",
                page_title="編輯作業",
                values=values,
                error=error,
            ), 400

        db = get_db()

        db.execute("""
            UPDATE assignments
            SET course = ?, task = ?, deadline = ?
            WHERE id = ?
        """, (
            values["course"],
            values["task"],
            values["deadline"],
            assignment_id,
        ))

        db.commit()

        return redirect(url_for("index"))

    return render_template(
        "form.html",
        page_title="編輯作業",
        values=values,
        error=None,
    )


# 刪除作業，只接受 POST 請求
@app.route("/delete/<int:assignment_id>", methods=["POST"])
def delete_assignment(assignment_id):
    get_assignment(assignment_id)

    db = get_db()

    db.execute(
        "DELETE FROM assignments WHERE id = ?",
        (assignment_id,),
    )

    db.commit()

    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(error):
    return "找不到指定的作業，請返回首頁。", 404


# 使用 Gunicorn 啟動時，也會初始化資料表
with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run()
