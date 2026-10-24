from datetime import date
from pathlib import Path

from flask import Flask, jsonify, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)

# 設定 SQLite 資料庫
Path(app.instance_path).mkdir(parents=True, exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///assignments.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# 作業資料模型
class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course = db.Column(db.String(100), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    deadline = db.Column(db.Date, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "course": self.course,
            "task": self.task,
            "deadline": self.deadline.isoformat(),
        }


# 檢查使用者傳入的資料
def validate_data():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return None, "請提供 JSON 格式的資料。"

    values = {}

    for field in ("course", "task", "deadline"):
        value = data.get(field)

        if not isinstance(value, str) or not value.strip():
            return None, "課程名稱、作業名稱及截止日期皆為必填。"

        values[field] = value.strip()

    if len(values["course"]) > 100:
        return None, "課程名稱最多 100 個字。"

    if len(values["task"]) > 200:
        return None, "作業名稱最多 200 個字。"

    try:
        parsed = date.fromisoformat(values["deadline"])

        if parsed.isoformat() != values["deadline"]:
            raise ValueError

        values["deadline"] = parsed
    except ValueError:
        return None, "截止日期必須是有效的 YYYY-MM-DD 日期。"

    return values, None


# ---------- 前端頁面 ----------

# 作業列表頁面
@app.get("/")
def index():
    return render_template("index.html")


# 新增作業頁面
@app.get("/create")
def create_page():
    return render_template(
        "form.html",
        page_title="新增作業",
        assignment=None,
    )


# 單筆作業頁面
@app.get("/assignments/<int:assignment_id>")
def detail_page(assignment_id):
    assignment = db.get_or_404(Assignment, assignment_id)

    return render_template(
        "detail.html",
        assignment=assignment,
    )


# 編輯作業頁面
@app.get("/assignments/<int:assignment_id>/edit")
def edit_page(assignment_id):
    assignment = db.get_or_404(Assignment, assignment_id)

    return render_template(
        "form.html",
        page_title="編輯作業",
        assignment=assignment,
    )


# ---------- RESTful API ----------

# Create：新增作業
@app.post("/api/assignments")
def create_assignment():
    values, error = validate_data()

    if error:
        return jsonify({"error": error}), 400

    assignment = Assignment(**values)
    db.session.add(assignment)
    db.session.commit()

    response = jsonify(assignment.to_dict())
    response.status_code = 201
    response.headers["Location"] = url_for(
        "read_assignments",
        assignment_id=assignment.id,
    )

    return response


# Read：讀取列表或單筆作業
@app.get("/api/assignments")
@app.get("/api/assignments/<int:assignment_id>")
def read_assignments(assignment_id=None):
    if assignment_id is not None:
        assignment = db.get_or_404(Assignment, assignment_id)
        return jsonify(assignment.to_dict())

    statement = db.select(Assignment).order_by(
        Assignment.deadline.asc(),
        Assignment.id.asc(),
    )

    assignments = db.session.execute(statement).scalars().all()

    return jsonify([
        assignment.to_dict()
        for assignment in assignments
    ])


# Update：更新作業
@app.put("/api/assignments/<int:assignment_id>")
def update_assignment(assignment_id):
    assignment = db.get_or_404(Assignment, assignment_id)

    values, error = validate_data()

    if error:
        return jsonify({"error": error}), 400

    assignment.course = values["course"]
    assignment.task = values["task"]
    assignment.deadline = values["deadline"]

    db.session.commit()

    return jsonify(assignment.to_dict())


# Delete：刪除作業
@app.delete("/api/assignments/<int:assignment_id>")
def delete_assignment(assignment_id):
    assignment = db.get_or_404(Assignment, assignment_id)

    db.session.delete(assignment)
    db.session.commit()

    return "", 204


# ---------- 錯誤處理 ----------

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "找不到指定的作業或 API。"}), 404

    return "找不到指定的作業或頁面，請返回首頁。", 404


@app.errorhandler(SQLAlchemyError)
def database_error(error):
    db.session.rollback()
    app.logger.exception("資料庫操作失敗")

    if request.path.startswith("/api/"):
        return jsonify({"error": "資料儲存失敗，請稍後再試。"}), 500

    return "資料庫操作失敗，請稍後再試。", 500


# 建立資料表
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run()
