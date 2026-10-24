// 共用 API 呼叫函式
async function apiRequest(url, options = {}) {
    const response = await fetch(url, options);

    if (response.status === 204) {
        return null;
    }

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error("伺服器回應異常，請稍後再試。");
    }

    if (!response.ok) {
        throw new Error(data.error || "操作失敗，請稍後再試。");
    }

    return data;
}


// 讀取作業列表
async function loadAssignments() {
    const rows = document.getElementById("assignment-rows");

    if (!rows) {
        return;
    }

    const message = document.getElementById("list-message");
    const list = document.getElementById("assignment-list");

    try {
        const assignments = await apiRequest("/api/assignments");

        rows.replaceChildren();

        if (assignments.length === 0) {
            message.textContent = "目前沒有作業，請先新增一筆。";
            return;
        }

        for (const assignment of assignments) {
            const row = document.createElement("tr");

            const courseCell = document.createElement("td");
            courseCell.textContent = assignment.course;

            const taskCell = document.createElement("td");
            const link = document.createElement("a");
            link.href = `/assignments/${assignment.id}`;
            link.textContent = assignment.task;
            taskCell.appendChild(link);

            const deadlineCell = document.createElement("td");
            deadlineCell.textContent = assignment.deadline;

            row.append(courseCell, taskCell, deadlineCell);
            rows.appendChild(row);
        }

        message.textContent = `共 ${assignments.length} 筆作業`;
        list.hidden = false;
    } catch (error) {
        message.textContent = error.message;
        message.classList.add("error");
    }
}


// 新增或編輯作業
const form = document.getElementById("assignment-form");

if (form) {
    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const errorBox = document.getElementById("form-error");
        const submitButton = form.querySelector('button[type="submit"]');
        const assignmentId = form.dataset.id;

        const payload = {
            course: form.elements.course.value.trim(),
            task: form.elements.task.value.trim(),
            deadline: form.elements.deadline.value,
        };

        errorBox.textContent = "";

        if (!payload.course || !payload.task || !payload.deadline) {
            errorBox.textContent = "三個欄位皆為必填，不能只輸入空白。";
            return;
        }

        const url = assignmentId
            ? `/api/assignments/${assignmentId}`
            : "/api/assignments";

        const method = assignmentId ? "PUT" : "POST";

        submitButton.disabled = true;

        try {
            const assignment = await apiRequest(url, {
                method: method,
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            window.location.href = `/assignments/${assignment.id}`;
        } catch (error) {
            errorBox.textContent = error.message;
        } finally {
            submitButton.disabled = false;
        }
    });
}


// 刪除作業
const deleteButton = document.getElementById("delete-button");

if (deleteButton) {
    deleteButton.addEventListener("click", async () => {
        if (!window.confirm("確定要刪除這筆作業嗎？")) {
            return;
        }

        const errorBox = document.getElementById("delete-error");
        errorBox.textContent = "";
        deleteButton.disabled = true;

        try {
            await apiRequest(
                `/api/assignments/${deleteButton.dataset.id}`,
                { method: "DELETE" }
            );

            window.location.href = "/";
        } catch (error) {
            errorBox.textContent = error.message;
            deleteButton.disabled = false;
        }
    });
}


loadAssignments();
