
document.addEventListener('DOMContentLoaded', async function () {
    const emailViewer = document.getElementById("emailViewer");
    emailViewer.addEventListener('click', async function (event) {
        const row = event.target.closest('tr');
        if (row) {
            const mailId = row.dataset.mailId;
            try {
                const response = await fetch(`email_detail/${mailId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email_id: mailId })
                });

                const data = await response.json();

                if (data.status === "success" && data.url) {
                    sessionStorage.setItem('redirectData', JSON.stringify(data));
                    window.location.href = data.url;
                }

                if (!response.ok) {
                    throw new Error(data.message);
                }
            } catch (error) {
                alert(error.message);
                console.error(error.message);
            }
        }
    });
});
