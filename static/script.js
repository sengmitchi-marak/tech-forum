// Wait until the HTML page is loaded
document.addEventListener("DOMContentLoaded", function () {


    // LOGIN / REGISTER PASSWORD TOGGLE
    
    const passwordInput = document.getElementById("password");
    const showPassword = document.getElementById("showPassword");

    if (showPassword && passwordInput) {
        showPassword.addEventListener("click", function () {

            if (passwordInput.type === "password") {
                passwordInput.type = "text";
                showPassword.textContent = "Hide";
            } else {
                passwordInput.type = "password";
                showPassword.textContent = "Show";
            }

        });
    }


    // ASK QUESTION FORM

    const questionForm = document.getElementById("questionForm");

    if (questionForm) {

        questionForm.addEventListener("submit", function (event) {

            const title = document.getElementById("title").value.trim();
            const description = document.getElementById("description").value.trim();

            if (title === "" || description === "") {

                event.preventDefault();

                alert("Please enter both the question title and description.");

            }

        });

    }


    
    // SEARCH QUESTIONS
    
    const searchInput = document.getElementById("searchInput");
    const questionList = document.querySelectorAll(".question-card");

    if (searchInput) {

        searchInput.addEventListener("input", function () {

            const searchText = searchInput.value.toLowerCase();

            questionList.forEach(function (question) {

                const text = question.textContent.toLowerCase();

                if (text.includes(searchText)) {
                    question.style.display = "";
                } else {
                    question.style.display = "none";
                }

            });

        });

    }


    
    //LIKE BUTTON
    
    const likeButtons = document.querySelectorAll(".like-btn");

    likeButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            let count = parseInt(button.dataset.likes);

            count++;

            button.dataset.likes = count;
            button.textContent = "👍 " + count;

        });

    });


    
    // DELETE CONFIRMATION
    function confirmDeleteQuestion() {

    return confirm("⚠️ Are you sure you want to delete this question?");

}

function confirmDeleteAccount() {

    return confirm("⚠️ This will permanently delete your account.\n\nAre you sure?");

}
    
//DELETE QUESTION or Account
<form action="/delete_question/{{ question[0] }}" method="POST"
      onsubmit="return confirmDeleteQuestion()">

    <button type="submit">
        🗑️ Delete Question
    </button>

    <button type="submit">
        🗑️ Delete Account
    </button>
    

</form>


    // 7. ANSWER FORM VALIDATION
    
    const answerForm = document.getElementById("answerForm");

    if (answerForm) {

        answerForm.addEventListener("submit", function (event) {

            const answer = document.getElementById("answer").value.trim();

            if (answer === "") {

                event.preventDefault();

                alert("Please write an answer before submitting.");

            }

        });

    }

});

